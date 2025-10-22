#!/usr/bin/env python3
"""
Convert GRMPY fractional n-back logs to BIDS-compliant events and update participants.tsv.

What it does (GRMPY-specific):
- Scans BIDS output for fracback funcs at --output-dir/sub-*/ses-1/func/*task-fracback*_bold.nii.gz
- Finds matching frac2B logs under --logs-dir per subject (case-insensitive 'B').
  If no log: skip and print. If multiple logs: use the first (previously confirmed that multiple logs are not diff).
- Loads scoring template XML (includes 0BACK, 1BACK, 2BACK) and reproduces the RT extraction logic.
- Writes BIDS events TSV/JSON alongside each func with columns:
  onset, duration, trial_type, results, response_time, score.
- Computes per-subject performance metrics (including d-prime) and updates
  --output-dir/participants.tsv (row 'participant_id' = sub-<id>), adding columns if needed.

CLI inputs:
- --xml: Path to task XML template (default: /cbica/projects/code/curation/04_cubids_curation/events/grmpytemplate.xml)
- --logs-dir: Flywheel SUBJECTS root (default: /cbica/projects/grmpy/sourcedata/GRMPY_822831_log/SUBJECTS)
- --output-dir: BIDS root (default: /cbica/projects/grmpy/data/bids_datalad)
- --dry-run: Print planned actions as JSON and make no file changes
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from scipy.stats import norm


# ------------------------------ CLI & Utilities ------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert GRMPY fracback .log files to BIDS events and participants metrics."
        ),
    )
    parser.add_argument(
        "--xml",
        type=Path,
        default=Path(
            "/cbica/projects/grmpy/code/curation/04_cubids_curation/events/grmpytemplate.xml"
        ),
        help="Path to task XML template used for scoring",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("/cbica/projects/grmpy/sourcedata/GRMPY_822831_log/SUBJECTS"),
        help="Flywheel SUBJECTS root containing per-subject directories (searched recursively)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/cbica/projects/grmpy/data/bids_datalad"),
        help="BIDS root directory to read funcs and write events/participants",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write any files; print a JSON report of intended actions",
    )
    return parser.parse_args()


def discover_log_files(logs_dir: Path) -> List[Path]:
    return sorted([p for p in logs_dir.rglob("*.log") if p.is_file()])


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
    """Collect fracback BOLD NIfTI files from sub-*/ses-1/func/ directories.

    Returns mapping of normalized subject id -> list of func file Paths.
    """
    funcs_by_subject: Dict[str, List[Path]] = {}
    for func_path in bids_root.glob("sub-*/ses-1/func/*task-fracback*_bold.nii.gz"):
        if not func_path.is_file():
            continue
        try:
            subj_dir = next(p for p in func_path.parents if p.name.startswith("sub-"))
        except StopIteration:
            continue
        raw_subject = subj_dir.name
        norm_subject = normalize_subject_id(raw_subject)
        funcs_by_subject.setdefault(norm_subject, []).append(func_path)

    for subject_id, files in funcs_by_subject.items():
        funcs_by_subject[subject_id] = sorted(files)
    return funcs_by_subject


def collect_flywheel_frac2b_logs(subjects_root: Path) -> Dict[str, List[Path]]:
    """Collect frac2B log files from Flywheel SUBJECTS directory.

    Returns mapping of normalized subject id -> list of log files (sorted).
    """
    logs_by_subject: Dict[str, List[Path]] = {}
    if not subjects_root.exists():
        return logs_by_subject

    for subj_dir in sorted([p for p in subjects_root.iterdir() if p.is_dir()]):
        raw_subject = subj_dir.name
        norm_subject = normalize_subject_id(raw_subject)
        matches: List[Path] = []
        for pattern in ("**/*frac2B*.log", "**/*frac2b*.log"):
            matches.extend(subj_dir.glob(pattern))
        unique_sorted = sorted({p for p in matches if p.is_file()})
        if unique_sorted:
            logs_by_subject[norm_subject] = unique_sorted
    return logs_by_subject


def extract_bblid_scanid(log_path: Path) -> Optional[Tuple[str, str]]:
    """
    Attempt to extract (bblid, scanid) from the parent directory name or file name.
    Expected parent dir like: <logs-dir>/bblid_scanid/
    Falls back to parsing the file stem if needed.
    """
    parent_name = log_path.parent.name
    if "_" in parent_name:
        parts = parent_name.split("_")
        if len(parts) >= 2 and parts[0] and parts[1]:
            return parts[0], parts[1]

    # Fallback: parse from file name like bblid_scanid-*.log
    stem = log_path.stem
    if "-" in stem and "_" in stem:
        prefix = stem.split("-")[0]
        parts = prefix.split("_")
        if len(parts) >= 2 and parts[0] and parts[1]:
            return parts[0], parts[1]

    return None


# ------------------------------ XML Processing -------------------------------


def load_score_labels(xml_path: Path) -> List[ET.Element]:
    """
    Load the XML and return the list of stimulus/scoring elements used by the
    original notebook (root[5]).

    We preserve the same indexing approach for compatibility. If the structure
    doesn't match, we raise a clear error to help the user point to the correct
    XML.
    """
    root = ET.parse(str(xml_path)).getroot()
    try:
        stim = root[5]
    except Exception as exc:
        raise RuntimeError(
            "XML structure not as expected; could not access root[5]. "
            "Please provide the XML file used for EF task scoring."
        ) from exc

    scorelabel: List[ET.Element] = []
    for s in stim:
        scorelabel.append(s)
    return scorelabel


def split_templates_by_category(
    scorelabel: List[ET.Element],
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Return (back0, back1, back2) lists of (expected, index) tuples by category."""
    back0: List[Tuple[str, str]] = []
    back1: List[Tuple[str, str]] = []
    back2: List[Tuple[str, str]] = []
    for elem in scorelabel:
        category = elem.get("category")
        if category == "0BACK":
            back0.append((elem.get("expected"), elem.get("index")))
        elif category == "1BACK":
            back1.append((elem.get("expected"), elem.get("index")))
        elif category == "2BACK":
            back2.append((elem.get("expected"), elem.get("index")))
    return back0, back1, back2


# ------------------------------ Data Processing ------------------------------


def read_log_as_dataframe(log_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        log_path,
        skiprows=4,
        sep="\t",
        header=None,
        dtype=str,  # read as strings first; we'll cast selectively
        engine="python",
        encoding_errors="ignore",
    )
    df.columns = [
        "Subject",
        "Trial",
        "EventType",
        "Code",
        "Time",
        "TTime",
        "Uncertainty0",
        "Duration",
        "Uncertainty1",
        "ReqTime",
        "ReqDur",
        "StimType",
        "PairIndex",
    ]
    df = df[2:]
    numeric_cols = [
        "Trial",
        "Time",
        "TTime",
        "Duration",
        "ReqTime",
        "Uncertainty0",
        "Uncertainty1",
        "PairIndex",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def compute_response_times(
    df: pd.DataFrame, template: List[Tuple[str, str]], label: str
) -> List[List[object]]:
    """
    Reproduce the response time extraction logic from the notebook for a given
    template (either 0BACK or 2BACK).
    Returns rows: [label, index, expected, response]
    """
    rows: List[List[object]] = []
    for expected, index_str in template:
        if index_str is None:
            continue
        index_val = int(index_str)
        a1 = df[df["Trial"] >= (index_val - 2)]
        a2 = df[df["Trial"] <= index_val]
        merged = pd.merge(a1, a2, how="inner")
        aa = np.array(merged["TTime"].to_list())

        if len(aa) > 6:
            if aa[0] > 0:
                response = aa[0] / 10
            else:
                # first non-zero among even indices
                # enumerate(aa[::2]) returns (i, value) pairs
                res = next((i for i, j in enumerate(aa[::2]) if j), None)
                if res is None:
                    response = None
                else:
                    ste = res - 1
                    centr = 2 * res - 1
                    response = aa[centr] / 10 + ste * 800
        else:
            response = None

        rows.append([label, index_val, expected, response])
    return rows


def build_events_dataframe(allback: List[List[object]]) -> pd.DataFrame:
    df = pd.DataFrame(allback, columns=["task", "index", "results", "response_time_ms"])
    df["index"] = df["index"].astype(int)
    df["onset"] = 0.8 * df["index"]
    df["duration"] = 3 * 0.8
    df["onset"] = df["onset"].round(1)
    df["duration"] = df["duration"].round(1)
    df["response_time_ms"] = pd.to_numeric(df["response_time_ms"], errors="coerce")
    df["response_time"] = df["response_time_ms"] / 1000.0
    df = df.drop(columns=["index", "response_time_ms"]).rename(
        columns={"task": "trial_type"}
    )

    # Scoring
    scores: List[str] = []
    for row in df.itertuples(index=False):
        # row: trial_type, results, onset, duration, response_time
        result = row.results
        rt_sec = row.response_time
        if "NR" in result and not pd.isna(rt_sec):
            scores.append("false_positive")
        elif "NR" in result and pd.isna(rt_sec):
            scores.append("true_negative")
        elif "Match" in result and (not pd.isna(rt_sec) and rt_sec <= 2.4):
            scores.append("true_positive")
        elif "Match" in result and (pd.isna(rt_sec) or rt_sec > 2.4):
            scores.append("false_negative")
        else:
            scores.append("unknown")
    df["score"] = scores

    # Column order: onset, duration first
    first_cols = ["onset", "duration"]
    other_cols = [c for c in df.columns if c not in first_cols]
    df = df[first_cols + other_cols]
    return df


def sidecar_json() -> Dict[str, object]:
    return {
        "trial_type": {
            "Description": "Task condition for each trial",
            "Levels": {
                "0BACK": "0-back trial: respond to target picture",
                "1BACK": "1-back trial: respond if picture matches the one shown one trial before",
                "2BACK": "2-back trial: respond if picture matches the one shown two trials before",
            },
        },
        "results": {
            "Description": "Expected outcome for each trial based on task rules",
            "Levels": {
                "NR": "No response expected",
                "Match": "Response expected",
            },
        },
        "score": {
            "Description": "Trial outcome classification",
            "Levels": {
                "false_positive": "No response expected, response detected",
                "true_negative": "No response expected, no response detected",
                "true_positive": "Response expected, response detected",
                "false_negative": "Response expected, no response detected",
            },
        },
    }


# ------------------------------ Summary Metrics ------------------------------


Z = norm.ppf


def dprime(hits: int, misses: int, fas: int, crs: int) -> float:
    """Compute d' replicating notebook behavior (with half-hit/FA corrections)."""
    half_hit = 0.5 / max(hits + misses, 1)
    half_fa = 0.5 / max(fas + crs, 1)

    hit_rate = hits / max(hits + misses, 1)
    if hit_rate == 1:
        hit_rate = 1 - half_hit
    if hit_rate == 0:
        hit_rate = half_hit

    fa_rate = fas / max(fas + crs, 1)
    if fa_rate == 1:
        fa_rate = 1 - half_fa
    if fa_rate == 0:
        fa_rate = half_fa

    return float(Z(hit_rate) - Z(fa_rate))


def summarize_subject(subject_display: str, df: pd.DataFrame) -> Dict[str, object]:
    metrics: Dict[str, object] = {}

    def condition_counts(
        condition: Optional[str] = None,
    ) -> Tuple[int, int, int, int, int, int]:
        sub = df if condition is None else df[df["trial_type"] == condition]
        tp = int((sub["score"] == "true_positive").sum())
        tn = int((sub["score"] == "true_negative").sum())
        fp = int((sub["score"] == "false_positive").sum())
        fn = int((sub["score"] == "false_negative").sum())
        num_targets = int((sub["results"] == "Match").sum())
        num_foils = int((sub["results"] == "NR").sum())
        return tp, tn, fp, fn, num_targets, num_foils

    for label_key, cond in (
        ("0_back", "0BACK"),
        ("1_back", "1BACK"),
        ("2_back", "2BACK"),
    ):
        tp, tn, fp, fn, num_targets, num_foils = condition_counts(cond)
        metrics.update(
            {
                f"{label_key}_true_positive": tp,
                f"{label_key}_true_negative": tn,
                f"{label_key}_false_positive": fp,
                f"{label_key}_false_negative": fn,
                f"{label_key}_all_correct": tp + tn,
                f"{label_key}_all_incorrect": fp + fn,
                f"{label_key}_hit_rate": (tp / num_targets) if num_targets > 0 else 0.0,
                f"{label_key}_false_alarm_rate": (fp / num_foils)
                if num_foils > 0
                else 0.0,
                f"{label_key}_dprime": dprime(tp, fn, fp, tn),
            }
        )

    # All-back aggregated across 0/1/2
    tp, tn, fp, fn, num_targets, num_foils = condition_counts(None)
    metrics.update(
        {
            "all_back_true_positive": tp,
            "all_back_true_negative": tn,
            "all_back_false_positive": fp,
            "all_back_false_negative": fn,
            "all_back_all_correct": tp + tn,
            "all_back_all_incorrect": fp + fn,
            "all_back_hit_rate": (tp / num_targets) if num_targets > 0 else 0.0,
            "all_back_false_alarm_rate": (fp / num_foils) if num_foils > 0 else 0.0,
            "all_back_dprime": dprime(tp, fn, fp, tn),
        }
    )

    return metrics


# ------------------------------ FW sessions -> BIDS ---------------------------


def events_paths_from_func_nii(func_nii: Path) -> Tuple[Path, Path]:
    """Given a BIDS BOLD NIfTI, return the events tsv/json paths with the same prefix."""
    name = func_nii.name
    if name.endswith("_bold.nii.gz"):
        name = name[: -len("_bold.nii.gz")]
    prefix_dir = func_nii.parent
    tsv = prefix_dir / f"{name}_events.tsv"
    js = prefix_dir / f"{name}_events.json"
    return tsv, js


def update_participants_tsv(
    bids_root: Path, participant_id: str, metrics: Dict[str, object]
) -> None:
    """Update participants.tsv at the BIDS root with the provided metrics.

    - Ensures a row for the given participant_id exists (creates file if needed).
    - Adds missing columns and writes values.
    """
    participants_path = bids_root / "participants.tsv"
    if participants_path.exists():
        df = pd.read_csv(participants_path, sep="\t")
    else:
        df = pd.DataFrame({"participant_id": [participant_id]})

    if "participant_id" not in df.columns:
        df.insert(0, "participant_id", pd.Series(dtype=str))

    if not (df["participant_id"] == participant_id).any():
        new_row = {
            col: (participant_id if col == "participant_id" else pd.NA)
            for col in df.columns
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Filter out id-like keys
    metrics = {k: v for k, v in metrics.items() if k not in {"bblid", "subject"}}

    for key in metrics.keys():
        if key not in df.columns:
            df[key] = pd.NA

    row_idx = df.index[df["participant_id"] == participant_id]
    for key, value in metrics.items():
        df.loc[row_idx, key] = value

    first_cols = [c for c in ["participant_id"] if c in df.columns]
    other_cols = [c for c in df.columns if c not in first_cols]
    df = df[first_cols + other_cols]

    df.to_csv(participants_path, sep="\t", index=False, na_rep="n/a")


# ----------------------------------- Main ------------------------------------


def main() -> int:
    args = parse_args()
    xml_path: Path = args.xml
    logs_dir: Path = args.logs_dir
    bids_root: Path = args.output_dir

    # Load XML scoring template
    scorelabel = load_score_labels(xml_path)
    back0, back1, back2 = split_templates_by_category(scorelabel)

    # Collect funcs and logs
    funcs_by_subject = collect_bids_fracback_funcs(bids_root)
    logs_by_subject = collect_flywheel_frac2b_logs(logs_dir)

    if not funcs_by_subject:
        print(f"No fracback funcs found under {bids_root}")
        return 1

    # Iterate subjects found in BIDS (single-session dataset: ses-1)
    for norm_subject, func_list in sorted(funcs_by_subject.items()):
        subject_display = f"sub-{norm_subject}"
        picked_func = func_list[0] if func_list else None
        log_list = logs_by_subject.get(norm_subject, [])
        if not log_list:
            print(f"Skip {subject_display}: no frac2B log in {logs_dir}")
            continue
        if len(log_list) > 1:
            print(
                f"Info {subject_display}: multiple logs found; using first: {log_list[0].name}"
            )
        log_path = log_list[0]

        try:
            bb = read_log_as_dataframe(log_path)

            allback: List[List[object]] = []
            if back0:
                allback.extend(compute_response_times(bb, back0, "0BACK"))
            if back1:
                allback.extend(compute_response_times(bb, back1, "1BACK"))
            if back2:
                allback.extend(compute_response_times(bb, back2, "2BACK"))

            events_df = build_events_dataframe(allback)

            if picked_func is None:
                print(f"Skip {subject_display}: no fracback func file found")
                continue
            tsv_path, json_path = events_paths_from_func_nii(picked_func)

            # Per-subject summary metrics
            subject_metrics = summarize_subject(subject_display, events_df)

            if args.dry_run:
                report_item = {
                    "subject": subject_display,
                    "func": str(picked_func),
                    "log": str(log_path),
                    "events_tsv": str(tsv_path),
                    "events_json": str(json_path),
                    "num_events": int(len(events_df)),
                    "metrics": subject_metrics,
                }
                print(json.dumps(report_item))
            else:
                events_df.to_csv(tsv_path, sep="\t", index=False, na_rep="n/a")
                with open(json_path, "w") as fp:
                    json.dump(sidecar_json(), fp, indent=2)
                update_participants_tsv(bids_root, subject_display, subject_metrics)
                print(f"Processed {subject_display} from {log_path.name}")

        except Exception as exc:
            print(f"Error processing {subject_display} {log_path}: {exc}")
            continue

    return 0


if __name__ == "__main__":
    sys.exit(main())
