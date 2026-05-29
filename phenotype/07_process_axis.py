#!/usr/bin/env python3
"""
Extract axis diagnosis and dx summary columns from the full Diagnosis TSV.

Columns retained:
  - participant_id
  - AXIS1_DESC1 .. AXIS1_DESC10
  - AXIS2_DESC1
  - All dx_* columns
  - dxsum

Output: axis.tsv

Example:
  python phenotype/07_process_axis.py \
    --input phenotype/data/Diagnosis.tsv \
    --output-dir phenotype/data
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Iterable, List


PARTICIPANT_ID_COL = "participant_id"

_AXIS1_DESC_RE = re.compile(r"^AXIS1_DESC\d+$", re.IGNORECASE)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract axis diagnosis columns and dx summary columns "
            "from Diagnosis.tsv into axis.tsv."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("phenotype/data/Diagnosis.tsv"),
        help="Path to input Diagnosis TSV (default: phenotype/data/Diagnosis.tsv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("phenotype/data"),
        help="Directory to write axis.tsv (default: phenotype/data)",
    )
    return parser.parse_args(list(argv))


def _natural_sort_key(col: str) -> List[object]:
    """Sort key that handles embedded numbers naturally."""
    parts = re.split(r"(\d+)", col)
    return [int(p) if p.isdigit() else p.lower() for p in parts]


def select_columns(all_columns: List[str]) -> List[str]:
    """Return the ordered subset of columns to keep."""
    kept: List[str] = [PARTICIPANT_ID_COL]

    axis1_desc = [col for col in all_columns if _AXIS1_DESC_RE.match(col)]
    axis1_desc.sort(key=_natural_sort_key)
    kept.extend(axis1_desc)

    if "AXIS2_DESC1" in all_columns:
        kept.append("AXIS2_DESC1")

    for col in all_columns:
        if col.startswith("dx_"):
            kept.append(col)

    if "dxsum" in all_columns:
        kept.append("dxsum")

    return kept


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
        rows = list(reader)

    kept_columns = select_columns(columns)
    if len(kept_columns) <= 1:
        print("No matching columns found in input.", file=sys.stderr)
        return 2

    out_path = args.output_dir / "axis.tsv"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(kept_columns)
        for row in rows:
            writer.writerow([row.get(col, "") or "n/a" for col in kept_columns])

    print(f"Wrote {out_path} ({len(kept_columns)} columns, {len(rows)} rows)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
