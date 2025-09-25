import os
import pandas as pd
from glob import glob

# Set base path to the top-level DSIStudio directory
base_dir = "/cbica/projects/executive_function/EF_dataset/derivatives/qsirecon_BABS_EF_full_project_outputs/qsirecon/derivatives/qsirecon-DSIStudio" #CUBIC project path

# Find all *_bundlestats.csv files recursively
bundlestats_files = glob(os.path.join(base_dir, "sub-*", "ses-*", "dwi", "*_bundlestats.csv"))

print(f"Found {len(bundlestats_files)} bundlestats files...")

for csv_file in bundlestats_files:
    try:
        # Load the CSV
        df = pd.read_csv(csv_file)

        # Make sure expected columns are present
        if 'bundle_name' not in df.columns or 'total_volume_mm3' not in df.columns:
            print(f"Skipping file {csv_file} sing expected columns.")
            continue

        # Pivot: one row, one column per bundle
        pivot_df = df.set_index('bundle_name')['total_volume_mm3'].T.to_frame().T

        # Rename columns with prefix
        pivot_df.columns = [f"total_volume_mm3_{col}" for col in pivot_df.columns]

        # Extract subject and session from path
        path_parts = os.path.normpath(csv_file).split(os.sep)
        sub_id = [part for part in path_parts if part.startswith("sub-")][0]
        ses_id = [part for part in path_parts if part.startswith("ses-")][0]

        # Compose output path and filename
        out_filename = f"{sub_id}_{ses_id}_space-ACPC_model-gqi_volume.csv"
        out_path = os.path.join(os.path.dirname(csv_file), out_filename)

        # Write out the new CSV
        pivot_df.to_csv(out_path, index=False)
        print(f"Wrote: {out_path}")

    except Exception as e:
        print(f"Failed to process {csv_file}: {e}")

