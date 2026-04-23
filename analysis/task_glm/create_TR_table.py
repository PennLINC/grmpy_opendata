#!/usr/bin/env python3
"""
Compute number of TRs occupied by each modeled condition and by implicit baseline.

Best source:
- events.tsv for modeled events
- actual BOLD image + JSON for run length and TR

Outputs a TSV table with one row per run and columns for:
- durations in seconds
- durations in TRs
"""

from pathlib import Path
import json

import nibabel as nib
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# EDIT THESE PATHS
# ---------------------------------------------------------------------

bids_root = Path("/cbica/projects/grmpy/data/bids_datalad")
deriv_root = Path(
    "/cbica/projects/grmpy/data/derivatives/fmriprep_func_full/fmriprep_func"
)

task_label = "fracback"
space_label = "MNI152NLin6Asym"

# Optional: restrict to one subject, e.g. "20238"
subject_filter = 102041  # or None

output_tsv = Path(
    "/cbica/projects/grmpy/code/analysis/task_glm/fracback_condition_tr_counts.tsv"
)


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def extract_bids_prefix(events_path: Path) -> str:
    name = events_path.name
    if not name.endswith("_events.tsv"):
        raise ValueError(f"Unexpected events filename: {name}")
    return name[:-11]  # remove "_events.tsv"


def normalize_trial_type(x: str) -> str:
    if pd.isna(x):
        return "unknown"
    x = str(x).strip()
    mapping = {
        "0BACK": "zero_back",
        "1BACK": "one_back",
        "2BACK": "two_back",
        "INST: "instruction",
        "zero_back": "zero_back",
        "one_back": "one_back",
        "two_back": "two_back",
        "instruction": "instruction",
    }
    return mapping.get(x, x)


def seconds_to_trs(seconds: float, tr: float) -> float:
    return seconds / tr


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

rows = []

events_paths = sorted(
    bids_root.glob(f"sub-*/ses-*/func/*task-{task_label}*_events.tsv")
)

if subject_filter is not None:
    events_paths = [p for p in events_paths if f"sub-{subject_filter}" in str(p)]

for events_path in events_paths:
    prefix = extract_bids_prefix(events_path)

    # Find matching BOLD json in raw BIDS
    bold_json = events_path.parent / f"{prefix}_bold.json"

    # --- FIXED: allow extra entities like _res-2 ---
    deriv_pattern = (
        f"{events_path.parts[-4]}/{events_path.parts[-3]}/func/"
        f"{prefix}_space-{space_label}*_desc-preproc_bold.nii.gz"
    )

    bold_candidates = sorted(deriv_root.glob(deriv_pattern))

    print(f"\nProcessing: {events_path}")
    print("Looking for:", deriv_root / deriv_pattern)
    print("Found:", bold_candidates)

    if not bold_json.exists():
        print(f"Skipping {events_path}: missing bold JSON {bold_json}")
        continue

    if len(bold_candidates) == 0:
        print(f"Skipping {events_path}: no matching preproc bold image found")
        continue

    bold_img_path = bold_candidates[0]

    # Load events
    events = pd.read_csv(events_path, sep="\t")
    if (
        "trial_type" not in events.columns
        or "onset" not in events.columns
        or "duration" not in events.columns
    ):
        print(f"Skipping {events_path}: missing required columns")
        continue

    events["trial_type"] = events["trial_type"].map(normalize_trial_type)
    events["onset"] = pd.to_numeric(events["onset"], errors="coerce")
    events["duration"] = pd.to_numeric(events["duration"], errors="coerce")
    events = events.dropna(subset=["onset", "duration"])

    # Load TR
    with open(bold_json, "r") as f:
        meta = json.load(f)
    tr = float(meta["RepetitionTime"])

    # Load n_scans from NIfTI
    img = nib.load(str(bold_img_path))
    n_scans = img.shape[3]
    total_run_sec = n_scans * tr

    # Sum modeled durations by condition
    dur_zero = events.loc[events["trial_type"] == "zero_back", "duration"].sum()
    dur_two = events.loc[events["trial_type"] == "two_back", "duration"].sum()
    dur_instr = events.loc[events["trial_type"] == "instruction", "duration"].sum()

    modeled_sec = dur_zero + dur_two + dur_instr
    implicit_baseline_sec = total_run_sec - modeled_sec

    # Guard against tiny negative values from rounding
    if implicit_baseline_sec < 0 and abs(implicit_baseline_sec) < 1e-6:
        implicit_baseline_sec = 0.0

    row = {
        "subject": events_path.parts[-4],
        "session": events_path.parts[-3],
        "run_prefix": prefix,
        "tr_sec": tr,
        "n_scans": n_scans,
        "total_run_sec": total_run_sec,
        "zero_back_sec": dur_zero,
        "two_back_sec": dur_two,
        "instruction_sec": dur_instr,
        "implicit_baseline_sec": implicit_baseline_sec,
        "zero_back_trs": seconds_to_trs(dur_zero, tr),
        "two_back_trs": seconds_to_trs(dur_two, tr),
        "instruction_trs": seconds_to_trs(dur_instr, tr),
        "implicit_baseline_trs": seconds_to_trs(implicit_baseline_sec, tr),
    }
    rows.append(row)

summary_df = pd.DataFrame(rows)

if len(summary_df) == 0:
    raise RuntimeError("No runs processed. Check your paths and filenames.")

# Optional prettier rounding
for col in summary_df.columns:
    if col.endswith("_sec") or col.endswith("_trs") or col == "tr_sec":
        summary_df[col] = summary_df[col].round(3)

summary_df.to_csv(output_tsv, sep="\t", index=False)
print(f"\nWrote {output_tsv}")
print(summary_df.head())
