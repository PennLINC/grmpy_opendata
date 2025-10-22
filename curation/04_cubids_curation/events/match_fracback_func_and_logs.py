import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def normalize_subject_id(raw_subject: str) -> str:
    """Return a normalized subject identifier used for matching.

    - Removes a leading 'sub-' if present
    - Returns lowercase for robust matching
    """
    subject = raw_subject
    if subject.startswith("sub-"):
        subject = subject[len("sub-") :]
    return subject.lower()


def collect_bids_fracback_funcs(bids_root: Path) -> Dict[str, List[Path]]:
    """Collect task-fracback NIfTI files from sub-*/ses-1/func/ directories.

    Returns a mapping of normalized subject id -> list of func file Paths.
    """
    funcs_by_subject: Dict[str, List[Path]] = {}

    # Limit search strictly to sub-*/ses-1/func/*task-fracback*.nii.gz
    pattern = "sub-*/ses-1/func/*task-fracback*.nii.gz"
    for func_path in bids_root.glob(pattern):
        if not func_path.is_file():
            continue
        # subject id is the immediate directory name starting with sub-
        try:
            subj_dir = next(p for p in func_path.parents if p.name.startswith("sub-"))
        except StopIteration:
            # If not found, skip conservatively
            print(
                f"[WARN] Could not infer subject for func: {func_path}",
                file=sys.stderr,
            )
            continue

        raw_subject = subj_dir.name  # e.g., sub-123
        norm_subject = normalize_subject_id(raw_subject)
        funcs_by_subject.setdefault(norm_subject, []).append(func_path)

    # Ensure canonical ordering for deterministic pairing
    for subject_id, files in funcs_by_subject.items():
        funcs_by_subject[subject_id] = sorted(files)
    return funcs_by_subject


def collect_flywheel_frac2b_logs(subjects_root: Path) -> Dict[str, List[Path]]:
    """Collect frac2B log files from Flywheel SUBJECTS directory.

    We treat each immediate subdirectory under subjects_root as a subject root,
    and search recursively for '*frac2B*.log' (case-insensitive for the 'B').

    Returns a mapping of normalized subject id -> list of log file Paths.
    """
    logs_by_subject: Dict[str, List[Path]] = {}

    if not subjects_root.exists():
        raise FileNotFoundError(
            f"Flywheel SUBJECTS directory not found: {subjects_root}"
        )

    for subj_dir in sorted([p for p in subjects_root.iterdir() if p.is_dir()]):
        raw_subject = subj_dir.name
        norm_subject = normalize_subject_id(raw_subject)

        # Search recursively for both frac2B and frac2b (case-insensitive 'B')
        matches: List[Path] = []
        for pattern in ("**/*frac2B*.log", "**/*frac2b*.log"):
            matches.extend(subj_dir.glob(pattern))
        # Deduplicate and sort
        unique_sorted = sorted({p for p in matches if p.is_file()})
        if unique_sorted:
            logs_by_subject[norm_subject] = unique_sorted

    return logs_by_subject


def pair_records(
    funcs_by_subject: Dict[str, List[Path]], logs_by_subject: Dict[str, List[Path]]
) -> List[Tuple[str, Path, Path]]:
    """Create rows pairing funcs and logs per subject.

    Rules:
    - Pair items one-to-one in sorted order up to the min length.
    - For extra funcs beyond logs, add rows with empty log.
    - For extra logs beyond funcs, add rows with empty func.
    - Include subjects that appear in only one side.

    Returns a list of tuples (subject_display, func_path_or_None, log_path_or_None).
    """
    rows: List[Tuple[str, Path, Path]] = []
    all_subjects = sorted(set(funcs_by_subject.keys()) | set(logs_by_subject.keys()))

    for norm_subject in all_subjects:
        # For display, use BIDS-style 'sub-<id>'
        subject_display = f"sub-{norm_subject}"
        func_list = funcs_by_subject.get(norm_subject, [])
        log_list = logs_by_subject.get(norm_subject, [])

        # Ensure lists are sorted for determinism
        func_list = sorted(func_list)
        log_list = sorted(log_list)

        min_len = min(len(func_list), len(log_list))
        # Paired rows
        for i in range(min_len):
            rows.append((subject_display, func_list[i], log_list[i]))

        # Extras funcs with no logs
        for i in range(min_len, len(func_list)):
            rows.append((subject_display, func_list[i], None))

        # Extra logs with no funcs
        for i in range(min_len, len(log_list)):
            rows.append((subject_display, None, log_list[i]))

    return rows


def write_tsv(rows: List[Tuple[str, Path, Path]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["subject_id", "func_path", "log_path"])
        for subject_id, func_path, log_path in rows:
            writer.writerow(
                [
                    subject_id,
                    str(func_path) if func_path is not None else "",
                    str(log_path) if log_path is not None else "",
                ]
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan BIDS and Flywheel directories for fracback funcs and frac2B logs, "
            "and produce a TSV mapping including unmatched rows."
        )
    )
    parser.add_argument(
        "--bids-root",
        type=Path,
        default=Path("/cbica/projects/grmpy/data/bids_datalad"),
        help="Path to BIDS root (containing sub-*/ directories)",
    )
    parser.add_argument(
        "--flywheel-subjects-root",
        type=Path,
        default=Path("/cbica/projects/grmpy/sourcedata/GRMPY_822831_log/SUBJECTS"),
        help="Path to Flywheel SUBJECTS root (containing per-subject directories)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("fracback_func_log_report.tsv"),
        help="Output TSV path",
    )
    args = parser.parse_args()

    print(f"[INFO] Scanning BIDS: {args.bids_root}", file=sys.stderr)
    funcs_by_subject = collect_bids_fracback_funcs(args.bids_root)
    print(
        f"[INFO] Found {sum(len(v) for v in funcs_by_subject.values())} fracback funcs across {len(funcs_by_subject)} subjects",
        file=sys.stderr,
    )

    print(
        f"[INFO] Scanning Flywheel SUBJECTS: {args.flywheel_subjects_root}",
        file=sys.stderr,
    )
    logs_by_subject = collect_flywheel_frac2b_logs(args.flywheel_subjects_root)
    print(
        f"[INFO] Found {sum(len(v) for v in logs_by_subject.values())} frac2B logs across {len(logs_by_subject)} subjects",
        file=sys.stderr,
    )

    rows = pair_records(funcs_by_subject, logs_by_subject)
    print(f"[INFO] Writing TSV: {args.out}", file=sys.stderr)
    write_tsv(rows, args.out)
    print(f"[INFO] Done. Rows written: {len(rows)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
