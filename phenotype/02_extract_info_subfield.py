#!/usr/bin/env python3
"""
Extract a specified subfield from the top-level `info` object across subject-level
Flywheel JSON files and concatenate into a single TSV table.

Discovery strategy (same as 01_summarize_available_phenotypes.py):
- Only inspect immediate child directories of the SUBJECTS root (each assumed to
  be a subject directory named <sub-id>).
- In each subject directory, process exactly one file named
  <sub-id>.flywheel.json. No recursive descent and no other JSON filenames are
  considered.

Behavior:
- The script accepts a dot-delimited path under `info` via --info-subfield
  (e.g., "demographics" or "session1.behavior").
- For each subject, the referenced subfield is extracted:
  - If the subfield resolves to a dict, it is recursively flattened using dot
    notation for keys (lists are treated as atomic values and not expanded).
  - If the subfield resolves to a scalar or a list, it is emitted as a single
    column named after the last path segment.
  - Missing subfields yield an empty row for that subject.
- Optional exclusions via --exclude remove exact fields or entire subtrees
  (prefix match) relative to the chosen subfield. Multiple --exclude values are
  allowed, and values can also be comma-separated.

Output:
- A TSV where the first column is `participant_id`, constructed as `sub-<sub-id>`
  where <sub-id> is the directory name of the subject.
- Remaining columns are the union of extracted field names across subjects,
  sorted alphabetically. Missing values are left blank.

Example
-------
```bash
python phenotype/02_extract_info_subfield.py \
  --subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
  --info-subfield demographics \
  --exclude height,weight \
  --output /cbica/projects/grmpy/sourcedata/GRMPY_822831/demographics.tsv
```
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Iterable as _Iterable, Mapping, Tuple


def parse_args(argv: _Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a specified `info` subfield across Flywheel JSON files in "
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
        "--info-subfield",
        required=True,
        type=str,
        help=(
            "Dot path under `info` to extract (e.g., demographics or session1.behavior)."
        ),
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help=(
            "Fields (relative to the chosen subfield) to exclude. Can be given "
            "multiple times or as a comma-separated list (prefix match removes subtrees)."
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the TSV table",
    )
    return parser.parse_args(list(argv))


def find_subject_jsons(subjects_root: Path) -> Iterable[Tuple[str, Path]]:
    """Yield pairs (subject_id, json_path) like (<sub-id>, <root>/<sub-id>/<sub-id>.flywheel.json>).

    - Only immediate directories are considered subjects.
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
            yield subject_id, candidate


def flatten_dict(obj: Mapping[str, Any], parent_key: str = "") -> Dict[str, Any]:
    """Flatten nested dict using dot notation for keys.

    Lists are treated as atomic values and not expanded. Dicts are recursively
    flattened. Only terminal key-paths are returned.
    """
    flat: Dict[str, Any] = {}
    for key, value in obj.items():
        path = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            flat.update(flatten_dict(value, parent_key=path))
        else:
            flat[path] = value
    return flat


def stringify_value(value: Any) -> str:
    """Convert a value to a TSV-safe string.

    - None becomes "" (missing)
    - Lists/dicts are JSON-serialized
    - Other types use str()
    """
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def split_excludes(values: Iterable[str]) -> Tuple[str, ...]:
    items: list[str] = []
    for v in values:
        if not v:
            continue
        parts = [p.strip() for p in v.split(",")]
        items.extend([p for p in parts if p])
    # Deduplicate while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def is_excluded(field: str, excludes: Tuple[str, ...]) -> bool:
    for ex in excludes:
        if field == ex or field.startswith(ex + "."):
            return True
    return False


def resolve_info_subfield(info_obj: Any, subpath: str) -> Tuple[Dict[str, Any], bool]:
    """Resolve a path under `info`.

    Returns (mapping, is_dict_like).
    - If the resolved object is a dict, returns its flattened mapping and True.
    - If scalar/list, returns a single-field mapping where the field name is the
      last segment of the subpath and False.
    - If path cannot be resolved, returns empty mapping and False.
    """
    if not isinstance(info_obj, dict):
        return {}, False

    node: Any = info_obj
    segments = [s for s in subpath.split(".") if s]
    for seg in segments:
        if isinstance(node, dict) and seg in node:
            node = node[seg]
        else:
            return {}, False

    if isinstance(node, dict):
        return flatten_dict(node), True

    # Scalar or list
    leaf_name = segments[-1] if segments else "value"
    return {leaf_name: node}, False


def write_tsv(
    output_path: Path,
    header_fields: Tuple[str, ...],
    rows: Iterable[Tuple[str, Dict[str, str]]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as out:
        out.write("participant_id\t" + "\t".join(header_fields) + "\n")
        for participant_id, field_map in rows:
            values = [field_map.get(h, "") for h in header_fields]
            out.write(participant_id + "\t" + "\t".join(values) + "\n")


def main(argv: _Iterable[str]) -> int:
    args = parse_args(argv)

    subjects_root: Path = args.subjects_root
    info_subfield: str = args.info_subfield
    output: Path = args.output
    excludes: Tuple[str, ...] = split_excludes(args.exclude)

    if not subjects_root.exists() or not subjects_root.is_dir():
        print(
            f"[error] subjects root not found or not a directory: {subjects_root}",
            file=sys.stderr,
        )
        return 2

    # Accumulate per-subject flattened fields and union of field names
    per_subject: list[Tuple[str, Dict[str, str]]] = []
    field_union: set[str] = set()

    for subject_id, json_path in find_subject_jsons(subjects_root):
        try:
            with json_path.open("r") as f:
                data = json.load(f)
        except Exception:
            # Skip unreadable or invalid JSON files
            continue

        info_obj = data.get("info")
        flat_map, _ = resolve_info_subfield(info_obj, info_subfield)

        # Apply exclusions
        filtered: Dict[str, str] = {}
        for field, value in flat_map.items():
            if is_excluded(field, excludes):
                continue
            filtered[field] = stringify_value(value)

        # participant_id is always `sub-<sub-id>` using directory name as <sub-id>
        participant_id = f"sub-{subject_id}"

        per_subject.append((participant_id, filtered))
        field_union.update(filtered.keys())

    header_fields = tuple(sorted(field_union))
    write_tsv(output, header_fields, per_subject)

    print(
        f"Wrote {len(per_subject)} rows with {len(header_fields)} fields to: {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
