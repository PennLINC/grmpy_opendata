#!/usr/bin/env python3
"""
Summarize `info` fields across subject-level Flywheel JSON files.

Search strategy (per request):
- Only inspect immediate child directories of the SUBJECTS root (each assumed to
  be a subject directory named <sub-id>).
- In each subject directory, process exactly one file named
  <sub-id>.flywheel.json. No recursive descent into deeper subdirectories and no
  other JSON filenames are considered.

For each discovered subject JSON, the script loads the JSON, extracts and
flattens the top-level `info` object (if present), and produces a TSV
summarizing, for every flattened field, how many subjects have a non-missing
value.

Missingness definition:
- A value is considered missing if it is None, an empty string "", or an empty
  container (list/dict of length 0). Numeric zero (0) and boolean False are
  treated as present.

Output TSV columns:
- field: dot-delimited flattened key under `info` (e.g., demographics.height)
- n_present: number of subject JSONs with a non-missing value for this field
- n_missing: number of subject JSONs without a non-missing value for this field
- present_pct: n_present / total_subject_jsons, rounded to 4 decimals
- types: comma-separated set of Python value types observed for present values

Example
-------
```bash
python curation/04_cubids_curation/01_summarize_available_phenotypes.py \
  --subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
  --output /cbica/projects/grmpy/sourcedata/GRMPY_822831/info_summary.tsv
```
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
        description=(
            "Summarize flattened `info` fields across Flywheel JSON files in "
            "immediate SUBJECTS subdirectories (<sub-id>/<sub-id>.flywheel.json)."
        )
    )
    parser.add_argument(
        "--subjects-root",
        required=True,
        type=Path,
        help="Path to SUBJECTS root (e.g., /cbica/projects/.../SUBJECTS)",
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


def find_subject_jsons(subjects_root: Path) -> Iterable[Path]:
    """Yield paths like <root>/<sub-id>/<sub-id>.flywheel.json only.

    - Only immediate directories are considered subjects.
    - No recursion into nested subdirectories.
    - Only exact filename match <sub-id>.flywheel.json is used.
    """
    if not subjects_root.exists() or not subjects_root.is_dir():
        return []

    for child in sorted(subjects_root.iterdir()):
        if not child.is_dir():
            continue
        subject_id = child.name
        candidate = child / f"{subject_id}.flywheel.json"
        if candidate.exists() and candidate.is_file():
            yield candidate


def summarize_info(json_files: Iterable[Path]) -> Tuple[int, Dict[str, FieldStats]]:
    total_subjects = 0
    present_counts: Dict[str, int] = defaultdict(int)
    type_sets: Dict[str, set] = defaultdict(set)

    for json_path in json_files:
        try:
            with json_path.open("r") as f:
                data = json.load(f)
        except Exception:
            # Skip unreadable or invalid JSON files, but do not increment total
            continue

        total_subjects += 1

        info_obj = data.get("info")
        if not isinstance(info_obj, dict):
            continue

        flat = flatten_info(info_obj)
        for field_path, value in flat.items():
            if is_missing_value(value):
                continue
            present_counts[field_path] += 1
            type_sets[field_path].add(human_type_name(value))

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

    subjects_root: Path = args.subjects_root
    output: Path = args.output

    if not subjects_root.exists() or not subjects_root.is_dir():
        print(
            f"[error] subjects root not found or not a directory: {subjects_root}",
            file=sys.stderr,
        )
        return 2

    json_files = list(find_subject_jsons(subjects_root))
    total, stats = summarize_info(json_files)
    write_tsv(output, total, stats)

    print(
        f"Scanned {len(json_files)} candidate subject files; "
        f"{total} valid subject JSONs.\n"
        f"Found {len(stats)} `info` fields with at least one present value.\n"
        f"Summary written to: {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
