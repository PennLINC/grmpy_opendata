#!/usr/bin/env python3
"""
Round AcquisitionTime fields in BIDS JSON sidecars to the nearest hour.

This script recursively scans a BIDS directory for all .json files,
looks for the top-level "AcquisitionTime" field, and, if present,
rounds it to the nearest hour. It writes changes back in place and
generates a report listing the before and after times for verification.

Usage:
  python round_AcquisitionTime.py /path/to/bids_dir \
      --report /path/to/report.txt

Optional flags:
  --dry-run    Perform a read-only run; do not modify any files
  --report     Path to write the before/after report (default: acquisition_time_rounding_report.txt)

Notes:
  - Times are normalized to the format HH:MM:SS (no fractional seconds) after rounding.
  - If rounding results in 24:00:00, the time wraps to 00:00:00.
  - Files without an "AcquisitionTime" field or with unparseable values are reported as skipped.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Optional, List


@dataclass
class ProcessResult:
    file_path: Path
    present: bool
    before: Optional[str]
    after: Optional[str]
    changed: bool
    reason: Optional[str] = None  # For skipped/unparseable cases


def parse_time_string(value: str) -> Optional[time]:
    """Parse various time string formats into a datetime.time.

    Supported formats include:
      - HH:MM:SS(.ffffff)
      - HH:MM (assumes seconds=0)
      - HHMMSS(.ffffff)

    Returns None if the string cannot be parsed.
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None

    # Pattern 1: HH:MM[:SS[.ffffff]]
    m = re.match(
        r"^(?P<h>\d{1,2}):(?P<m>\d{2})(?::(?P<s>\d{2})(?:\.(?P<f>\d{1,6}))?)?$", s
    )
    if m:
        hour = int(m.group("h"))
        minute = int(m.group("m"))
        second = int(m.group("s") or 0)
        micro_str = m.group("f")
        micro = int(micro_str.ljust(6, "0")) if micro_str else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            return None
        return time(hour=hour, minute=minute, second=second, microsecond=micro)

    # Pattern 2: HHMMSS[.ffffff]
    m2 = re.match(r"^(?P<h>\d{2})(?P<m>\d{2})(?P<s>\d{2})(?:\.(?P<f>\d{1,6}))?$", s)
    if m2:
        hour = int(m2.group("h"))
        minute = int(m2.group("m"))
        second = int(m2.group("s"))
        micro_str = m2.group("f")
        micro = int(micro_str.ljust(6, "0")) if micro_str else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
            return None
        return time(hour=hour, minute=minute, second=second, microsecond=micro)

    return None


def round_to_nearest_hour(t: time) -> time:
    """Round a time to the nearest hour, returning HH:00:00 (no microseconds).

    Rounding rule: offset from the hour >= 30 minutes (including seconds and
    microseconds) rounds up to the next hour (wrapping at 24), otherwise rounds
    down to the current hour.
    """
    offset_us = (t.minute * 60 + t.second) * 1_000_000 + t.microsecond
    threshold_us = 30 * 60 * 1_000_000
    if offset_us >= threshold_us:
        new_hour = (t.hour + 1) % 24
    else:
        new_hour = t.hour
    return time(hour=new_hour, minute=0, second=0, microsecond=0)


def format_time_hhmmss(t: time) -> str:
    return f"{t.hour:02d}:{t.minute:02d}:{t.second:02d}"


def process_json_file(json_path: Path, dry_run: bool) -> ProcessResult:
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return ProcessResult(
            file_path=json_path,
            present=False,
            before=None,
            after=None,
            changed=False,
            reason=f"Failed to read JSON: {e}",
        )

    if not isinstance(data, dict):
        return ProcessResult(
            file_path=json_path,
            present=False,
            before=None,
            after=None,
            changed=False,
            reason="Top-level JSON is not an object",
        )

    if "AcquisitionTime" not in data:
        return ProcessResult(
            file_path=json_path,
            present=False,
            before=None,
            after=None,
            changed=False,
            reason="No AcquisitionTime field",
        )

    original_value = data.get("AcquisitionTime")
    original_str = str(original_value) if original_value is not None else None
    parsed = parse_time_string(original_str or "")
    if parsed is None:
        return ProcessResult(
            file_path=json_path,
            present=True,
            before=original_str,
            after=None,
            changed=False,
            reason="Unrecognized time format",
        )

    rounded = round_to_nearest_hour(parsed)
    rounded_str = format_time_hhmmss(rounded)

    # Determine if a change should be written. We normalize the original string to HH:MM:SS if it
    # already represents an exact hour, but only mark as changed if the hour/min/sec differ after rounding.
    # If the parsed time is already exactly at HH:00:00, we still standardize format but do not count as changed.
    original_exact = (
        parsed.minute == 0 and parsed.second == 0 and parsed.microsecond == 0
    )
    will_change_content = (
        (rounded.hour != parsed.hour)
        or (parsed.minute != 0)
        or (parsed.second != 0)
        or (parsed.microsecond != 0)
    )

    if will_change_content and not dry_run:
        data["AcquisitionTime"] = rounded_str
        try:
            with json_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                f.write("\n")
        except Exception as e:
            return ProcessResult(
                file_path=json_path,
                present=True,
                before=original_str,
                after=None,
                changed=False,
                reason=f"Failed to write JSON: {e}",
            )

    return ProcessResult(
        file_path=json_path,
        present=True,
        before=original_str,
        after=rounded_str
        if will_change_content
        else original_str
        if original_exact
        else rounded_str,
        changed=will_change_content,
        reason=None,
    )


def find_json_files(bids_dir: Path) -> List[Path]:
    return sorted(p for p in bids_dir.rglob("*.json") if p.is_file())


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Round BIDS AcquisitionTime values to nearest hour."
    )
    parser.add_argument(
        "bids_dir", type=Path, help="Path to the BIDS directory to scan"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("acquisition_time_rounding_report.txt"),
        help="Path to write the before/after report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a read-only run; do not modify files",
    )
    args = parser.parse_args(argv)

    bids_dir: Path = args.bids_dir
    report_path: Path = args.report
    dry_run: bool = args.dry_run

    if not bids_dir.exists() or not bids_dir.is_dir():
        print(f"Error: '{bids_dir}' is not a directory", file=sys.stderr)
        return 2

    json_files = find_json_files(bids_dir)
    if not json_files:
        print("No JSON files found.")
        return 0

    results: List[ProcessResult] = []
    for jp in json_files:
        res = process_json_file(jp, dry_run=dry_run)
        results.append(res)

    # Write report
    lines: List[str] = []
    lines.append("# AcquisitionTime rounding report\n")
    lines.append(f"BIDS dir: {bids_dir.resolve()}\n")
    lines.append(f"Dry run: {dry_run}\n")
    total = len(results)
    with_time = sum(1 for r in results if r.present)
    changed = sum(1 for r in results if r.changed)
    skipped = sum(1 for r in results if r.present and r.after is None)
    lines.append(f"Total JSON files scanned: {total}\n")
    lines.append(f"Files with AcquisitionTime: {with_time}\n")
    lines.append(f"Files changed: {changed}\n")
    lines.append(f"Files skipped (unparseable): {skipped}\n")
    lines.append("\n")

    for r in results:
        if not r.present:
            # No AcquisitionTime; omit from detailed mapping to keep report concise
            continue
        if r.after is None:
            lines.append(
                f"{r.file_path}: AcquisitionTime: {r.before} -> SKIPPED ({r.reason})\n"
            )
        else:
            suffix = " [CHANGED]" if r.changed else ""
            lines.append(
                f"{r.file_path}: AcquisitionTime: {r.before} -> {r.after}{suffix}\n"
            )

    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"Failed to write report to {report_path}: {e}", file=sys.stderr)
        return 1

    print(f"Report written to: {report_path}")
    if not dry_run:
        print(f"Files updated: {changed}")
    else:
        print("Dry run complete; no files modified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
