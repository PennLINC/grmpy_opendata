#!/usr/bin/env python3
"""
Extract diagnostic (dx) columns from the updated axis REDCap export.

The participant list is taken from the CUBIDS curation participants TSV so that
every released subject is represented, even those absent from the REDCap export.

Processing rules:
  - participant_id is derived as "sub-<bblid>" and placed first.
  - Only dx_* columns are retained, ordered alphabetically.
  - Binary dx flags are written as integers; dx_pscat is a categorical text
    column and is left as-is.
  - Participants whose date_diff_dx_to_scan exceeds 365 days have all dx values
    set to n/a, since the diagnosis is too far from the scan.
  - Participants absent from the REDCap export are emitted with all values n/a.
  - Any missing value is written as n/a.

Output: axis.tsv

Example:
  python phenotype/07_process_axis.py \
    --input phenotype/data/axis-updated-redcap.tsv \
    --participants curation/04_cubids_curation/participants_tmp.tsv \
    --output-dir phenotype/data
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Iterable, List

NA = "n/a"
BBLID_COL = "bblid"
PARTICIPANT_ID_COL = "participant_id"
DATE_DIFF_COL = "date_diff_dx_to_scan"
MAX_DATE_DIFF_DAYS = 365

# dx_* columns that hold categorical text rather than an integer flag.
TEXT_DX_COLS = {"dx_pscat"}

# dx_* columns to exclude from the output (all-zero / uninformative in these
# data and not confidently interpretable).
EXCLUDED_DX_COLS = {
    "dx_cogdis",
    "dx_cogdis_remit",
    "dx_intdis",
    "dx_other",
    "dx_other_remit",
    "dx_pdd",
    "dx_sleep",
    "dx_sub_other",
}


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract dx_* diagnostic columns from the updated axis "
            "REDCap export into axis.tsv."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("phenotype/data/axis-updated-redcap.tsv"),
        help=(
            "Path to the updated axis REDCap TSV "
            "(default: phenotype/data/axis-updated-redcap.tsv)"
        ),
    )
    parser.add_argument(
        "--participants",
        type=Path,
        default=Path("curation/04_cubids_curation/participants_tmp.tsv"),
        help=(
            "Path to the participants TSV defining the full subject list "
            "(default: curation/04_cubids_curation/participants_tmp.tsv)"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("phenotype/data"),
        help="Directory to write axis.tsv (default: phenotype/data)",
    )
    return parser.parse_args(list(argv))


def build_output_columns(input_columns: List[str]) -> List[str]:
    """participant_id first, then dx_* alphabetically."""
    dx_cols = sorted(
        c for c in input_columns if c.startswith("dx_") and c not in EXCLUDED_DX_COLS
    )
    return [PARTICIPANT_ID_COL, *dx_cols]


def format_value(col: str, raw: str) -> str:
    """Normalize a single cell value for output."""
    value = (raw or "").strip()
    if value == "":
        return NA
    if col in TEXT_DX_COLS:
        return value
    # Integer-valued columns (binary dx flags).
    try:
        return str(int(float(value)))
    except ValueError:
        return value


def _exceeds_date_diff(raw: str) -> bool:
    value = (raw or "").strip()
    if value == "":
        return False
    try:
        return float(value) > MAX_DATE_DIFF_DAYS
    except ValueError:
        return False


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        print(f"Input TSV not found: {args.input}", file=sys.stderr)
        return 2
    if not args.participants.exists():
        print(f"Participants TSV not found: {args.participants}", file=sys.stderr)
        return 2

    with args.input.open("r", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        input_columns = reader.fieldnames or []
        if not input_columns:
            print("Input TSV has no header.", file=sys.stderr)
            return 2
        redcap_rows = list(reader)

    if BBLID_COL not in input_columns:
        print(f"Input TSV missing '{BBLID_COL}' column.", file=sys.stderr)
        return 2

    redcap_by_id: Dict[str, dict] = {
        f"sub-{(row.get(BBLID_COL) or '').strip()}": row for row in redcap_rows
    }

    output_columns = build_output_columns(input_columns)
    data_columns = [c for c in output_columns if c != PARTICIPANT_ID_COL]

    with args.participants.open("r", newline="") as f:
        participants = list(csv.DictReader(f, delimiter="\t"))

    out_path = args.output_dir / "axis.tsv"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    n_missing = 0
    n_blanked = 0
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(output_columns)
        for participant in participants:
            participant_id = (participant.get(PARTICIPANT_ID_COL) or "").strip()
            source = redcap_by_id.get(participant_id)

            if source is None:
                n_missing += 1
                writer.writerow([participant_id] + [NA] * len(data_columns))
                continue

            if _exceeds_date_diff(source.get(DATE_DIFF_COL, "")):
                n_blanked += 1
                writer.writerow([participant_id] + [NA] * len(data_columns))
                continue

            writer.writerow(
                [participant_id]
                + [format_value(col, source.get(col, "")) for col in data_columns]
            )

    print(
        f"Wrote {out_path} ({len(output_columns)} columns, "
        f"{len(participants)} rows; {n_missing} not in REDCap, "
        f"{n_blanked} blanked for date_diff > {MAX_DATE_DIFF_DAYS})"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
