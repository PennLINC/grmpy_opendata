#!/usr/bin/env python3
"""
Build participants_tmp.tsv and participants_tmp.json.

Assembles participant-level demographic / clinical variables from several
sources so they can later be collided into the BIDS participants.tsv/json on
CUBIC (see collide_participants_tmp.py).

Sources (all keyed on BBLID -> participant_id = sub-<BBLID>):
  - group, age (ageatscan), race, ethnicity, sex, handedness, education,
    mother_edu, father_edu:
        ignore/GRMPYDataEntryInterv-DemographicsAndDates_DATA_2026-03-30_2009.csv
  - bmi:      phenotype/data/demographics.tsv        (matched on participant_id)
  - rbc_id:   ignore/bblid_scanid_sub.csv            (matched on bblid -> rbcid)
  - dx_*:     phenotype/data/axis.tsv                (matched on participant_id)

JSON sidecar:
  - Demographic fields get an empty "Description" for you to fill in manually
    (edit DEMO_FIELD_JSON below).
  - dx_* fields are copied verbatim from phenotype/data/axis.json.

Missing / unfilled values are written as 'n/a'.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ------------------------------ Paths ---------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]

DEMO_CSV = (
    REPO_ROOT
    / "ignore"
    / "GRMPYDataEntryInterv-DemographicsAndDates_DATA_2026-03-30_2009.csv"
)
DEMOGRAPHICS_TSV = REPO_ROOT / "phenotype" / "data" / "demographics.tsv"
RBC_CSV = REPO_ROOT / "ignore" / "bblid_scanid_sub.csv"
AXIS_TSV = REPO_ROOT / "phenotype" / "data" / "axis.tsv"
AXIS_JSON = REPO_ROOT / "phenotype" / "data" / "axis.json"

OUT_TSV = SCRIPT_DIR / "participants_tmp.tsv"
OUT_JSON = SCRIPT_DIR / "participants_tmp.json"

NA = "n/a"

# ------------------------------ Config --------------------------------------

# Columns pulled straight from the REDCap demographics CSV, mapped to their
# output names. Order here defines output column order for these fields.
DEMO_CSV_COLUMNS = {
    "group": "group",
    "ageatscan": "age",
    "race": "race",
    "ethnicity": "ethnicity",
    "sex": "sex",
    "handedness": "handedness",
    "education": "education",
    "mother_edu": "mother_edu",
    "father_edu": "father_edu",
}

# dx_* diagnostic flag columns to copy from axis.tsv (in this order).
DX_COLUMNS = [
    "dx_BrderPD",
    "dx_adhd",
    "dx_anx",
    "dx_bp1",
    "dx_bpoth",
    "dx_mdd",
    "dx_moodnos",
    "dx_none",
    "dx_other",
    "dx_prodromal",
    "dx_prodromal_remit",
    "dx_pscat",
    "dx_psychosis",
    "dx_ptsd",
    "dx_scz",
    "dx_sub_abuse",
    "dx_sub_abuse_alc",
    "dx_sub_abuse_can",
    "dx_sub_abuse_oth",
    "dx_sub_dep",
    "dx_sub_dep_alc",
    "dx_sub_dep_can",
    "dx_sub_dep_oth",
]

# Final column order (excluding participant_id, which is written first).
OUTPUT_COLUMNS = [
    "group",
    "age",
    "race",
    "ethnicity",
    "sex",
    "handedness",
    "education",
    "mother_edu",
    "father_edu",
    "bmi",
    "rbc_id",
] + DX_COLUMNS

# JSON descriptions for the non-dx (demographic) fields.
# Fill in the "Description" (and any "Levels") manually.
DEMO_FIELD_JSON = {
    "group": {
        "Description": "Study group",
        "Levels": {
            "TD": "typically developing",
            "I": "irritability",
            "BPD": "borderline personality disorder"
        },
    },
    "age": {"Description": "Age at scan (years)"},
    "race": {
        "Description": "Race",
        "Levels": {
            "0": "Caucasian",
            "1": "African American",
            "2": "Asian",
            "3": "American Indian or Alaska Native",
            "4": "Hawaiian/Pacific Islander",
            "5": "Mixed/Other",
            "6": "Unknown/not reported"
        },
    },
    "ethnicity": {
        "Description": "Ethnicity",
        "Levels": {
            "0": "Non Hispanic/Latino",
            "1": "Hispanic/Latino",
            "2": "Unknown/not reported"
        },
    },
    "sex": {
        "Description": "Sex",
        "Levels": {
            "0": "Male",
            "1": "Female",
            "2": "Other",
            "3": "Not willing to answer"
        },
    },
    "handedness": {
        "Description": "Handedness",
        "Levels": {
            "0": "Right",
            "1": "Left",
            "2": "Ambidextrous"
        },
    },
    "education": {
        "Description": "Education",
        "Levels": {
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7",
            "8": "8",
            "9": "9",
            "10": "10",
            "11": "11",
            "12": "12 (high school diploma or GED)",
            "13": "13",
            "14": "14",
            "15": "15",
            "16": "16 (bachelor's degree)",
            "17": "17",
            "18": "18 (master's degree)",
            "19": "19",
            "20": "20 (ph.d or equivalent)"
        },
    },
    "mother_edu": {
        "Description": "Mother's education",
        "Levels": {
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7",
            "8": "8",
            "9": "9",
            "10": "10",
            "11": "11",
            "12": "12 (high school diploma or GED)",
            "13": "13",
            "14": "14",
            "15": "15",
            "16": "16 (bachelor's degree)",
            "17": "17",
            "18": "18 (master's degree)",
            "19": "19",
            "20": "20 (ph.d or equivalent)",
            "unknown": "unknown"
        },
    },
    "father_edu": {
        "Description": "Father's education",
        "Levels": {
            "3": "3",
            "4": "4",
            "5": "5",
            "6": "6",
            "7": "7",
            "8": "8",
            "9": "9",
            "10": "10",
            "11": "11",
            "12": "12 (high school diploma or GED)",
            "13": "13",
            "14": "14",
            "15": "15",
            "16": "16 (bachelor's degree)",
            "17": "17",
            "18": "18 (master's degree)",
            "19": "19",
            "20": "20 (ph.d or equivalent)",
            "unknown": "unknown",
    "bmi": {"Description": "Body mass index (kg/m^2)"},
    "rbc_id": {"Description": "RBC ID used to match the participant to RBC data"},
}

# ------------------------------ Helpers -------------------------------------


def clean(value) -> str:
    """Normalize a cell to a string, mapping missing to 'n/a'."""
    if value is None:
        return NA
    if isinstance(value, float) and np.isnan(value):
        return NA
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "na", "n/a"}:
        return NA
    return text


# ------------------------------ Build ---------------------------------------


def main() -> None:
    # Master roster (ground truth) = participant_id list in demographics.tsv,
    # which reflects the subjects that actually have imaging data.
    dem_tsv = pd.read_csv(DEMOGRAPHICS_TSV, sep="\t", dtype=str)
    out = pd.DataFrame({"participant_id": dem_tsv["participant_id"].str.strip()})
    bblid = out["participant_id"].str.replace("^sub-", "", regex=True)

    # Demographic fields from the REDCap CSV (keyed on bblid).
    demo = pd.read_csv(DEMO_CSV, dtype=str)
    demo["bblid"] = demo["bblid"].astype(str).str.strip()
    demo = demo.set_index("bblid")
    for src_col, out_col in DEMO_CSV_COLUMNS.items():
        out[out_col] = bblid.map(demo[src_col]).map(clean)

    # Fallback age from demographics.tsv visitagemonths/12 where CSV age missing.
    visitage_map = dict(
        zip(dem_tsv["participant_id"].str.strip(), dem_tsv["visitagemonths"])
    )
    missing_age = out["age"] == NA
    fallback_age = out.loc[missing_age, "participant_id"].map(visitage_map)
    out.loc[missing_age, "age"] = fallback_age.map(
        lambda m: NA if clean(m) == NA else f"{float(m) / 12:.2f}"
    )

    # bmi from phenotype/data/demographics.tsv (keyed on participant_id).
    bmi_map = dict(zip(dem_tsv["participant_id"].str.strip(), dem_tsv["bmi"]))
    out["bmi"] = out["participant_id"].map(bmi_map).map(clean)

    # rbc_id from ignore/bblid_scanid_sub.csv (keyed on bblid -> rbcid).
    rbc = pd.read_csv(RBC_CSV, dtype=str)
    rbc_map = dict(zip(rbc["bblid"].str.strip(), rbc["rbcid"]))
    out["rbc_id"] = bblid.map(rbc_map).map(clean)

    # dx_* flags from phenotype/data/axis.tsv (keyed on participant_id).
    axis = pd.read_csv(AXIS_TSV, sep="\t", dtype=str).set_index("participant_id")
    for col in DX_COLUMNS:
        mapped = out["participant_id"].map(axis[col]) if col in axis.columns else np.nan
        out[col] = pd.Series(mapped, index=out.index).map(clean)

    # Enforce column order and write.
    out = out[["participant_id"] + OUTPUT_COLUMNS]
    out.to_csv(OUT_TSV, sep="\t", index=False, na_rep=NA)
    print(f"Wrote {OUT_TSV} ({len(out)} participants, {len(out.columns)} columns).")

    # ---- JSON sidecar ----
    with open(AXIS_JSON) as f:
        axis_json = json.load(f)

    sidecar = {}
    for col in OUTPUT_COLUMNS:
        if col in DX_COLUMNS:
            if col in axis_json:
                sidecar[col] = axis_json[col]
            else:
                sidecar[col] = {"Description": ""}
        else:
            sidecar[col] = DEMO_FIELD_JSON.get(col, {"Description": ""})

    with open(OUT_JSON, "w") as f:
        json.dump(sidecar, f, indent=2)
        f.write("\n")
    print(f"Wrote {OUT_JSON} ({len(sidecar)} fields).")


if __name__ == "__main__":
    main()
