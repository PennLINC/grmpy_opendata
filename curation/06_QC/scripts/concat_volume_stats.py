import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from glob import glob

# -------------------------------
# Configuration
# -------------------------------
input_base = "/cbica/projects/executive_function/EF_dataset/derivatives/qsirecon_BABS_EF_full_project_outputs/qsirecon/derivatives/qsirecon-DSIStudio" #CUBIC project path - replace
output_dir = "/cbica/projects/executive_function/EF_dataset_figures/concatenated_data" #CUBIC project path - replace
os.makedirs(output_dir, exist_ok=True)
concat_csv_path = os.path.join(output_dir, "concatenated_bundle_volume.csv")
plot_total_path = os.path.join(output_dir, "concat_bundle_volume_histogram.png")
plot_mean_path = os.path.join(output_dir, "concat_bundle_volume_mean_histogram.png")

# -------------------------------
# Concatenate per-subject volumes
# -------------------------------
volume_files = glob(os.path.join(input_base, "sub-*", "ses-*", "dwi", "*_space-ACPC_model-gqi_volume.csv"))
print(f"Found {len(volume_files)} volume summary files...")

all_rows = []

for vol_file in volume_files:
    try:
        df = pd.read_csv(vol_file)

        # Extract sub and ses from path
        path_parts = os.path.normpath(vol_file).split(os.sep)
        sub_id = [p for p in path_parts if p.startswith("sub-")][0]
        ses_id = [p for p in path_parts if p.startswith("ses-")][0]

        df.insert(0, "subject", sub_id)
        df.insert(1, "session", ses_id)

        all_rows.append(df)

    except Exception as e:
        print(f"Failed to process {vol_file}: {e}")

# Concatenate and save
if all_rows:
    df_concat = pd.concat(all_rows, ignore_index=True)

    # Compute total and mean bundle volume per row
    volume_cols = df_concat.filter(like='total_volume_mm3_')
    df_concat['total_volume_all_bundles'] = volume_cols.sum(axis=1)
    df_concat['mean_bundle_volume'] = volume_cols.mean(axis=1)

    df_concat.to_csv(concat_csv_path, index=False)
    print(f"Saved concatenated CSV to: {concat_csv_path}")
else:
    print("No valid volume files found.")
    exit()

# -------------------------------
# Plot 1: Total Volume Histogram
# -------------------------------
plt.ion()
sns.displot(df_concat['total_volume_all_bundles'].astype(float), kde=True, bins=20)
plt.title('Total Bundle Volume Distribution')
plt.xlabel('Total Volume (mmB3)')
plt.ylabel('Density')
plt.tight_layout()
plt.savefig(plot_total_path, bbox_inches='tight', dpi=300, transparent=True)
plt.close()
print(f"Saved total volume histogram to: {plot_total_path}")

# -------------------------------
# Plot 2: Mean Volume Histogram
# -------------------------------
plt.ion()
sns.displot(df_concat['mean_bundle_volume'].astype(float), kde=True, bins=20)
plt.title('Mean Bundle Volume Distribution')
plt.xlabel('Mean Volume per Bundle (mmB3)')
plt.ylabel('Density')
plt.tight_layout()
plt.savefig(plot_mean_path, bbox_inches='tight', dpi=300, transparent=True)
plt.close()
print(f"Saved mean volume histogram to: {plot_mean_path}")

