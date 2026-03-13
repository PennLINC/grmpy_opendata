#!/usr/bin/env python3
"""
Split the developmental scales TSV (Tanner/Substance/SPQ) into separate
per-instrument TSVs.

Instruments extracted (with column-prefix matching):
  - tanner_boy   (prefixes: tanner_boy_, tannerb_, tanner_developmental_boys_)
  - tanner_girl  (prefixes: tanner_girl_, tannerg_, tanner_developmental_girls_)
  - spq          (prefix:  spq_)
  - suq          (prefixes: substance_, drugs_)

Columns not matching any instrument go to dev_misc.tsv.

Output naming: {instrument}.tsv, dev_misc.tsv

Row clearing (retain row, blank values):
- Rows are retained but with empty values for all columns except
  "participant_id" when any of these hold (only checked if the column
  exists in the input):
    - bbl_protocol is not "GRMPY"
    - statetrait_vcode is not in {"V", "U", "F"}
    - admin_proband is not "p"

Example:
  python phenotype/06_separate_dev_scales.py \\
    --input phenotype/data/tanner_substance_spq.tsv \\
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
INVALID_FAKE_DRUGS_COL = "invalid_fake_drugs"
_FAKE_DRUG_COLS = ("substance_othr_040", "substance_othr_050")

# (output_name, column_prefixes, exclude_suffixes) – scales are tested in order;
# first match wins.  Columns matching a prefix but ending with an excluded
# suffix are sent to misc instead.
ScaleDef = Tuple[str, List[str], List[str]]

SCALES: List[ScaleDef] = [
    (
        "tanner_boy",
        ["tanner_boy_", "tannerb_", "tanner_developmental_boys_"],
        ["_complete", "_vcode"],
    ),
    (
        "tanner_girl",
        ["tanner_girl_", "tannerg_", "tanner_developmental_girls_"],
        ["_complete", "_vcode"],
    ),
    ("spq", ["spq_"], ["_complete", "_vcode"]),
    ("suq", ["substance_", "drugs_"], ["_vcode", "_complete"]),
]


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split developmental scales TSV (Tanner/Substance/SPQ) into "
            "separate per-instrument TSVs."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("phenotype/data/tanner_substance_spq.tsv"),
        help="Path to input TSV",
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
        help="Do not write a dev_misc.tsv for unassigned columns",
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

    Returns:
      - scale_columns: dict mapping scale name -> columns (naturally sorted)
      - misc_columns: unmatched columns (alphabetically sorted)
    """
    scale_columns: Dict[str, List[str]] = {name: [] for name, _, _ in scales}
    exclude_map: Dict[str, List[str]] = {name: exc for name, _, exc in scales}
    misc: List[str] = []

    for col in columns:
        if col == PARTICIPANT_ID_COL:
            continue
        col_lower = col.lower()
        matched = False
        for name, prefixes, _ in scales:
            if any(col_lower.startswith(p) for p in prefixes):
                if any(col_lower.endswith(s) for s in exclude_map[name]):
                    misc.append(col)
                else:
                    scale_columns[name].append(col)
                matched = True
                break
        if not matched:
            misc.append(col)

    for name in scale_columns:
        scale_columns[name].sort(key=lambda c: natural_key(c.lower()))
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


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        print(f"Input TSV not found: {args.input}", file=sys.stderr)
        return 2

    with args.input.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        columns = reader.fieldnames or []
        if not columns:
            print("Input TSV has no header.", file=sys.stderr)
            return 2

    scale_columns, misc_columns = classify_columns(columns, SCALES)

    # Build headers (participant_id + scale columns)
    headers: Dict[str, List[str]] = {}
    for name, cols in scale_columns.items():
        if cols:
            headers[name] = [PARTICIPANT_ID_COL] + cols

    if "suq" in headers:
        headers["suq"].append(INVALID_FAKE_DRUGS_COL)

    misc_key = "dev_misc"
    misc_header: List[str] = []
    write_misc = not args.no_misc
    if write_misc and misc_columns:
        misc_header = [PARTICIPANT_ID_COL] + misc_columns

    # Prepare output containers
    outputs: Dict[str, Tuple[Path, List[Mapping[str, str]]]] = {}
    for name in headers:
        outputs[name] = (args.output_dir / f"{name}.tsv", [])
    if misc_header:
        outputs[misc_key] = (args.output_dir / f"{misc_key}.tsv", [])

    # Stream rows
    with args.input.open("r", newline="") as f:
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
                    out_row = {col: row.get(col, "") for col in header}
                    if name == "suq":
                        fake = any(
                            row.get(c, "") not in ("0", "0.0", "")
                            for c in _FAKE_DRUG_COLS
                        )
                        out_row[INVALID_FAKE_DRUGS_COL] = "1" if fake else ""
                    outputs[name][1].append(out_row)

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

    print(
        f"Wrote {len(outputs)} files to {args.output_dir}"
        + (f" (including {misc_key}.tsv)" if misc_key in outputs else "")
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
