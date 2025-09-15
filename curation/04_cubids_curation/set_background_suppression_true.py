#!/usr/bin/env python3
"""
Scan a BIDS directory for ASL JSON sidecars in perf directories and update
the "BackgroundSuppression" field from false to true.

Usage:
  python set_background_suppression_true.py /path/to/bids_dir [--dry-run]

Notes:
- Only files under perf/ are considered.
- Files inside derivatives/ are skipped.
- Only updates when BackgroundSuppression exists and is false (boolean or string "false").
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Tuple


def iter_asl_json_files(bids_root: Path) -> Iterable[Path]:
    """Yield ASL JSON files under perf/ while skipping derivatives/.

    Parameters
    ----------
    bids_root: Path
        The root directory of the BIDS dataset.
    """
    # Match typical BIDS ASL JSON filenames
    for json_path in bids_root.rglob("*_asl.json"):
        parts = json_path.parts
        if any(part == "derivatives" for part in parts):
            continue
        if "perf" not in parts:
            continue
        yield json_path


def should_set_true(value) -> bool:
    """Return True if the given value represents a false that should be set to True."""
    if isinstance(value, bool):
        return value is False
    if isinstance(value, str):
        return value.strip().lower() == "false"
    return False


def update_background_suppression(json_path: Path, dry_run: bool) -> Tuple[bool, str]:
    """Update BackgroundSuppression from false to true in a single JSON file.

    Returns (changed, message).
    """
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001
        return False, f"ERROR reading {json_path}: {exc}"

    if "BackgroundSuppression" not in data:
        return False, f"SKIP (missing field): {json_path}"

    if not should_set_true(data["BackgroundSuppression"]):
        return False, f"SKIP (already true or non-false): {json_path}"

    data["BackgroundSuppression"] = True

    if dry_run:
        return True, f"DRY-RUN would update: {json_path}"

    try:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            f.write("\n")
    except Exception as exc:  # noqa: BLE001
        return False, f"ERROR writing {json_path}: {exc}"

    return True, f"UPDATED: {json_path}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Update BackgroundSuppression from false to true in ASL JSON sidecars under perf/."
        )
    )
    parser.add_argument(
        "bids_dir", type=Path, help="Absolute path to the BIDS dataset root"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report changes; do not write files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bids_root: Path = args.bids_dir.resolve()

    if not bids_root.exists() or not bids_root.is_dir():
        raise SystemExit(f"BIDS directory not found or not a directory: {bids_root}")

    changed_count = 0
    skipped_count = 0
    error_count = 0

    for json_path in iter_asl_json_files(bids_root):
        changed, message = update_background_suppression(json_path, args.dry_run)
        print(message)
        if message.startswith("ERROR"):
            error_count += 1
        elif changed:
            changed_count += 1
        else:
            skipped_count += 1

    summary = f"Completed. Changed: {changed_count}, Skipped: {skipped_count}, Errors: {error_count}."
    print(summary)


if __name__ == "__main__":
    main()
