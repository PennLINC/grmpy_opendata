#!/usr/bin/env python3
"""
Split self-report itemwise TSV into separate TSVs, one per instrument, with
columns ordered in natural numeric sequence (e.g., aces_1, aces_2, ..., aces_10).

Heuristics for instrument detection:
- Instruments are inferred primarily from columns that have item-like tokens
  starting with a digit after an instrument prefix (e.g., "aces_1", "hcl16_3_1",
  "eswan_dmdd_01a", "grit_15___2"). The instrument is the underscore-joined
  prefix tokens up to (but not including) the first token that starts with a digit.
- Non-item columns (e.g., metadata or timing fields) are mapped to the most
  likely instrument by searching for known instrument names within the column
  name (favoring longer matches). If still ambiguous, a lightweight plural
  fallback is applied (e.g., map "ace_flag" → "aces").
- Columns whose names contain "complete" (case-insensitive), including long
  names like "pittsburgh_sleep_quality_index_psqi_complete", are NOT included
  in instrument TSVs and are instead written to "misc.tsv".

Output:
- One TSV per instrument in the output directory. Each TSV includes
  "participant_id" followed by the instrument's item columns sorted naturally
  (numeric-aware), then any other non-item columns assigned to that instrument
  (excluding completion/"complete" columns), sorted alphabetically.
- Optionally a "misc.tsv" that includes completion/"complete" columns and any
  other columns that could not be reliably assigned to an instrument.

Example:
  python phenotype/03_separate_self_reports.py \
    --input phenotype/data/self_report_itemwise.tsv \
    --output-dir phenotype/data
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple


PARTICIPANT_ID_COL = "participant_id"


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split self-report itemwise TSV into separate instrument TSVs with\n"
            "natural numeric ordering of item columns."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("phenotype/data/self_report_itemwise.tsv"),
        help="Path to input TSV (default: phenotype/data/self_report_itemwise.tsv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("phenotype/data/self_report_itemwise_split"),
        help="Directory to write instrument TSVs (default: phenotype/data/self_report_itemwise_split)",
    )
    parser.add_argument(
        "--no-misc",
        action="store_true",
        help="Do not write a misc.tsv for unassigned columns",
    )
    return parser.parse_args(list(argv))


_DIGIT_SPLIT_RE = re.compile(r"(\d+)")


def natural_key(text: str) -> List[object]:
    """Return a list key that enables natural (numeric-aware) sorting.

    Example: "10a" sorts after "2" and after "2a".
    """
    parts = _DIGIT_SPLIT_RE.split(text)
    key: List[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part)
    return key


def split_tokens(name: str) -> List[str]:
    return [t for t in name.split("_") if t != ""]


def is_item_column(column: str) -> bool:
    """Heuristic: a column is an item column if it has any token after the
    instrument prefix that starts with a digit. This captures patterns like:
    - aces_1
    - hcl16_3_1
    - eswan_dmdd_01a
    - grit_15___2
    """
    tokens = split_tokens(column.lower())
    # Skip leading participant_id and clearly non-instrument roots
    if not tokens or tokens[0] == PARTICIPANT_ID_COL:
        return False
    # Find first token starting with a digit
    for token in tokens:
        if token and token[0].isdigit():
            return True
    return False


def infer_instrument_from_item(column: str) -> str | None:
    """Infer instrument name from an item-like column by taking tokens up to the
    first token that starts with a digit.
    """
    tokens = split_tokens(column.lower())
    if not tokens or tokens[0] == PARTICIPANT_ID_COL:
        return None
    inst_tokens: List[str] = []
    for token in tokens:
        if token and token[0].isdigit():
            break
        inst_tokens.append(token)
    if not inst_tokens:
        return None
    return "_".join(inst_tokens)


def instrument_prefix_for_column(column: str, instrument: str) -> str:
    """Return the prefix of a column that corresponds to the instrument.

    If the column starts with the instrument followed by an underscore, we use
    that. Otherwise return the instrument itself; callers should handle suffix
    extraction accordingly.
    """
    col_l = column.lower()
    inst_l = instrument.lower()
    if col_l.startswith(inst_l + "_"):
        return instrument
    return instrument


def extract_suffix_after_instrument(column: str, instrument: str) -> str:
    """Extract suffix after the instrument prefix for sorting purposes.
    If no clear prefix match, return the column itself.
    """
    col_l = column.lower()
    inst_l = instrument.lower()
    if col_l.startswith(inst_l + "_"):
        return column[len(instrument) + 1 :]
    return column


def assign_non_item_column(column: str, instruments: List[str]) -> str | None:
    """Assign a non-item column to the most likely instrument.

    Note: Columns containing "complete" are handled upstream and are not
    assigned to any instrument by this function.

    Strategy:
    - Prefer instruments that appear as whole tokens in the column, favoring
      longer instrument names.
    - Fallback to prefix match (column starts with instrument).
    - As a last resort, handle simple pluralization (instrument ending with 's' or 'es').
    """
    col_l = column.lower()
    tokens = split_tokens(col_l)
    candidates = sorted(instruments, key=len, reverse=True)

    # 1) Whole-token match
    for inst in candidates:
        pat = re.compile(rf"(^|_){re.escape(inst)}(_|$)")
        if pat.search(col_l):
            return inst

    # 2) Prefix match
    for inst in candidates:
        if col_l.startswith(inst + "_") or col_l.startswith(inst):
            return inst

    # 3) Simple pluralization fallback, e.g., ace_complete → aces
    if tokens:
        first = tokens[0]
        for inst in candidates:
            if inst.endswith("es") and inst[:-2] == first:
                return inst
            if inst.endswith("s") and inst[:-1] == first:
                return inst

    return None


@dataclass
class InstrumentColumns:
    item_columns: List[str]
    other_columns: List[str]


def build_instrument_groups(
    columns: List[str],
) -> Tuple[Dict[str, InstrumentColumns], List[str]]:
    """Build mapping from instrument → columns and return unassigned columns.

    Returns:
      - instrument_to_columns: dict mapping instrument to its item and other columns
      - leftover_columns: list of non-item columns that could not be assigned,
        plus any columns containing "complete" which are intentionally excluded
        from instrument TSVs and written to misc instead
    """
    instruments: List[str] = []
    col_to_instrument: Dict[str, str] = {}

    # First pass: infer instruments from item columns
    for col in columns:
        if col == PARTICIPANT_ID_COL:
            continue
        if is_item_column(col):
            inst = infer_instrument_from_item(col)
            if inst:
                col_to_instrument[col] = inst
                if inst not in instruments:
                    instruments.append(inst)

    # Prepare container
    instrument_to_columns: Dict[str, InstrumentColumns] = {
        inst: InstrumentColumns(item_columns=[], other_columns=[])
        for inst in instruments
    }

    # Assign item columns to instruments
    for col, inst in col_to_instrument.items():
        instrument_to_columns[inst].item_columns.append(col)

    # Second pass: assign non-item columns to best-matching instrument
    leftover: List[str] = []
    for col in columns:
        if col == PARTICIPANT_ID_COL:
            continue
        if col in col_to_instrument:
            continue
        # Send any completion/"complete" columns to leftover (misc) unconditionally
        if "complete" in col.lower():
            leftover.append(col)
            continue
        assigned = assign_non_item_column(col, instruments)
        if assigned is None:
            leftover.append(col)
        else:
            instrument_to_columns[assigned].other_columns.append(col)

    # Sort columns: items by natural order of suffix; others alphabetical
    for inst, cols in instrument_to_columns.items():
        cols.item_columns.sort(
            key=lambda c: natural_key(extract_suffix_after_instrument(c, inst))
        )
        cols.other_columns.sort(key=lambda c: c.lower())

    return instrument_to_columns, leftover


def write_tsv(path: Path, header: List[str], rows: Iterable[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(header)
        for row in rows:
            writer.writerow([row.get(col, "") for col in header])


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        print(f"Input TSV not found: {args.input}", file=sys.stderr)
        return 2

    # Read header first
    with args.input.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        columns = reader.fieldnames or []
        if not columns:
            print("Input TSV has no header.", file=sys.stderr)
            return 2

    instrument_to_columns, leftover = build_instrument_groups(columns)

    # Prepare per-instrument headers
    instrument_headers: Dict[str, List[str]] = {}
    for inst, cols in instrument_to_columns.items():
        header = [PARTICIPANT_ID_COL]
        header.extend(cols.item_columns)
        header.extend(cols.other_columns)
        instrument_headers[inst] = header

    misc_header: List[str] = []
    if leftover and not args.no_misc:
        # Exclude participant_id if present (already added by us at write time)
        misc_cols = [c for c in leftover if c != PARTICIPANT_ID_COL]
        misc_cols.sort(key=lambda c: c.lower())
        misc_header = [PARTICIPANT_ID_COL] + misc_cols

    # Stream rows and write per-instrument outputs in one pass
    outputs: Dict[str, Tuple[Path, List[List[str]]]] = {}
    for inst in instrument_headers:
        out_path = args.output_dir / f"{inst}.tsv"
        outputs[inst] = (out_path, [])
    if misc_header:
        outputs["misc"] = (args.output_dir / "misc.tsv", [])

    with args.input.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            for inst, header in instrument_headers.items():
                outputs[inst][1].append({col: row.get(col, "") for col in header})
            if misc_header:
                outputs["misc"][1].append(
                    {col: row.get(col, "") for col in misc_header}
                )

    # Write files
    for inst, (path, rows) in outputs.items():
        if inst == "misc":
            header = misc_header
        else:
            header = instrument_headers[inst]
        write_tsv(path, header, rows)

    print(
        f"Wrote {len(outputs)} files to {args.output_dir}"
        + (" (including misc.tsv)" if "misc" in outputs else "")
    )

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
