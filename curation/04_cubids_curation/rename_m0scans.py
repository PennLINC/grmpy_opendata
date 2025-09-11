import argparse
import subprocess
import sys
from pathlib import Path


def find_subject_entity(path: Path) -> str:
    """Return the subject entity (e.g., 'sub-1234') from a path."""
    for part in path.parts:
        if part.startswith("sub-"):
            return part
    raise ValueError(f"No subject entity found in path: {path}")


def rename_file_with_git_mv(src: Path, dst: Path, dry_run: bool = False) -> None:
    """Use git mv to rename a file. Skips if src == dst. Fails if dst exists."""
    if src.resolve() == dst.resolve():
        return
    if dst.exists():
        print(f"Destination exists, skipping: {dst}", file=sys.stderr)
        return
    cmd = ["git", "mv", str(src), str(dst)]
    if dry_run:
        print("DRY-RUN:", " ".join(cmd))
        return
    subprocess.run(cmd, check=True)


def rename_m0scans(root: Path, dry_run: bool = False) -> int:
    """
    Find all '*_m0scan.nii.gz' under sub-*/ses-1/perf/ and rename them (and matching .json)
    to 'sub-<ID>_ses-1_m0scan.*' using 'git mv'.
    Returns the count of NIfTI files processed.
    """
    processed = 0

    # Use root.glob to support absolute roots; Path().glob does not support absolute patterns
    pattern = "sub-*/ses-1/perf/*_m0scan.nii.gz"
    for nii_path in sorted(root.glob(pattern)):
        try:
            subject_entity = find_subject_entity(nii_path)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            continue

        dest_basename = f"{subject_entity}_ses-1_m0scan"
        dest_dir = nii_path.parent
        dest_nii = dest_dir / f"{dest_basename}.nii.gz"

        if nii_path.name == dest_nii.name:
            # Already correctly named
            continue

        # Move NIfTI first
        rename_file_with_git_mv(nii_path, dest_nii, dry_run=dry_run)
        processed += 1

        # If a JSON sidecar exists, move it too
        # Remove '.nii.gz' (7 chars) and append '.json'
        src_prefix = nii_path.name[:-7]
        src_json = dest_dir / f"{src_prefix}.json"
        if src_json.exists():
            dest_json = dest_dir / f"{dest_basename}.json"
            rename_file_with_git_mv(src_json, dest_json, dry_run=dry_run)

    return processed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Rename all m0scan files (and .json sidecars) in sub-*/ses-1/perf/ to "
            "'sub-<ID>_ses-1_m0scan.*' using git mv."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print git mv commands without executing them",
    )

    args = parser.parse_args()

    try:
        count = rename_m0scans(args.root, dry_run=args.dry_run)
    except subprocess.CalledProcessError as exc:
        print(f"git mv failed with exit code {exc.returncode}", file=sys.stderr)
        sys.exit(exc.returncode)

    if args.dry_run:
        print(f"DRY-RUN: would process {count} m0scan NIfTI file(s)")
    else:
        print(f"Processed {count} m0scan NIfTI file(s)")


if __name__ == "__main__":
    main()
