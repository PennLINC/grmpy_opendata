#!/usr/bin/env python3
"""
Summarize `info` fields across subject-level Flywheel JSON files.

This utility recursively searches a GRMPY SUBJECTS directory for files matching
the pattern "*.flywheel.json", loads each JSON, extracts and flattens the
top-level `info` object (if present), and produces a TSV summarizing, for every
flattened field, how many subjects have a non-missing value.

Missingness definition:
- A value is considered missing if it is None, an empty string "", or an empty
  container (list/dict of length 0). Numeric zero (0) and boolean False are
  treated as present.

Output TSV columns:
- field: dot-delimited flattened key under `info` (e.g., demographics.height)
- n_present: number of JSON files with a non-missing value for this field
- n_missing: number of JSON files without a non-missing value for this field
- present_pct: n_present / total_subject_jsons, rounded to 4 decimals
- types: comma-separated set of Python value types observed for present values

Example
-------
```bash
python curation/04_cubids_curation/01_summarize_available_phenotypes.py \
  --subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
  --output info_summary.tsv
```

You can also restrict the search pattern if needed (default: *.flywheel.json):
```bash
python curation/04_cubids_curation/01_summarize_available_phenotypes.py \
  --subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
  --pattern "*.json" --output info_summary.tsv
```

The script prints a short run summary to stdout, and writes the TSV to the
requested path.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Tuple


@dataclass
class FieldStats:
    present_count: int
    type_names: set


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize flattened `info` fields across Flywheel JSON files."
    )
    parser.add_argument(
        "--subjects-root",
        required=True,
        type=Path,
        help="Path to SUBJECTS root (e.g., /cbica/projects/.../SUBJECTS)",
    )
    parser.add_argument(
        "--pattern",
        default="*.flywheel.json",
        help="Glob pattern for subject-level JSON files (default: *.flywheel.json)",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the TSV summary (e.g., info_summary.tsv)",
    )
    return parser.parse_args(list(argv))


def is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def flatten_info(info: Mapping[str, Any], parent_key: str = "") -> Dict[str, Any]:
    """Flatten nested dict under `info` using dot notation for keys.

    Lists are treated as atomic values and not expanded. Dicts are recursively
    flattened. Only terminal key-paths are returned.
    """
    flat: Dict[str, Any] = {}
    for key, value in info.items():
        if parent_key:
            path = f"{parent_key}.{key}"
        else:
            path = key

        if isinstance(value, dict):
            nested = flatten_info(value, parent_key=path)
            flat.update(nested)
        else:
            flat[path] = value
    return flat


def human_type_name(value: Any) -> str:
    # Normalize some common types for readability
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def find_json_files(root: Path, pattern: str) -> Iterable[Path]:
    # rglob handles recursive search; pattern is applied at filename level.
    return root.rglob(pattern)


def summarize_info(json_files: Iterable[Path]) -> Tuple[int, Dict[str, FieldStats]]:
    total_subjects = 0
    present_counts: Dict[str, int] = defaultdict(int)
    type_sets: Dict[str, set] = defaultdict(set)

    for json_path in json_files:
        # Only count files that we can parse as subject JSONs
        try:
            with json_path.open("r") as f:
                data = json.load(f)
        except Exception:
            # Skip unreadable or invalid JSON files, but do not increment total
            continue

        total_subjects += 1

        info_obj = data.get("info")
        if not isinstance(info_obj, dict):
            # No usable `info` field; count as missing for all fields implicitly
            continue

        flat = flatten_info(info_obj)
        for field_path, value in flat.items():
            if is_missing_value(value):
                continue
            present_counts[field_path] += 1
            type_sets[field_path].add(human_type_name(value))

    # Build FieldStats
    stats: Dict[str, FieldStats] = {}
    for field, count in present_counts.items():
        stats[field] = FieldStats(present_count=count, type_names=type_sets[field])
    return total_subjects, stats


def write_tsv(
    output_path: Path, total_subjects: int, stats: Dict[str, FieldStats]
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as out:
        out.write("field\tn_present\tn_missing\tpresent_pct\ttypes\n")
        for field in sorted(stats.keys()):
            present = stats[field].present_count
            missing = max(total_subjects - present, 0)
            pct = (present / total_subjects) if total_subjects > 0 else 0.0
            type_str = ",".join(sorted(stats[field].type_names))
            out.write(f"{field}\t{present}\t{missing}\t{pct:.4f}\t{type_str}\n")


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)

    root: Path = args.subjects_root
    pattern: str = args.pattern
    output: Path = args.output

    if not root.exists() or not root.is_dir():
        print(
            f"[error] subjects root not found or not a directory: {root}",
            file=sys.stderr,
        )
        return 2

    json_files = list(find_json_files(root, pattern))
    total, stats = summarize_info(json_files)
    write_tsv(output, total, stats)

    print(
        f"Scanned {len(json_files)} files; {total} valid subject JSONs.\n"
        f"Found {len(stats)} `info` fields with at least one present value.\n"
        f"Summary written to: {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
