"""
Collect Schaefer 2018 400-parcel cortical thickness (thickavg) values from
per-subject FreeSurfer surface stats TSVs and write a wide-format summary TSV.

Input:
    /cbica/projects/grmpy/data/derivatives/freesurfer-post/sub-*/
        sub-*_seg-Schaefer2018400Parcels7Networks_surfacestats.tsv

Output:
    /cbica/projects/grmpy/code/misc/Schaefer2018400Parcels7Networks_ct.tsv

Columns: participant_id | <one column per ROI (thickavg)> | mean_ct
The Background+FreeSurfer_Defined_Medial_Wall ROI is excluded.
"""

import glob
import os

import pandas as pd

DERIV_DIR = "/cbica/projects/grmpy/data/derivatives/freesurfer-post"
TSV_GLOB = os.path.join(
    DERIV_DIR, "sub-*", "sub-*_seg-Schaefer2018400Parcels7Networks_surfacestats.tsv"
)
OUTPUT_PATH = "/cbica/projects/grmpy/code/misc/Schaefer2018400Parcels7Networks_ct.tsv"
MEDIAL_WALL = "Background+FreeSurfer_Defined_Medial_Wall"


def process_subject(tsv_path: str) -> pd.Series | None:
    df = pd.read_csv(tsv_path, sep="\t")

    df = df[df["structname"] != MEDIAL_WALL].copy()

    if df.empty:
        print(f"  WARNING: no ROIs remaining after filtering medial wall in {tsv_path}")
        return None

    participant_id = df["participant_id"].iloc[0]

    roi_series = df.set_index("structname")["thickavg"]
    roi_series.name = None

    result = pd.Series({"participant_id": participant_id})
    result = pd.concat([result, roi_series])
    result["mean_ct"] = roi_series.mean()

    return result


def main():
    tsv_files = sorted(glob.glob(TSV_GLOB))

    if not tsv_files:
        raise FileNotFoundError(
            f"No TSV files found matching pattern:\n  {TSV_GLOB}\n"
            "Check that the derivatives directory is mounted and the file naming is correct."
        )

    print(f"Found {len(tsv_files)} subject TSV(s). Processing...")

    rows = []
    for path in tsv_files:
        print(f"  {os.path.basename(os.path.dirname(path))}")
        row = process_subject(path)
        if row is not None:
            rows.append(row)

    if not rows:
        raise RuntimeError("No valid data was collected. Output not written.")

    output_df = pd.DataFrame(rows).reset_index(drop=True)

    cols = (
        ["participant_id"]
        + [c for c in output_df.columns if c not in ("participant_id", "mean_ct")]
        + ["mean_ct"]
    )
    output_df = output_df[cols]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output_df.to_csv(OUTPUT_PATH, sep="\t", index=False)

    print(
        f"\nDone. {len(output_df)} participant(s), {len(output_df.columns) - 2} ROI columns."
    )
    print(f"Output written to:\n  {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
