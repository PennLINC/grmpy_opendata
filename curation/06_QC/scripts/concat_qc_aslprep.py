import glob
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ----------------------
# Paths
# ----------------------
project_path = '/cbica/projects/executive_function/'
inpath_qc = os.path.join(project_path, 'EF_dataset/derivatives/aslprep_BABS_EF_full_project_outputs/aslprep/') #CUBIC project path - replace
outpath = os.path.join(project_path, 'EF_dataset_figures/concatenated_data/') #CUBIC project path - replace
os.makedirs(outpath, exist_ok=True)

# ----------------------
# Get all QC file paths
# ----------------------
fileNames_qc = sorted(
    glob.glob(
        os.path.join(inpath_qc, 'sub-*/ses-*/perf/', 'sub-*_ses-*_run-*_desc-qualitycontrol_cbf.tsv')
    )
)

# ----------------------
# Loop through files, compute mean QC values
# ----------------------
rows = []

for fpath in fileNames_qc:
    subj_qc = pd.read_csv(fpath, delimiter='\t')

    # Drop any unnamed index columns
    subj_qc = subj_qc.loc[:, ~subj_qc.columns.str.startswith('Unnamed')]

    # Separate metadata and numeric data
    numeric_cols = subj_qc.select_dtypes(include='number').columns
    mean_values = subj_qc[numeric_cols].mean(axis=0)

    # Get metadata (take from first row)
    metadata_cols = ['sub', 'ses', 'acq', 'run']
    metadata = {}
    for col in metadata_cols:
        if col in subj_qc.columns:
            metadata[col] = subj_qc[col].iloc[0]
        else:
            metadata[col] = 'n/a'

    # Combine metadata + means into one row
    combined = pd.DataFrame([{**metadata, **mean_values.to_dict()}])
    rows.append(combined)

# ----------------------
# Concatenate all rows into a single dataframe
# ----------------------
df_main_qc = pd.concat(rows, ignore_index=True)

# ----------------------
# Save concatenated QC file
# ----------------------
qc_output_path = os.path.join(outpath, 'concat_aslprep_qc.csv')
df_main_qc.to_csv(qc_output_path, index=False)
print(f"Saved concatenated QC file to: {qc_output_path}")

# ----------------------
# Plot QEI distribution
# ----------------------
plt.ion()
sns.displot(df_main_qc['qei_cbf'].astype(float), kde=True, bins=20)
plt.title('Mean QEI Distribution')
plt.xlabel('Mean QEI')
plt.ylabel('Density')
plt.tight_layout()

plot_output_path = os.path.join(outpath, 'concat_aslprep_qc_histogram.png')
plt.savefig(plot_output_path, bbox_inches='tight', dpi=300, transparent=True)
plt.close()
print(f"Saved QEI histogram to: {plot_output_path}")

