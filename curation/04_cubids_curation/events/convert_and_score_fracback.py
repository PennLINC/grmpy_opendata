#!/usr/bin/env python3
"""
Convert EF fractal n-back logs to BIDS-compliant events and update sessions.tsv.

What it does:
- Discovers EF logs under Flywheel-style trees:
  <bblid>/SESSIONS/<scanid>/ACQUISITIONS/*/FILES/*-frac2B_1.00_no1B.log
- Maps each <scanid> to BIDS session labels ses-1/2/3 by reading the session_map.tsv file
- For each subject/session, finds an existing functional BIDS sidecar at
  --output-dir/sub-<bblid>/<ses-X>/func/*task-nback*bold.json. If multiple
  runs exist, chooses the highest run (e.g., run-02 over run-01). If none,
  the session is skipped.
- Writes BIDS events alongside that sidecar, with lower-case columns and order:
  onset, duration, trial_type, results, response_time, score.
- Writes per-session performance metrics (including d-prime) into the subject's
  sessions.tsv at --output-dir/sub-<bblid>/sub-<bblid>_sessions.tsv (lower-case
  column names). It creates the file or row if missing.

CLI inputs:
- --xml: Path to EF task XML template used for scoring
- --logs-dir: Root directory containing the Flywheel-style trees
- --output-dir: BIDS output root (defaults to <logs-dir>/bids_out)
- --session-map: Path to session_map.tsv file
- --dry-run: Print planned actions as JSON and make no file changes

Note: This script assumes that the session_map.tsv file has been generated using the generate_session_map.py script.

Example executed:
python /cbica/projects/executive_function/code/curation/cubids_curation/convert_and_score_EF_task_data.py \
  --xml /cbica/projects/executive_function/task_events_files/msmri522_2vs0_back.xml \
  --logs-dir /cbica/projects/executive_function/task_events_files/flywheel/EFR01/SUBJECTS \
  --output-dir /cbica/projects/executive_function/data/bids/EF_bids_data_DataLad \
  --session-map /cbica/projects/executive_function/task_events_files/session_map.tsv
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from scipy.stats import norm


# ------------------------------ CLI & Utilities ------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Convert EF fractal n-back .log files to BIDS events and summary.")
    )
    parser.add_argument(
        "--xml",
        required=True,
        type=Path,
        help="Path to EF task XML template used for scoring",
    )
    parser.add_argument(
        "--logs-dir",
        required=True,
        type=Path,
        help="Directory containing subject folders with .log files (searched recursively)",
    )
    parser.add_argument(
        "--output-dir",
        required=False,
        type=Path,
        default=None,
        help="Directory to write outputs (defaults to <logs-dir>/bids_out)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write any files; print a JSON report of intended actions",
    )
    parser.add_argument(
        "--session-map",
        required=True,
        type=Path,
        help="Optional TSV with columns bblid, scanid, session_id to override internal mapping",
    )
    return parser.parse_args()


def discover_log_files(logs_dir: Path) -> List[Path]:
    return sorted([p for p in logs_dir.rglob("*.log") if p.is_file()])


def discover_logs_flywheel(logs_dir: Path) -> Dict[Tuple[str, str], List[Path]]:
    """
    Discover logs using the Flywheel tree pattern:
      <bblid>/SESSIONS/<scanid>/ACQUISITIONS/*/FILES/*-frac2B_1.00_no1B.log

    Returns mapping (bblid, scanid) -> list of log paths.
    """
    mapping: Dict[Tuple[str, str], List[Path]] = {}
    for log_path in logs_dir.rglob("*-frac2B_1.00_no1B.log"):
        parts = log_path.parts
        if "SESSIONS" not in parts:
            continue
        idx = parts.index("SESSIONS")
        if idx - 1 < 0 or idx + 1 >= len(parts):
            continue
        bblid = parts[idx - 1]
        scanid = parts[idx + 1]
        if not bblid or not scanid:
            continue
        mapping.setdefault((bblid, scanid), []).append(log_path)
    return mapping


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
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    Returns (back0, back2) where each is a list of tuples (expected, index).
    """
    back0: List[Tuple[str, str]] = []
    back2: List[Tuple[str, str]] = []
    for elem in scorelabel:
        category = elem.get("category")
        if category == "0BACK":
            back0.append((elem.get("expected"), elem.get("index")))
        elif category == "2BACK":
            back2.append((elem.get("expected"), elem.get("index")))
    return back0, back2


# ------------------------------ Data Processing ------------------------------


def read_log_as_dataframe(log_path: Path) -> pd.DataFrame:
    df = pd.read_csv(
        log_path,
        skiprows=3,
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


def summarize_subject(bblid: str, df: pd.DataFrame) -> Dict[str, object]:
    back0fp = back0fn = back0tp = back0tn = 0
    back2fp = back2fn = back2tp = back2tn = 0

    for row in df.itertuples(index=False):
        trial = row.trial_type
        score = row.score
        if trial == "0BACK":
            if score == "false_positive":
                back0fp += 1
            elif score == "false_negative":
                back0fn += 1
            elif score == "true_positive":
                back0tp += 1
            elif score == "true_negative":
                back0tn += 1
        elif trial == "2BACK":
            if score == "false_positive":
                back2fp += 1
            elif score == "false_negative":
                back2fn += 1
            elif score == "true_positive":
                back2tp += 1
            elif score == "true_negative":
                back2tn += 1

    summary: Dict[str, object] = {
        "0_back_false_positive": back0fp,
        "0_back_false_negative": back0fn,
        "0_back_true_positive": back0tp,
        "0_back_true_negative": back0tn,
        "2_back_false_positive": back2fp,
        "2_back_false_negative": back2fn,
        "2_back_true_positive": back2tp,
        "2_back_true_negative": back2tn,
    }

    summary.update(
        {
            "all_back_true_positive": back0tp + back2tp,
            "all_back_true_negative": back0tn + back2tn,
            "all_back_false_positive": back0fp + back2fp,
            "all_back_false_negative": back0fn + back2fn,
            "0_back_all_correct": back0tp + back0tn,
            "0_back_all_incorrect": back0fp + back0fn,
            "2_back_all_correct": back2tp + back2tn,
            "2_back_all_incorrect": back2fp + back2fn,
            "all_back_all_correct": back2tp + back2tn + back0tp + back0tn,
            "all_back_all_incorrect": back0fp + back0fn + back2fp + back2fn,
        }
    )

    # Based on notebook constants: 0BACK has 15 targets and 45 foils, same for 2BACK
    summary.update(
        {
            "0_back_hit_rate": (back0tp / 15) if 15 else 0.0,
            "0_back_false_alarm_rate": (back0fp / 45) if 45 else 0.0,
            "2_back_hit_rate": (back2tp / 15) if 15 else 0.0,
            "2_back_false_alarm_rate": (back2fp / 45) if 45 else 0.0,
            "all_back_hit_rate": ((back0tp + back2tp) / 30) if 30 else 0.0,
            "all_back_false_alarm_rate": ((back0fp + back2fp) / 90) if 90 else 0.0,
        }
    )

    summary.update(
        {
            "0_back_dprime": dprime(back0tp, back0fn, back0fp, back0tn),
            "2_back_dprime": dprime(back2tp, back2fn, back2fp, back2tn),
            "all_back_dprime": dprime(
                back0tp + back2tp,
                back0fn + back2fn,
                back0fp + back2fp,
                back0tn + back2tn,
            ),
        }
    )

    return summary


# ------------------------------ FW sessions -> BIDS ---------------------------


_RUN_RE = re.compile(r"run-(\d+)")


def choose_highest_run_sidecar(func_dir: Path) -> Optional[Path]:
    """
    Pick the bold sidecar JSON with highest run number among *task-nback*bold.json.
    If no run- is present, treat as run-1. Returns None if none found.
    """
    candidates = sorted(func_dir.glob("*task-nback*bold.json"))
    if not candidates:
        return None

    def run_number(p: Path) -> int:
        m = _RUN_RE.search(p.name)
        return int(m.group(1)) if m else 1

    candidates.sort(key=lambda p: (run_number(p), p.name))
    return candidates[-1]


def events_paths_from_bold_sidecar(bold_json: Path) -> Tuple[Path, Path]:
    """
    Given a BIDS bold sidecar JSON, return the events tsv/json paths with the
    same prefix in the same directory.
    """
    prefix = bold_json.with_suffix("")
    name = prefix.name[:-5] if prefix.name.endswith("_bold") else prefix.name
    tsv = prefix.parent / f"{name}_events.tsv"
    js = prefix.parent / f"{name}_events.json"
    return tsv, js


# ------------------------------ Sessions.tsv Writing --------------------------


def update_sessions_tsv(
    output_dir: Path, bblid: str, ses_label: str, metrics: Dict[str, object]
) -> None:
    """
    Write the per-session summary metrics into the subject's sessions.tsv.
    - sessions.tsv path: <output_dir>/sub-<bblid>/sub-<bblid>_sessions.tsv
    - Ensures a row for the given ses_label exists; adds missing columns.
    """
    subj_dir = output_dir / f"sub-{bblid}"
    subj_dir.mkdir(parents=True, exist_ok=True)
    sessions_path = subj_dir / f"sub-{bblid}_sessions.tsv"

    # Load or initialize sessions dataframe
    if sessions_path.exists():
        df = pd.read_csv(sessions_path, sep="\t")
    else:
        df = pd.DataFrame({"session_id": [ses_label]})

    # Ensure target session row exists
    if "session_id" not in df.columns:
        df.insert(0, "session_id", pd.Series(dtype=str))
    if not (df["session_id"] == ses_label).any():
        # Append a new row with session_id set; keep other columns as NaN
        new_row = {
            col: (ses_label if col == "session_id" else pd.NA) for col in df.columns
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Prepare metrics (exclude any id keys if present)
    metrics = {k: v for k, v in metrics.items() if k not in {"bblid", "subject"}}

    # Add any missing columns
    for key in metrics.keys():
        if key not in df.columns:
            df[key] = pd.NA

    # Update values for the session row
    row_idx = df.index[df["session_id"] == ses_label]
    for key, value in metrics.items():
        df.loc[row_idx, key] = value

    # Keep 'session_id' and 'acq_time' as the first columns if present
    first_cols = [c for c in ["session_id", "acq_time"] if c in df.columns]
    other_cols = [c for c in df.columns if c not in first_cols]
    df = df[first_cols + other_cols]

    # Write back (BIDS missing values as 'n/a')
    df.to_csv(sessions_path, sep="\t", index=False, na_rep="n/a")

    # Create or update sessions.json sidecar with clear metric descriptions
    sessions_json = subj_dir / f"sub-{bblid}_sessions.json"
    if sessions_json.exists():
        try:
            with open(sessions_json, "r") as fp:
                sidecar = json.load(fp)
        except Exception:
            sidecar = {}
    else:
        sidecar = {}

    # Ensure base fields
    sidecar.setdefault(
        "session_id",
        {
            "Description": "BIDS session label assigned chronologically via Flywheel created timestamp",
        },
    )
    sidecar.setdefault(
        "acq_time",
        {
            "Description": "Acquisition time for the session rounded to the nearest hour and half-month period for anonymization",
        },
    )

    def pretty_block_label(prefix: str) -> str:
        return {
            "0_back": "0-back",
            "2_back": "2-back",
            "all_back": "0- and 2-back",
        }.get(prefix, prefix.replace("_", "-"))

    # Add/refresh metric entries with descriptions and units
    for key in metrics.keys():
        desc: str
        units: str
        if key.endswith("_dprime"):
            prefix = key[: key.rfind("_dprime")]
            desc = (
                f"d' sensitivity index for {pretty_block_label(prefix)} (Z(H) - Z(FA))"
            )
            units = "arbitrary"
        elif key.endswith("_hit_rate"):
            prefix = key[: key.rfind("_hit_rate")]
            desc = (
                f"Hit rate in {pretty_block_label(prefix)} (true positives / targets)"
            )
            units = "proportion (0-1)"
        elif key.endswith("_false_alarm_rate"):
            prefix = key[: key.rfind("_false_alarm_rate")]
            desc = f"False alarm rate in {pretty_block_label(prefix)} (false positives / foils)"
            units = "proportion (0-1)"
        elif key.endswith("_true_positive"):
            prefix = key[: key.rfind("_true_positive")]
            desc = f"True positives in {pretty_block_label(prefix)}"
            units = "count"
        elif key.endswith("_true_negative"):
            prefix = key[: key.rfind("_true_negative")]
            desc = f"True negatives in {pretty_block_label(prefix)}"
            units = "count"
        elif key.endswith("_false_positive"):
            prefix = key[: key.rfind("_false_positive")]
            desc = f"False positives in {pretty_block_label(prefix)}"
            units = "count"
        elif key.endswith("_false_negative"):
            prefix = key[: key.rfind("_false_negative")]
            desc = f"False negatives in {pretty_block_label(prefix)}"
            units = "count"
        elif key.endswith("_all_correct"):
            prefix = key[: key.rfind("_all_correct")]
            desc = f"All correct responses in {pretty_block_label(prefix)} (true positives + true negatives)"
            units = "count"
        elif key.endswith("_all_incorrect"):
            prefix = key[: key.rfind("_all_incorrect")]
            desc = f"All incorrect responses in {pretty_block_label(prefix)} (false positives + false negatives)"
            units = "count"
        else:
            desc = f"Metric {key.replace('_', ' ')}"
            units = ""
        sidecar[key] = {"Description": desc, **({"Units": units} if units else {})}

    with open(sessions_json, "w") as fp:
        json.dump(sidecar, fp, indent=2)


# ----------------------------------- Main ------------------------------------


def main() -> int:
    args = parse_args()
    xml_path: Path = args.xml
    logs_dir: Path = args.logs_dir
    output_dir: Path = args.output_dir or (logs_dir / "bids_out")
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Load XML scoring template
    scorelabel = load_score_labels(xml_path)
    back0, back2 = split_templates_by_category(scorelabel)

    logs_map = discover_logs_flywheel(logs_dir)
    if not logs_map:
        print(f"No .log files found under {logs_dir} with Flywheel pattern")
        return 1

    # error if session map file does not exist
    if not args.session_map.exists():
        raise ValueError("Session map file does not exist")

    # Build session mapping from provided TSV
    ses_map: Dict[Tuple[str, str], str]
    df_map = pd.read_csv(args.session_map, sep="\t")
    ses_map = {
        (str(r.bblid), str(r.scanid)): str(r.session_id)
        for r in df_map.itertuples(index=False)
    }

    for (bblid, scanid), log_list in sorted(logs_map.items()):
        ses_label = ses_map.get((bblid, scanid))
        if not ses_label:
            continue

        # Check BIDS func presence under output-dir and choose bold sidecar
        func_dir = output_dir / f"sub-{bblid}" / ses_label / "func"
        bold_sidecar = choose_highest_run_sidecar(func_dir)
        if bold_sidecar is None:
            print(
                f"Skip sub-{bblid} {ses_label}: no *task-nback*bold.json in {func_dir}"
            )
            continue

        # Choose a single log file for this session: prefer latest mtime
        log_path = max(log_list, key=lambda p: p.stat().st_mtime)

        try:
            bb = read_log_as_dataframe(log_path)

            allback: List[List[object]] = []
            allback.extend(compute_response_times(bb, back0, "0BACK"))
            allback.extend(compute_response_times(bb, back2, "2BACK"))

            events_df = build_events_dataframe(allback)

            tsv_path, json_path = events_paths_from_bold_sidecar(bold_sidecar)

            # Per-session summary metrics
            session_metrics = summarize_subject(bblid, events_df)

            if args.dry_run:
                report_item = {
                    "subject": f"sub-{bblid}",
                    "session": ses_label,
                    "log": str(log_path),
                    "bold_sidecar": str(bold_sidecar),
                    "events_tsv": str(tsv_path),
                    "events_json": str(json_path),
                    "num_events": int(len(events_df)),
                    "metrics": session_metrics,
                }
                print(json.dumps(report_item))
            else:
                events_df.to_csv(tsv_path, sep="\t", index=False, na_rep="n/a")
                with open(json_path, "w") as fp:
                    json.dump(sidecar_json(), fp, indent=2)
                update_sessions_tsv(output_dir, bblid, ses_label, session_metrics)
                print(f"Processed sub-{bblid} {ses_label} from {log_path.name}")

        except Exception as exc:
            print(f"Error processing {log_path}: {exc}")
            continue

    # No global summary CSV; metrics were written to sessions.tsv per subject or printed in dry-run

    return 0


if __name__ == "__main__":
    sys.exit(main())
