#!/usr/bin/env python3
"""
Remove run- entities from BIDS filenames and update IntendedFor in fmap JSONs.

This script recursively scans a BIDS directory, identifies files whose
basename contains a run entity ("_run-<digits>") and plans renames that remove
the run entity from the stem. It also finds and updates IntendedFor fields in
the corresponding subject/session `fmap/*.json` files so that references to
renamed files are updated, and removes IntendedFor entries that refer to files
that no longer exist.

Key behaviors:
- Includes files inside any `fmap/` directory as well.
- Renames data files (.nii/.nii.gz) and common sidecars with the same stem
  (.json, .tsv, .tsv.gz, .bval, .bvec).
- Updates IntendedFor entries that reference renamed files (subject-relative
  paths) and drops references that point to non-existent files after renames.
- Supports a dry-run mode to report planned changes without modifying files.

Usage:
  python remove_run_and_fix_intendedfor.py /path/to/bids_dir [--dry-run]

Notes:
- IntendedFor values can be a string or a list; both forms are supported.
- Name collisions after removing run- are detected; such files are skipped and
  reported.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


RUN_TOKEN_RE = re.compile(r"_run-\d+")


@dataclass
class RenamePlan:
    """Represents a rename for one file (and its sidecars)."""

    src: Path
    dst: Path


def split_name_suffix(name: str) -> Tuple[str, str]:
    """Split filename into stem and suffix (extension with leading dot[s]).

    Examples:
      'file.nii.gz' -> ('file', '.nii.gz')
      'file.nii'    -> ('file', '.nii')
      'file.json'   -> ('file', '.json')
      'file'        -> ('file', '')
    """
    if name.endswith(".nii.gz"):
        return name[:-7], ".nii.gz"
    if name.endswith(".nii"):
        return name[:-4], ".nii"
    dot = name.rfind(".")
    if dot == -1:
        return name, ""
    return name[:dot], name[dot:]


def subject_and_session_from_path(p: Path) -> Optional[Tuple[str, Optional[str]]]:
    """Extract subject (sub-XXX) and session (ses-YYY if present) from path parts."""
    subject: Optional[str] = None
    session: Optional[str] = None
    for part in p.parts:
        if part.startswith("sub-"):
            subject = part
        elif part.startswith("ses-"):
            session = part
        if subject and session:
            break
    if not subject:
        return None
    return subject, session


def is_inside_fmap(p: Path) -> bool:
    return "fmap" in p.parts


def candidate_sidecars(img_path: Path) -> Iterable[Path]:
    """Yield common sidecars that share the same stem as img_path.

    Includes: .json, .tsv, .tsv.gz, .bval, .bvec
    """
    stem, _ = split_name_suffix(img_path.name)
    for ext in (".json", ".tsv", ".tsv.gz", ".bval", ".bvec"):
        yield img_path.with_name(f"{stem}{ext}")


def compute_rename_plans(bids_dir: Path) -> List[RenamePlan]:
    """Find files with a run- entity and plan renames to remove it."""
    plans: List[RenamePlan] = []
    planned_dsts: Set[Path] = set()

    # Consider both image and non-image files; but we will primarily use image
    # renames to drive IntendedFor mapping. We include sidecars separately.
    for src in bids_dir.rglob("*"):
        if not src.is_file():
            continue
        # Only consider BIDS-like files that include _run-<digits>
        if not RUN_TOKEN_RE.search(src.name):
            continue

        stem, suffix = split_name_suffix(src.name)
        new_stem = RUN_TOKEN_RE.sub("", stem)
        if new_stem == stem:
            continue
        dst = src.with_name(f"{new_stem}{suffix}")

        # Detect collision either with existing file or another planned dst
        if dst.exists() or dst in planned_dsts:
            print(
                f"WARNING: Skipping due to destination collision: {src} -> {dst}",
                file=sys.stderr,
            )
            continue

        plans.append(RenamePlan(src=src, dst=dst))
        planned_dsts.add(dst)

    return plans


def build_intendedfor_mapping(
    plans: Sequence[RenamePlan], bids_dir: Path
) -> Dict[str, str]:
    """Map subject-relative NIfTI paths with run- to new subject-relative paths.

    Only includes NIfTI files (.nii or .nii.gz). Keys and values use POSIX-style
    relative paths (e.g., 'ses-01/func/sub-XX_ses-01_task-YY_bold.nii.gz'
    without the leading 'sub-XX/').
    """
    rel_map: Dict[str, str] = {}
    for plan in plans:
        # Only for NIfTI files; IntendedFor references NIfTI paths
        if not (
            str(plan.src.name).endswith(".nii")
            or str(plan.src.name).endswith(".nii.gz")
        ):
            continue
        ss = subject_and_session_from_path(plan.src)
        if not ss:
            continue
        subject, _ = ss
        try:
            src_rel = plan.src.relative_to(bids_dir / subject)
            dst_rel = plan.dst.relative_to(bids_dir / subject)
        except ValueError:
            # Not under the subject root; skip
            continue
        # Normalize to posix strings
        rel_map[str(PurePosixPath(src_rel))] = str(PurePosixPath(dst_rel))
    return rel_map


def sidecars_for_plan(plan: RenamePlan) -> List[RenamePlan]:
    """Generate rename plans for sidecars with same stem as the main file.

    Only generate sidecar plans when the main plan is for a NIfTI image to
    avoid duplicating plans for JSON/TSV/etc. that already match RUN_TOKEN_RE
    and will be handled directly by compute_rename_plans.
    """
    sidecar_plans: List[RenamePlan] = []
    if not (
        str(plan.src.name).endswith(".nii") or str(plan.src.name).endswith(".nii.gz")
    ):
        return sidecar_plans
    src_stem, _ = split_name_suffix(plan.src.name)
    dst_stem, _ = split_name_suffix(plan.dst.name)
    for ext in (".json", ".tsv", ".tsv.gz", ".bval", ".bvec"):
        src_sc = plan.src.with_name(f"{src_stem}{ext}")
        if src_sc.exists():
            dst_sc = plan.dst.with_name(f"{dst_stem}{ext}")
            sidecar_plans.append(RenamePlan(src=src_sc, dst=dst_sc))
    return sidecar_plans


def apply_renames(plans: Sequence[RenamePlan], dry_run: bool) -> None:
    for plan in plans:
        print(f"RENAME: {plan.src} -> {plan.dst}")
        if dry_run:
            continue
        plan.dst.parent.mkdir(parents=True, exist_ok=True)
        if plan.dst.exists():
            print(
                f"WARNING: Destination already exists, skipping: {plan.dst}",
                file=sys.stderr,
            )
            continue
        plan.src.rename(plan.dst)


def list_fmap_jsons_for_session(
    bids_dir: Path, subject: str, session: Optional[str]
) -> List[Path]:
    base = bids_dir / subject
    if session:
        base = base / session
    fmap_dir = base / "fmap"
    if not fmap_dir.exists() or not fmap_dir.is_dir():
        return []
    return [p for p in fmap_dir.glob("*.json") if p.is_file()]


def ensure_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for it in items:
        if it not in seen:
            seen.add(it)
            result.append(it)
    return result


def exists_after_renames(
    rel_path: str, subject: str, bids_dir: Path, rel_map: Dict[str, str]
) -> bool:
    """Check if a subject-relative NIfTI path would exist after applying renames."""
    # If path is a key in rel_map, it gets renamed to the mapped value
    if rel_path in rel_map:
        final_rel = rel_map[rel_path]
    else:
        final_rel = rel_path
    abs_path = bids_dir / subject / Path(final_rel)
    return abs_path.exists()


def update_intendedfor_in_json(
    json_path: Path,
    subject: str,
    rel_map: Dict[str, str],
    bids_dir: Path,
    dry_run: bool,
) -> Tuple[bool, List[Tuple[str, Optional[str]]]]:
    """Update IntendedFor entries in a fieldmap JSON.

    Returns a tuple (changed, changes_list) where changes_list contains tuples of
    (old_rel, new_rel_or_None if removed).
    """
    try:
        with json_path.open("r") as f:
            data = json.load(f)
    except Exception as exc:  # noqa: BLE001
        print(f"WARNING: Could not read JSON {json_path}: {exc}", file=sys.stderr)
        return False, []

    if "IntendedFor" not in data:
        return False, []

    original = ensure_list(data["IntendedFor"])
    updated: List[str] = []
    changes: List[Tuple[str, Optional[str]]] = []

    for rel in original:
        # Normalize to posix
        rel_posix = str(PurePosixPath(rel))
        # If this path is being renamed, substitute
        if rel_posix in rel_map:
            new_rel = rel_map[rel_posix]
            updated.append(new_rel)
            if new_rel != rel_posix:
                changes.append((rel_posix, new_rel))
            continue

        # If not explicitly mapped but still exists after renames, keep
        if exists_after_renames(rel_posix, subject, bids_dir, rel_map):
            updated.append(rel_posix)
        else:
            # Remove stale reference
            changes.append((rel_posix, None))

    # Deduplicate while preserving order
    updated_unique = unique_preserve_order(updated)

    if updated_unique == original:
        return False, []

    # Write back
    print(f"UPDATE IntendedFor: {json_path}")
    for old_rel, new_rel in changes:
        if new_rel is None:
            print(f"  REMOVE: {old_rel}")
        else:
            print(f"  {old_rel} -> {new_rel}")

    if not dry_run:
        try:
            data["IntendedFor"] = (
                updated_unique if len(updated_unique) != 1 else updated_unique
            )
            with json_path.open("w") as f:
                json.dump(data, f, indent=2, sort_keys=True)
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: Failed writing JSON {json_path}: {exc}", file=sys.stderr)
            return False, changes

    return True, changes


def update_all_fmap_intendedfor(
    bids_dir: Path,
    rel_map: Dict[str, str],
    dry_run: bool,
) -> None:
    """Update IntendedFor across fmap JSONs affected by the rel_map."""
    # Group by subject and session (if present). Support datasets with or without sessions.
    subjects: Set[str] = set()
    sessions_by_subject: Dict[str, Set[Optional[str]]] = {}

    for abs_path in bids_dir.rglob("sub-*/**/*.nii*"):
        ss = subject_and_session_from_path(abs_path)
        if not ss:
            continue
        sub, ses = ss
        subjects.add(sub)
        sessions_by_subject.setdefault(sub, set()).add(ses)

    # Process fmap JSONs per subject/session
    for subject in sorted(subjects):
        for session in sorted(
            sessions_by_subject.get(subject, {None}),
            key=lambda x: ("" if x is None else x),
        ):
            for json_path in list_fmap_jsons_for_session(bids_dir, subject, session):
                update_intendedfor_in_json(
                    json_path, subject, rel_map, bids_dir, dry_run
                )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Remove run- entities from BIDS filenames and update IntendedFor references in fmap JSONs."
        )
    )
    parser.add_argument("bids_dir", type=Path, help="Path to BIDS directory (root)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned changes without modifying files",
    )
    args = parser.parse_args(argv)

    bids_dir: Path = args.bids_dir
    dry_run: bool = args.dry_run

    if not bids_dir.exists() or not bids_dir.is_dir():
        print(f"Error: '{bids_dir}' is not a directory", file=sys.stderr)
        return 2

    # Plan core renames
    core_plans = compute_rename_plans(bids_dir)
    if not core_plans:
        print("No files with run- entities found.")
    else:
        # Expand with sidecars for each planned rename
        all_plans: List[RenamePlan] = []
        for p in core_plans:
            all_plans.append(p)
            all_plans.extend(sidecars_for_plan(p))

        # Apply renames (or report in dry-run)
        apply_renames(all_plans, dry_run=dry_run)

    # Build IntendedFor mapping from planned NIfTI renames
    rel_map = build_intendedfor_mapping(core_plans, bids_dir)

    # Update fmap IntendedFor (also cleans stale references)
    update_all_fmap_intendedfor(bids_dir, rel_map, dry_run=dry_run)

    if dry_run:
        print("Dry run complete; no files modified.")
    else:
        print("Completed renames and IntendedFor updates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
