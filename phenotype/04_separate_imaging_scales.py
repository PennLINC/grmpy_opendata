#!/usr/bin/env python3
"""
Split imaging pre/post-scan scale TSVs into separate per-instrument TSVs.

Instruments are assigned by explicit column-prefix matching (longest prefix
wins).  Columns that do not match any defined instrument go to a misc file.

Prescan instruments extracted:
  - stai       (prefix: stai_)
  - staxi2_ca  (prefix: staxi2_ca_)

Postscan instruments extracted:
  - stai       (prefix: stai_)     – the stai_state items
  - wolf       (prefix: wolf_)

Output naming: {instrument}_{pre|post}_imaging.tsv
               misc_{pre|post}_imaging.tsv

Row clearing (retain row, blank values):
- Rows are retained but with empty values for all columns except
  "participant_id" when any of these hold (only checked if the column
  exists in the input):
    - bbl_protocol is not "GRMPY"
    - statetrait_vcode is not in {"V", "U", "F"}
    - admin_proband is not "p"

Example:
  python phenotype/05_separate_imaging_scales.py \\
    --input-pre phenotype/data/imaging_prescan_scales.tsv \\
    --input-post phenotype/data/imaging_postscan_scales.tsv \\
    --output-dir phenotype/data
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple


PARTICIPANT_ID_COL = "participant_id"

# (scale_name, column_prefix, last_column) – longer prefixes first so that
# e.g. staxi2_ca_ is tested before a hypothetical staxi2_ entry.
# Columns that match the prefix but come after last_column (in natural sort
# order) are sent to misc.
ScaleDef = Tuple[str, str, str]

PRESCAN_SCALES: List[ScaleDef] = [
    ("staxi2_ca", "staxi2_ca_", "staxi2_ca_35"),
    ("stai", "stai_", "stai_q_40"),
]

POSTSCAN_SCALES: List[ScaleDef] = [
    ("stai", "stai_", "stai_q_20"),
    ("wolf", "wolf_", "wolf_post_3"),
]


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split imaging pre/post-scan scale TSVs into separate "
            "per-instrument TSVs."
        )
    )
    parser.add_argument(
        "--input-pre",
        type=Path,
        default=Path("phenotype/data/imaging_prescan_scales.tsv"),
        help="Path to prescan input TSV",
    )
    parser.add_argument(
        "--input-post",
        type=Path,
        default=Path("phenotype/data/imaging_postscan_scales.tsv"),
        help="Path to postscan input TSV",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("phenotype/data"),
        help="Directory to write instrument TSVs (default: phenotype/data)",
    )
    parser.add_argument(
        "--no-misc",
        action="store_true",
        help="Do not write misc TSVs for unassigned columns",
    )
    return parser.parse_args(list(argv))


_DIGIT_SPLIT_RE = re.compile(r"(\d+)")


def natural_key(text: str) -> List[object]:
    """Return a list key that enables natural (numeric-aware) sorting."""
    parts = _DIGIT_SPLIT_RE.split(text)
    key: List[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key


def classify_columns(
    columns: List[str],
    scales: List[ScaleDef],
) -> Tuple[Dict[str, List[str]], List[str]]:
    """Classify columns into scale groups by prefix matching.

    Columns that match a scale's prefix but sort after its *last_column*
    (natural order) are moved to misc.

    Returns:
      - scale_columns: dict mapping scale name → columns (naturally sorted)
      - misc_columns: unmatched columns (alphabetically sorted)
    """
    scale_columns: Dict[str, List[str]] = {name: [] for name, _, _ in scales}
    last_col_map: Dict[str, str] = {name: last for name, _, last in scales}
    misc: List[str] = []

    for col in columns:
        if col == PARTICIPANT_ID_COL:
            continue
        col_lower = col.lower()
        matched = False
        for name, prefix, _ in scales:
            if col_lower.startswith(prefix):
                scale_columns[name].append(col)
                matched = True
                break
        if not matched:
            misc.append(col)

    for name in scale_columns:
        scale_columns[name].sort(key=lambda c: natural_key(c.lower()))

    # Trim columns past the last_column cutoff → move overflow to misc
    for name, cols in list(scale_columns.items()):
        last_col = last_col_map[name]
        cutoff_key = natural_key(last_col.lower())
        keep: List[str] = []
        for col in cols:
            if natural_key(col.lower()) <= cutoff_key:
                keep.append(col)
            else:
                misc.append(col)
        scale_columns[name] = keep

    misc.sort(key=lambda c: c.lower())

    return scale_columns, misc


def write_tsv(path: Path, header: List[str], rows: Iterable[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        for row in rows:
            writer.writerow([row.get(col, "") for col in header])


def _get_row_value_ci(row: Mapping[str, str], key: str) -> str:
    """Return the value for the first column matching *key* case-insensitively."""
    key_l = key.lower()
    for k, v in row.items():
        if k.lower() == key_l:
            return v
    return ""


def row_should_be_cleared(row: Mapping[str, str]) -> bool:
    """Determine whether a row's values should be blanked out.

    Criteria (applied only when the column is present):
      - bbl_protocol must be "GRMPY"
      - statetrait_vcode must be in {"V", "U", "F"}
      - admin_proband must be "p"
    """
    protocol = _get_row_value_ci(row, "bbl_protocol")
    if protocol != "" and protocol != "GRMPY":
        return True

    vcode = _get_row_value_ci(row, "statetrait_vcode")
    if vcode != "" and vcode not in {"V", "U", "F"}:
        return True

    proband = _get_row_value_ci(row, "admin_proband")
    if proband != "" and proband != "p":
        return True

    return False


def process_file(
    input_path: Path,
    output_dir: Path,
    scales: List[ScaleDef],
    suffix: str,
    write_misc: bool,
) -> int:
    """Process one input TSV and write per-scale + misc outputs.

    Returns the number of files written.
    """
    if not input_path.exists():
        print(f"Input TSV not found: {input_path}", file=sys.stderr)
        return 0

    with input_path.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        columns = reader.fieldnames or []
        if not columns:
            print(f"Input TSV has no header: {input_path}", file=sys.stderr)
            return 0

    scale_columns, misc_columns = classify_columns(columns, scales)

    # Build headers (participant_id + scale columns)
    headers: Dict[str, List[str]] = {}
    for name, cols in scale_columns.items():
        if cols:
            headers[name] = [PARTICIPANT_ID_COL] + cols

    misc_header: List[str] = []
    if write_misc and misc_columns:
        misc_header = [PARTICIPANT_ID_COL] + misc_columns

    # Prepare output containers
    outputs: Dict[str, Tuple[Path, List[Mapping[str, str]]]] = {}
    for name in headers:
        outputs[name] = (output_dir / f"{name}_{suffix}.tsv", [])
    misc_key = f"misc_{suffix}"
    if misc_header:
        outputs[misc_key] = (output_dir / f"{misc_key}.tsv", [])

    # Stream rows
    with input_path.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            should_clear = row_should_be_cleared(row)
            pid = row.get(PARTICIPANT_ID_COL, "")

            for name, header in headers.items():
                if should_clear:
                    cleared = {col: "" for col in header}
                    cleared[PARTICIPANT_ID_COL] = pid
                    outputs[name][1].append(cleared)
                else:
                    outputs[name][1].append({col: row.get(col, "") for col in header})

            if misc_header:
                if should_clear:
                    cleared = {col: "" for col in misc_header}
                    cleared[PARTICIPANT_ID_COL] = pid
                    outputs[misc_key][1].append(cleared)
                else:
                    outputs[misc_key][1].append(
                        {col: row.get(col, "") for col in misc_header}
                    )

    # Write files
    for name, (path, rows) in outputs.items():
        header = misc_header if name == misc_key else headers[name]
        write_tsv(path, header, rows)

    return len(outputs)


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    write_misc = not args.no_misc
    total = 0

    total += process_file(
        args.input_pre,
        args.output_dir,
        PRESCAN_SCALES,
        "pre_imaging",
        write_misc,
    )
    total += process_file(
        args.input_post,
        args.output_dir,
        POSTSCAN_SCALES,
        "post_imaging",
        write_misc,
    )

    print(f"Wrote {total} files to {args.output_dir}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
