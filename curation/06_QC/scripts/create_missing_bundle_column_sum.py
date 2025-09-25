import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# -------------------------------
# Configuration
# -------------------------------
input_csv = "/cbica/projects/executive_function/EF_dataset_figures/concatenated_data/concatenated_bundle_volume.csv" #CUBIC project path
output_csv = "/cbica/projects/executive_function/EF_dataset_figures/concatenated_data/missing_bundle_column_sum.csv" #CUBIC project path
plot_path = "/cbica/projects/executive_function/EF_dataset_figures/concatenated_data/missing_bundle_column_distribution.png" #CUBIC project path

# -------------------------------
# Load data
# -------------------------------
df = pd.read_csv(input_csv)

# -------------------------------
# Identify bundle columns (exclude metadata)
# -------------------------------
meta_cols = ['subject', 'session']
exclude_cols = meta_cols + ['total_volume_all_bundles', 'mean_bundle_volume']
volume_cols = [col for col in df.columns if col not in exclude_cols]

# -------------------------------
# Count NaNs per bundle column
# -------------------------------
missing_counts = df[volume_cols].isna().sum()

# -------------------------------
# Create new row
# -------------------------------
# Convert counts to a dict with all columns present (meta columns get NaN)
new_row = {col: (missing_counts[col] if col in missing_counts else pd.NA) for col in df.columns}
# Append label in subject column for clarity
new_row['subject'] = 'num_subjects_with_missing_bundle'
new_row['session'] = pd.NA

# Append to DataFrame
df_with_row = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

# -------------------------------
# Save to CSV
# -------------------------------
df_with_row.to_csv(output_csv, index=False)
print(f"Saved missing bundle counts per column to: {output_csv}")

# -------------------------------
# Plot distribution of missing counts across bundle columns
# -------------------------------
plt.ion()
sns.displot(missing_counts, kde=False, bins=20)
plt.title('Number of Subjects with Missing Data per Bundle')
plt.xlabel('Number of Missing Subjects')
plt.ylabel('Bundle Count')
plt.tight_layout()
plt.savefig(plot_path, bbox_inches='tight', dpi=300, transparent=True)
plt.close()

print(f"Saved missing bundle distribution plot to: {plot_path}")

