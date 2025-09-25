import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# -------------------------------
# Configuration
# -------------------------------
input_csv = "/cbica/projects/executive_function/EF_dataset_figures/concatenated_data/concatenated_bundle_volume.csv" #CUBIC project path
output_csv = "/cbica/projects/executive_function/EF_dataset_figures/concatenated_data/row_sum_bundle_volume.csv" #CUBIC project path
plot_path = "/cbica/projects/executive_function/EF_dataset_figures/concatenated_data/row_bundle_outlier_distribution.png" #CUBIC project path

# -------------------------------
# Load data and define columns
# -------------------------------
df = pd.read_csv(input_csv)
meta_cols = ['subject', 'session']
exclude_cols = meta_cols + ['total_volume_all_bundles', 'mean_bundle_volume']
volume_cols = [col for col in df.columns if col not in exclude_cols]

# -------------------------------
# Compute column-wise stats
# -------------------------------
col_means = df[volume_cols].mean()
col_stds = df[volume_cols].std()
upper_thresh = col_means + 3 * col_stds
lower_thresh = col_means - 3 * col_stds

# -------------------------------
# Flag high/low outliers AND NaNs
# -------------------------------
outlier_df = df.copy()
outlier_matrix = pd.DataFrame(0, index=df.index, columns=volume_cols)

for col in volume_cols:
    outlier_matrix[col] = (
        (df[col].isna()) |  # Flag NaN values
        (df[col] >= upper_thresh[col]) |
        (df[col] <= lower_thresh[col])
    ).astype(int)

# Add binary flags back into the main DataFrame
outlier_df.update(outlier_matrix)

# -------------------------------
# Count number of outliers per subject
# -------------------------------
outlier_df['num_row_outliers'] = outlier_matrix.sum(axis=1)

# -------------------------------
# Count number of missing bundle values per subject
# -------------------------------
outlier_df['num_missing_bundles'] = df[volume_cols].isna().sum(axis=1)

# -------------------------------
# Save CSV
# -------------------------------
outlier_df.to_csv(output_csv, index=False)
print(f"Saved subject-level outlier matrix to: {output_csv}")

# -------------------------------
# Plot distribution of outlier counts per subject
# -------------------------------
plt.ion()
sns.displot(outlier_df['num_row_outliers'], kde=True, bins=20)
plt.title('Outlier Bundle Count per Subject (greater or less than 3 SD from bundle mean or NaN)')
plt.xlabel('Number of Outlier Bundles')
plt.ylabel('Subject Count')
plt.tight_layout()
plt.savefig(plot_path, bbox_inches='tight', dpi=300, transparent=True)
plt.close()

print(f"Saved row outlier distribution plot to: {plot_path}")

