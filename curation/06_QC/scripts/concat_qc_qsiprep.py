 
import glob
import pandas as pd
import numpy as np
import os
import seaborn as sns
import matplotlib.pyplot as plt


project_path = '/cbica/projects/executive_function/'
inpath_qc = project_path + 'EF_dataset/derivatives/qsiprep_BABS_EF_full_project_outputs/qsiprep' #CUBIC project path - replace
outpath = project_path + 'EF_dataset_figures/concatenated_data/' #CUBIC project path - replace

fileNames_qc = sorted(glob.glob(os.path.join(
    inpath_qc, 'sub-*', 'ses-*', 'dwi',
    'sub-*_ses-*_space-*_desc-image_qc.tsv'
)))

df_all = []

for fpath in fileNames_qc:
    # Load single-row coverage data
    df_qc = pd.read_csv(fpath, delimiter='\t')

    # Extract metadata from filename
    fname_parts = os.path.basename(fpath).split('_')
    metadata = {p.split('-')[0]: p.split('-')[1] for p in fname_parts[:-1]}  # skip .tsv part

    # Combine metadata and QC values into one row
    df_row = pd.DataFrame({**metadata, **df_qc.to_dict(orient='records')[0]}, index=[0])
    df_all.append(df_row)

# Combine all rows
df_main_qc = pd.concat(df_all, ignore_index=True)

# Save
os.makedirs(outpath, exist_ok=True)
df_main_qc.to_csv(os.path.join(outpath, 'concat_qsiprep_qc.csv'), index=False)



################
# plotting
################
# plot the distribution of mean FD
plt.ion()
sns.set_context(font_scale=1.5)
sns.displot(df_main_qc['raw_neighbor_corr'], kde=True, bins=20)
plt.title('Mean Neighborhood Corr distribution')
plt.xlabel('Mean Neighborhood Corr')
plt.ylabel('Density')
plt.tight_layout()
plt.savefig(outpath + 'concat_qsiprep_neighborhood_corr_histogram.png',
            bbox_inches='tight', dpi=300,
            transparent=True)
plt.close()


plt.ion()
sns.set_context(font_scale=1.5)
sns.displot(df_main_qc['mean_fd'], kde=True, bins=20)
plt.title('Mean FD distribution')
plt.xlabel('Mean FD')
plt.ylabel('Density')
plt.tight_layout()
plt.savefig(outpath + 'concat_qsiprep_fd_histogram.png',
            bbox_inches='tight', dpi=300,
            transparent=True)
plt.close()



################
# scatterplot
################
plt.ion()
sns.set(style='whitegrid')
sns.set_context(font_scale=1.5)

# Create scatterplot of mean FD vs. raw neighborhood corr
scatter_plot = sns.scatterplot(
    data=df_main_qc,
    x='mean_fd',
    y='raw_neighbor_corr',
    s=50,  # marker size
    alpha=0.7,
    edgecolor='k'
)

plt.title('Mean FD vs. Raw Neighborhood Correlation')
plt.xlabel('Mean Framewise Displacement (FD)')
plt.ylabel('Raw Neighborhood Correlation')
plt.tight_layout()

# Save the figure
plt.savefig(outpath + 'scatter_meanfd_vs_neighborcorr.png',
            bbox_inches='tight', dpi=300, transparent=True)
plt.close()

