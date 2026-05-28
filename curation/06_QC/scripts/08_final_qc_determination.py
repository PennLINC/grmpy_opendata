#!/usr/bin/env python3
"""Create final modality-level QC CSVs and JSON sidecars for GRMPY."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


SCRIPT_PATH = Path(__file__).resolve()
QC_DIR = SCRIPT_PATH.parents[1]
DATA_DIR = QC_DIR / "data"
OUTPUT_DIR = DATA_DIR / "final_qc"

FMRI_MOTION_CSV = DATA_DIR / "xcpd_qc_median_fd.csv"
FMRI_COVERAGE_CSV = DATA_DIR / "xcpd_4S1056Parcels_qc_coverage_row_sums.csv"
DIFFUSION_QSIPREP_CSV = DATA_DIR / "qsiprep_qc.csv"
DIFFUSION_QSIRECON_CSV = DATA_DIR / "qsirecon_DSIStudio_row_sum_bundle_volume.csv"
ASL_CSV = DATA_DIR / "aslprep_qc.csv"
FREESURFER_CSV = DATA_DIR / "freesurfer-post_euler_qc.csv"
T1_RATINGS_CSV = DATA_DIR / "T1-ratings_consensus.csv"


def write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


def normalize_label(value: object, prefix: str) -> str:
    value_str = str(value).strip()
    if value_str.endswith(".0"):
        value_str = value_str[:-2]
    return value_str if value_str.startswith(prefix) else f"{prefix}{value_str}"


def normalize_participant(series: pd.Series) -> pd.Series:
    return series.map(lambda value: normalize_label(value, "sub-"))


def normalize_session(series: pd.Series) -> pd.Series:
    return series.map(lambda value: normalize_label(value, "ses-"))


def assert_unique(df: pd.DataFrame, subset: list[str], label: str) -> None:
    duplicate_rows = df[df.duplicated(subset=subset, keep=False)]
    if not duplicate_rows.empty:
        example = duplicate_rows[subset].head().to_dict(orient="records")
        raise ValueError(f"Found duplicate {label} rows for {subset}: {example}")


def sort_output(
    df: pd.DataFrame, extra_sort_cols: list[str] | None = None
) -> pd.DataFrame:
    sorted_df = df.copy()
    sorted_df["_participant_sort"] = pd.to_numeric(
        sorted_df["participant_id"].str.replace("sub-", "", regex=False),
        errors="coerce",
    ).fillna(10**9)
    sorted_df["_session_sort"] = pd.to_numeric(
        sorted_df["session_id"].str.replace("ses-", "", regex=False),
        errors="coerce",
    ).fillna(10**9)

    sort_cols = ["_participant_sort", "_session_sort"]
    if extra_sort_cols:
        sort_cols.extend(extra_sort_cols)

    sorted_df = sorted_df.sort_values(sort_cols).drop(
        columns=["_participant_sort", "_session_sort"]
    )
    return sorted_df.reset_index(drop=True)


def save_outputs(stem: str, df: pd.DataFrame, sidecar: dict[str, object]) -> None:
    df.to_csv(OUTPUT_DIR / f"{stem}_qc.csv", index=False)
    write_json(OUTPUT_DIR / f"{stem}_qc.json", sidecar)


def build_fmri_qc() -> tuple[pd.DataFrame, dict[str, object]]:
    motion_df = pd.read_csv(FMRI_MOTION_CSV)
    coverage_df = pd.read_csv(FMRI_COVERAGE_CSV)

    merge_cols = ["sub", "ses", "task", "acq"]
    assert_unique(motion_df, merge_cols, "fMRI motion")
    assert_unique(coverage_df, merge_cols, "fMRI coverage")

    metadata_cols = {"sub", "ses", "task", "acq", "space", "seg", "stat", "row_sum"}
    parcel_cols = [
        column for column in coverage_df.columns if column not in metadata_cols
    ]

    n_scans = len(coverage_df)
    low_coverage_counts = (coverage_df[parcel_cols] < 0.5).sum(axis=0)
    retained_parcels = low_coverage_counts[
        low_coverage_counts == n_scans
    ].index.tolist()

    retained_coverage_df = coverage_df[merge_cols].copy()
    retained_coverage_df["low_coverage_sum"] = (
        coverage_df[retained_parcels] < 0.5
    ).sum(axis=1)

    fmri_df = motion_df.merge(
        retained_coverage_df,
        on=merge_cols,
        how="inner",
        validate="one_to_one",
    )

    if len(fmri_df) != len(motion_df):
        raise ValueError("fMRI motion and coverage tables did not merge cleanly.")

    fmri_df["participant_id"] = normalize_participant(fmri_df["sub"])
    fmri_df["session_id"] = normalize_session(fmri_df["ses"])
    fmri_df["median_FD"] = fmri_df["framewise_displacement"]
    fmri_df["qc_determination"] = "pass"
    fmri_df.loc[
        (fmri_df["median_FD"] > 0.2) | (fmri_df["low_coverage_sum"] > 2),
        "qc_determination",
    ] = "fail"

    fmri_df = fmri_df[
        [
            "participant_id",
            "session_id",
            "task",
            "acq",
            "median_FD",
            "low_coverage_sum",
            "qc_determination",
        ]
    ]
    fmri_df = sort_output(fmri_df, extra_sort_cols=["task", "acq"])

    sidecar = {
        "participant_id": {
            "LongName": "Participant identifier",
            "Description": "The BIDS participant label for the scan.",
        },
        "session_id": {
            "LongName": "Session identifier",
            "Description": "The BIDS session label for the scan.",
        },
        "task": {
            "LongName": "Task",
            "Description": "The functional task label for the scan.",
            "Levels": {
                "face": "Face-processing task scan.",
                "fracback": "Fractal n-back task scan.",
                "rest": "Resting-state scan.",
            },
        },
        "acq": {
            "LongName": "Acquisition label",
            "Description": (
                "The BIDS acquisition label used to distinguish scans within the "
                "same task."
            ),
        },
        "median_FD": {
            "LongName": "Median framewise displacement",
            "Description": "Median framewise displacement across timepoints for the scan.",
        },
        "low_coverage_sum": {
            "LongName": "Count of retained parcels with less than 50% coverage",
            "Description": (
                "Number of parcels below 50% coverage after first removing parcels "
                f"that were low coverage in more than half of all {n_scans} scans."
            ),
        },
        "qc_determination": {
            "LongName": "Final fMRI QC determination",
            "Description": (
                "Final scan-level QC call for fMRI. A scan fails if median FD is "
                "greater than 0.2 mm and/or if more than 2 retained parcels have "
                "less than 50% coverage."
            ),
            "Levels": {
                "fail": "The scan fails QC and should be excluded from fMRI analyses.",
                "pass": "The scan passes QC and can be used in fMRI analyses.",
            },
        },
    }

    return fmri_df, sidecar


def build_diffusion_qc() -> tuple[pd.DataFrame, dict[str, object]]:
    qsiprep_df = pd.read_csv(DIFFUSION_QSIPREP_CSV)
    qsirecon_df = pd.read_csv(DIFFUSION_QSIRECON_CSV)

    assert_unique(qsiprep_df, ["sub", "ses"], "diffusion qsiprep")
    assert_unique(qsirecon_df, ["subject", "session"], "diffusion qsirecon")

    qsiprep_df = qsiprep_df.copy()
    qsirecon_df = qsirecon_df.copy()

    qsiprep_df["participant_id"] = normalize_participant(qsiprep_df["sub"])
    qsiprep_df["session_id"] = normalize_session(qsiprep_df["ses"])
    qsirecon_df["participant_id"] = normalize_participant(qsirecon_df["subject"])
    qsirecon_df["session_id"] = normalize_session(qsirecon_df["session"])

    diffusion_df = qsiprep_df.merge(
        qsirecon_df[
            [
                "participant_id",
                "session_id",
                "num_row_outliers",
                "num_missing_bundles",
            ]
        ],
        on=["participant_id", "session_id"],
        how="inner",
        validate="one_to_one",
    )

    if len(diffusion_df) != len(qsiprep_df):
        raise ValueError("Diffusion qsiprep and qsirecon tables did not merge cleanly.")

    diffusion_df["mean_FD"] = diffusion_df["mean_fd"]
    diffusion_df["raw_neighbor_corr"] = diffusion_df["raw_neighbor_corr"]
    diffusion_df["num_outlier_bundles"] = diffusion_df["num_row_outliers"].astype(int)
    diffusion_df["num_missing_bundles"] = diffusion_df["num_missing_bundles"].astype(
        int
    )
    diffusion_df["qc_determination_scalar_maps"] = "pass"
    diffusion_df.loc[
        (diffusion_df["mean_FD"] > 2.0) | (diffusion_df["raw_neighbor_corr"] < 0.8),
        "qc_determination_scalar_maps",
    ] = "fail"
    diffusion_df["qc_determination_bundles"] = "pass"
    diffusion_df.loc[
        diffusion_df["num_outlier_bundles"] > 6, "qc_determination_bundles"
    ] = "fail"

    diffusion_df = diffusion_df[
        [
            "participant_id",
            "session_id",
            "mean_FD",
            "raw_neighbor_corr",
            "num_outlier_bundles",
            "num_missing_bundles",
            "qc_determination_scalar_maps",
            "qc_determination_bundles",
        ]
    ]
    diffusion_df = sort_output(diffusion_df)

    sidecar = {
        "participant_id": {
            "LongName": "Participant identifier",
            "Description": "The BIDS participant label for the scan.",
        },
        "session_id": {
            "LongName": "Session identifier",
            "Description": "The BIDS session label for the scan.",
        },
        "mean_FD": {
            "LongName": "Mean framewise displacement",
            "Description": "Mean framewise displacement across diffusion volumes.",
        },
        "raw_neighbor_corr": {
            "LongName": "Raw neighboring DWI correlation",
            "Description": (
                "QSIPrep raw neighboring DWI correlation used to assess diffusion "
                "image quality."
            ),
        },
        "num_outlier_bundles": {
            "LongName": "Number of outlier bundles",
            "Description": (
                "Number of tract bundles flagged as outliers because the bundle "
                "volume was missing or more than 3 standard deviations from the "
                "cohort mean."
            ),
        },
        "num_missing_bundles": {
            "LongName": "Number of missing bundles",
            "Description": "Number of bundles missing completely for that scan.",
        },
        "qc_determination_scalar_maps": {
            "LongName": "Final diffusion QC determination for scalar maps",
            "Description": (
                "QC call based on QSIPrep summary metrics. A scan fails if mean FD "
                "is greater than 2.0 or raw neighboring DWI correlation is less "
                "than 0.8."
            ),
            "Levels": {
                "fail": "The scan fails scalar-map QC and should be excluded.",
                "pass": "The scan passes scalar-map QC.",
            },
        },
        "qc_determination_bundles": {
            "LongName": "Final diffusion QC determination for tract bundles",
            "Description": (
                "QC call based on QSIRecon bundle outliers. A scan fails if it has "
                "more than 6 outlier bundles."
            ),
            "Levels": {
                "fail": "The scan fails bundle QC and should be excluded.",
                "pass": "The scan passes bundle QC.",
            },
        },
    }

    return diffusion_df, sidecar


def build_asl_qc() -> tuple[pd.DataFrame, dict[str, object]]:
    asl_df = pd.read_csv(ASL_CSV)
    assert_unique(asl_df, ["sub", "ses"], "ASL")

    asl_df = asl_df.copy()
    asl_df["participant_id"] = normalize_participant(asl_df["sub"])
    asl_df["session_id"] = normalize_session(asl_df["ses"])
    asl_df["QEI"] = asl_df["qei_cbf"]
    asl_df["qc_determination"] = "pass"
    asl_df.loc[asl_df["QEI"] < 0.6, "qc_determination"] = "fail"

    asl_df = asl_df[["participant_id", "session_id", "QEI", "qc_determination"]]
    asl_df = sort_output(asl_df)

    sidecar = {
        "participant_id": {
            "LongName": "Participant identifier",
            "Description": "The BIDS participant label for the scan.",
        },
        "session_id": {
            "LongName": "Session identifier",
            "Description": "The BIDS session label for the scan.",
        },
        "QEI": {
            "LongName": "Quality evaluation index for cerebral blood flow",
            "Description": "ASLPrep quality evaluation index (QEI) for the CBF map.",
        },
        "qc_determination": {
            "LongName": "Final ASL QC determination",
            "Description": "Final ASL QC call. A scan fails if QEI is less than 0.6.",
            "Levels": {
                "fail": "The scan fails QC and should be excluded from ASL analyses.",
                "pass": "The scan passes QC and can be used in ASL analyses.",
            },
        },
    }

    return asl_df, sidecar


def build_t1_qc() -> tuple[pd.DataFrame, dict[str, object]]:
    ratings_df = pd.read_csv(T1_RATINGS_CSV)
    fs_df = pd.read_csv(FREESURFER_CSV)

    assert_unique(ratings_df, ["subid", "sesid"], "T1 ratings")
    assert_unique(fs_df, ["participant_id"], "FreeSurfer")

    ratings_df = ratings_df.copy()
    ratings_df["participant_id"] = normalize_participant(ratings_df["subid"])
    ratings_df["session_id"] = normalize_session(ratings_df["sesid"])

    fs_df = fs_df.copy()
    fs_df["participant_id"] = normalize_participant(fs_df["participant_id"])
    fs_df["mean_euler"] = (fs_df["lh_euler"] + fs_df["rh_euler"]) / 2

    t1_df = ratings_df.merge(
        fs_df[["participant_id", "lh_euler", "rh_euler", "mean_euler"]],
        on="participant_id",
        how="inner",
        validate="one_to_one",
    )

    if len(t1_df) != len(ratings_df):
        raise ValueError("T1 ratings and FreeSurfer tables did not merge cleanly.")

    t1_df["qc_determination"] = t1_df["classification"].str.lower()

    t1_df = t1_df[
        [
            "participant_id",
            "session_id",
            "average_rating",
            "classification",
            "lh_euler",
            "rh_euler",
            "mean_euler",
            "qc_determination",
        ]
    ]
    t1_df = sort_output(t1_df)

    sidecar = {
        "participant_id": {
            "LongName": "Participant identifier",
            "Description": "The BIDS participant label for the scan.",
        },
        "session_id": {
            "LongName": "Session identifier",
            "Description": "The BIDS session label for the scan.",
        },
        "average_rating": {
            "LongName": "Average manual T1w rating",
            "Description": (
                "Mean rating (0 - 1) of four independent slices from visual "
                "inspection of T1-weighted images by two independent raters."
            ),
        },
        "classification": {
            "LongName": "Manual consensus classification",
            "Description": (
                "Consensus label derived from the average rating. Pass means all "
                "slices were approved, Fail means all slices were rejected, and Artifact "
                "means between 1 and 3 slices contained artifacts."
            ),
            "Levels": {
                "Pass": "All slices were approved (average rating 1.0).",
                "Artifact": "Between 1 and 3 slices contained artifacts (average rating 0.25-0.75).",
                "Fail": "All slices contained artifacts (average rating 0.0).",
            },
        },
        "lh_euler": {
            "LongName": "Left hemisphere Euler number",
            "Description": (
                "Euler characteristic of the left hemisphere surface from "
                "FreeSurfer reconstruction. Less negative values indicate "
                "fewer topological defects."
            ),
        },
        "rh_euler": {
            "LongName": "Right hemisphere Euler number",
            "Description": (
                "Euler characteristic of the right hemisphere surface from "
                "FreeSurfer reconstruction. Less negative values indicate "
                "fewer topological defects."
            ),
        },
        "mean_euler": {
            "LongName": "Mean Euler number",
            "Description": (
                "Mean of the left and right hemisphere Euler characteristics from "
                "FreeSurfer surface reconstruction."
            ),
        },
        "qc_determination": {
            "LongName": "Final T1w QC determination",
            "Description": (
                "Final T1w QC call derived from the manual consensus classification."
            ),
            "Levels": {
                "artifact": "Some artifacts present; use with caution.",
                "fail": "The scan fails QC and should be excluded from T1w-derived analyses.",
                "pass": "The scan passes QC and can be used in T1w-derived analyses.",
            },
        },
    }

    return t1_df, sidecar


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fmri_df, fmri_sidecar = build_fmri_qc()
    save_outputs("fmri", fmri_df, fmri_sidecar)

    diffusion_df, diffusion_sidecar = build_diffusion_qc()
    save_outputs("diffusion", diffusion_df, diffusion_sidecar)

    asl_df, asl_sidecar = build_asl_qc()
    save_outputs("asl", asl_df, asl_sidecar)

    t1_df, t1_sidecar = build_t1_qc()
    save_outputs("T1", t1_df, t1_sidecar)

    print(f"Wrote final QC outputs to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
