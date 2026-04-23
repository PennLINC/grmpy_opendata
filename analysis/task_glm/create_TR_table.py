#!/usr/bin/env python3
"""
Compute number of TRs occupied by each modeled condition and by implicit baseline.

Sources:
- events.tsv  → condition durations, TR
- BOLD sidecar JSON → TR
- preprocessed BOLD NIfTI → n_scans (and therefore total run duration)

Outputs a TSV with one row per run and columns for durations in seconds and TRs.
"""

from pathlib import Path
import json

import nibabel as nib
import pandas as pd


# ---------------------------------------------------------------------
# CONFIGURATION — edit these before running
# ---------------------------------------------------------------------

BIDS_ROOT = Path("/cbica/projects/grmpy/data/bids_datalad")
DERIV_ROOT = Path(
    "/cbica/projects/grmpy/data/derivatives/fmriprep_func_full/fmriprep_func"
)

TASK_LABEL = "fracback"
SPACE_LABEL = "MNI152NLin6Asym"

# Set to an integer subject ID to process only that subject, or None for all
SUBJECT_FILTER = 102041

OUTPUT_TSV = Path(
    "/cbica/projects/grmpy/code/analysis/task_glm/fracback_condition_tr_counts.tsv"
)

CONDITIONS = ["zero_back", "one_back", "two_back", "instruction"]

TRIAL_TYPE_MAP = {
    "0BACK": "zero_back",
    "1BACK": "one_back",
    "2BACK": "two_back",
    "INST":  "instruction",
}


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def bids_prefix(events_path: Path) -> str:
    name = events_path.name
    if not name.endswith("_events.tsv"):
        raise ValueError(f"Unexpected events filename: {name}")
    return name[: -len("_events.tsv")]


def normalize_trial_type(x) -> str:
    if pd.isna(x):
        return "unknown"
    x = str(x).strip()
    return TRIAL_TYPE_MAP.get(x, x)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

events_paths = sorted(
    BIDS_ROOT.glob(f"sub-*/ses-*/func/*task-{TASK_LABEL}*_events.tsv")
)

if SUBJECT_FILTER is not None:
    events_paths = [p for p in events_paths if f"sub-{SUBJECT_FILTER}" in str(p)]

rows = []

for events_path in events_paths:
    prefix = bids_prefix(events_path)
    print(f"\nProcessing: {events_path.name}")

    # Sidecar JSON for TR
    bold_json = events_path.parent / f"{prefix}_bold.json"
    if not bold_json.exists():
        print(f"  Skipping: missing sidecar JSON {bold_json.name}")
        continue

    # Preprocessed BOLD for n_scans (allow extra entities like _res-2)
    sub, ses = events_path.parts[-4], events_path.parts[-3]
    bold_candidates = sorted(
        DERIV_ROOT.glob(
            f"{sub}/{ses}/func/{prefix}_space-{SPACE_LABEL}*_desc-preproc_bold.nii.gz"
        )
    )
    if not bold_candidates:
        print("  Skipping: no preproc BOLD found")
        continue

    # Load events
    events = pd.read_csv(events_path, sep="\t")
    required = {"trial_type", "onset", "duration"}
    if not required.issubset(events.columns):
        print(f"  Skipping: missing columns {required - set(events.columns)}")
        continue

    events["trial_type"] = events["trial_type"].map(normalize_trial_type)
    events["onset"] = pd.to_numeric(events["onset"], errors="coerce")
    events["duration"] = pd.to_numeric(events["duration"], errors="coerce")
    events = events.dropna(subset=["onset", "duration"])

    # TR from sidecar JSON
    with open(bold_json) as f:
        tr = float(json.load(f)["RepetitionTime"])

    # n_scans from NIfTI header (avoids loading voxel data)
    n_scans = nib.load(str(bold_candidates[0])).shape[3]
    total_run_sec = n_scans * tr

    # Duration per condition
    cond_dur = {
        cond: events.loc[events["trial_type"] == cond, "duration"].sum()
        for cond in CONDITIONS
    }
    modeled_sec = sum(cond_dur.values())
    implicit_baseline_sec = max(total_run_sec - modeled_sec, 0.0)

    row = {
        "subject": sub,
        "session": ses,
        "run_prefix": prefix,
        "tr_sec": tr,
        "n_scans": n_scans,
        "total_run_sec": total_run_sec,
        **{f"{cond}_sec": cond_dur[cond] for cond in CONDITIONS},
        "implicit_baseline_sec": implicit_baseline_sec,
        **{f"{cond}_trs": cond_dur[cond] / tr for cond in CONDITIONS},
        "implicit_baseline_trs": implicit_baseline_sec / tr,
    }
    rows.append(row)

if not rows:
    raise RuntimeError("No runs processed. Check your paths and filenames.")

summary_df = pd.DataFrame(rows)

float_cols = [c for c in summary_df.columns if c.endswith(("_sec", "_trs", "tr_sec"))]
summary_df[float_cols] = summary_df[float_cols].round(3)

summary_df.to_csv(OUTPUT_TSV, sep="\t", index=False)
print(f"\nWrote {OUTPUT_TSV}")
print(summary_df.head())
