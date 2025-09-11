#!/usr/bin/env python3
"""
Fix BIDS entity order for anat files where run- precedes rec-.

Target pattern (incorrect):
  sub-*/ses-*/anat/... run-XX _ rec-YYY ...
Should be (correct):
  sub-*/ses-*/anat/... rec-YYY _ run-XX ...

This script recursively scans below a given BIDS directory for files in
sub-*/ses-*/anat/ with suffixes like T1w/T2w/etc., identifies filenames where
the 'run-' entity appears before the 'rec-' entity, and renames them so that
the 'rec-' entity comes immediately before the 'run-' entity. Matching JSON
sidecars are also renamed if present.

Usage:
  python fix_run_rec_entities.py /path/to/bids_dir [--dry-run]

Notes:
  - Only files within sub-*/ses-*/anat/ are affected.
  - Both .nii and .nii.gz are supported, along with optional .json sidecars.
  - Renames are reported; in dry-run mode no files are modified.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class RenamePlan:
    src: Path
    dst: Path
    sidecar_src: Optional[Path]
    sidecar_dst: Optional[Path]


def is_anat_path(p: Path) -> bool:
    parts = p.parts
    try:
        anat_idx = parts.index("anat")
    except ValueError:
        return False
    # Ensure that there is a sub-*/ses-* above anat dir
    if anat_idx >= 2:
        return parts[anat_idx - 2].startswith("sub-") and parts[
            anat_idx - 1
        ].startswith("ses-")
    return False


def split_name_suffix(name: str) -> Tuple[str, str]:
    """Split basename into stem and suffix including dots.

    Examples:
      'file.nii.gz' -> ('file', '.nii.gz')
      'file.nii'    -> ('file', '.nii')
      'file'        -> ('file', '')
    """
    if name.endswith(".nii.gz"):
        return name[:-7], ".nii.gz"
    if name.endswith(".nii"):
        return name[:-4], ".nii"
    if name.endswith(".json"):
        return name[:-5], ".json"
    dot = name.rfind(".")
    if dot == -1:
        return name, ""
    return name[:dot], name[dot:]


def derive_sidecar_path(img_path: Path) -> Optional[Path]:
    stem, ext = split_name_suffix(img_path.name)
    if ext not in {".nii", ".nii.gz"}:
        return None
    return img_path.with_name(f"{stem}.json")


def reorder_run_rec(stem: str) -> Optional[str]:
    """If stem contains run- before rec-, return new stem with rec- before run-.

    We only swap the first occurrence of these entities and keep the rest of
    the stem as-is. If order is already correct or one is missing, return None.
    """
    run_idx = stem.find("_run-")
    rec_idx = stem.find("_rec-")

    # If either is missing, or rec- already appears before run-, do nothing
    if run_idx == -1 or rec_idx == -1 or rec_idx < run_idx:
        return None

    # Identify the full tokens: _run-<val> and _rec-<val>
    def token_bounds(start: int) -> Tuple[int, int]:
        end = stem.find("_", start + 1)
        if end == -1:
            end = len(stem)
        return start, end

    run_start, run_end = token_bounds(run_idx)
    rec_start, rec_end = token_bounds(rec_idx)

    # Ensure run- actually precedes rec- in the string
    if run_start < rec_start:
        # Build new stem: prefix + rec_token + run_token + remainder (excluding original tokens)
        prefix = stem[:run_start]
        mid_between = stem[run_end:rec_start]
        run_token = stem[run_start:run_end]
        rec_token = stem[rec_start:rec_end]
        suffix = stem[rec_end:]

        # Swap order to rec then run, preserving any text between tokens at the original location
        # If there was anything between run and rec (unlikely for entities), keep it after the swap
        new_stem = f"{prefix}{rec_token}{mid_between}{run_token}{suffix}"
        return new_stem

    return None


def plan_renames(bids_dir: Path) -> List[RenamePlan]:
    plans: List[RenamePlan] = []
    for img_path in bids_dir.rglob("*.nii*"):
        if not img_path.is_file():
            continue
        if not is_anat_path(img_path):
            continue
        stem, ext = split_name_suffix(img_path.name)
        new_stem = reorder_run_rec(stem)
        if not new_stem:
            continue
        dst_img = img_path.with_name(f"{new_stem}{ext}")
        sidecar_src = derive_sidecar_path(img_path)
        sidecar_dst = None
        if sidecar_src and sidecar_src.exists():
            # Use same stem transformation for sidecar
            sc_stem, _ = split_name_suffix(sidecar_src.name)
            sc_new_stem = reorder_run_rec(sc_stem) or sc_stem
            sidecar_dst = sidecar_src.with_name(f"{sc_new_stem}.json")
        plans.append(
            RenamePlan(
                src=img_path,
                dst=dst_img,
                sidecar_src=sidecar_src
                if sidecar_src and sidecar_src.exists()
                else None,
                sidecar_dst=sidecar_dst,
            )
        )
    return plans


def apply_renames(plans: List[RenamePlan], dry_run: bool) -> None:
    for plan in plans:
        print(f"RENAME: {plan.src} -> {plan.dst}")
        if plan.sidecar_src and plan.sidecar_dst:
            print(f"RENAME: {plan.sidecar_src} -> {plan.sidecar_dst}")
        if dry_run:
            continue
        # Create destination parent dirs just in case
        plan.dst.parent.mkdir(parents=True, exist_ok=True)
        if plan.dst.exists():
            print(
                f"WARNING: Destination already exists, skipping file: {plan.dst}",
                file=sys.stderr,
            )
        else:
            plan.src.rename(plan.dst)
        if plan.sidecar_src and plan.sidecar_dst:
            plan.sidecar_dst.parent.mkdir(parents=True, exist_ok=True)
            if plan.sidecar_dst.exists():
                print(
                    f"WARNING: Destination already exists, skipping sidecar: {plan.sidecar_dst}",
                    file=sys.stderr,
                )
            else:
                plan.sidecar_src.rename(plan.sidecar_dst)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fix run/rec entity order for anat files in a BIDS dataset"
    )
    parser.add_argument("bids_dir", type=Path, help="Path to BIDS directory (root)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned renames without changing files",
    )
    args = parser.parse_args(argv)

    bids_dir: Path = args.bids_dir
    dry_run: bool = args.dry_run

    if not bids_dir.exists() or not bids_dir.is_dir():
        print(f"Error: '{bids_dir}' is not a directory", file=sys.stderr)
        return 2

    plans = plan_renames(bids_dir)
    if not plans:
        print("No files requiring run/rec reordering were found under anat.")
        return 0

    apply_renames(plans, dry_run=dry_run)
    if dry_run:
        print("Dry run complete; no files modified.")
    else:
        print("Renaming complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
