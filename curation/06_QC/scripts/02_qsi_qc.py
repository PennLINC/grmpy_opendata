import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from glob import glob

# -------------------------------
# Configuration
# -------------------------------
project_path = "/cbica/projects/grmpy/"
qsiprep_path = os.path.join(project_path, "data/derivatives/qsiprep")
qsirecon_path = os.path.join(
    project_path,
    "data/derivatives/qsirecon/derivatives/qsirecon-DSIStudio",
)
output_path = os.path.join(project_path, "code/curation/06_QC/data")

# Create output directory
os.makedirs(output_path, exist_ok=True)


# -------------------------------
# Step 1: Process Bundle Stats
# -------------------------------
def process_bundle_stats():
    """Convert bundlestats CSVs to per-subject volume CSVs."""
    print("\nProcessing bundle stats files...")

    bundlestats_files = glob(
        os.path.join(qsirecon_path, "sub-*", "ses-*", "dwi", "*_bundlestats.csv")
    )
    print(f"Found {len(bundlestats_files)} bundlestats files...")

    for csv_file in bundlestats_files:
        try:
            # Load the CSV
            df = pd.read_csv(csv_file)

            # Make sure expected columns are present
            if "bundle_name" not in df.columns or "total_volume_mm3" not in df.columns:
                print(f"Skipping file {csv_file} - missing expected columns.")
                continue

            # Pivot: one row, one column per bundle
            pivot_df = df.set_index("bundle_name")["total_volume_mm3"].T.to_frame().T

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


# -------------------------------
# Step 2: Concatenate Volume Stats
# -------------------------------
def concatenate_volume_stats():
    """Concatenate individual volume CSVs and create visualizations."""
    print("\nConcatenating volume stats...")

    volume_files = glob(
        os.path.join(
            qsirecon_path, "sub-*", "ses-*", "dwi", "*_space-ACPC_model-gqi_volume.csv"
        )
    )
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
    if not all_rows:
        print("No valid volume files found.")
        return None

    df_concat = pd.concat(all_rows, ignore_index=True)

    # Compute total and mean bundle volume per row
    volume_cols = df_concat.filter(like="total_volume_mm3_")
    df_concat["total_volume_all_bundles"] = volume_cols.sum(axis=1)
    df_concat["mean_bundle_volume"] = volume_cols.mean(axis=1)

    # Save concatenated data
    concat_csv_path = os.path.join(output_path, "qsirecon_DSIStudio_bundle_volume.csv")
    df_concat.to_csv(concat_csv_path, index=False)
    print(f"Saved concatenated CSV to: {concat_csv_path}")

    # Create visualizations
    create_volume_visualizations(df_concat)

    return df_concat


def create_volume_visualizations(df_concat):
    """Create visualizations for volume data."""
    # Plot 1: Total Volume Histogram
    plt.ion()
    sns.displot(df_concat["total_volume_all_bundles"].astype(float), kde=True, bins=20)
    plt.title("Total Bundle Volume Distribution")
    plt.xlabel("Total Volume (mmB3)")
    plt.ylabel("Density")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_path, "qsirecon_DSIStudio_bundle_volume_histogram.png"),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()

    # Plot 2: Mean Volume Histogram
    plt.ion()
    sns.displot(df_concat["mean_bundle_volume"].astype(float), kde=True, bins=20)
    plt.title("Mean Bundle Volume Distribution")
    plt.xlabel("Mean Volume per Bundle (mmB3)")
    plt.ylabel("Density")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            output_path, "qsirecon_DSIStudio_bundle_volume_mean_histogram.png"
        ),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()


# -------------------------------
# Step 3: Analyze Missing Data
# -------------------------------
def analyze_missing_data(df):
    """Analyze and visualize missing data patterns."""
    print("\nAnalyzing missing data patterns...")

    # Identify bundle columns
    meta_cols = ["subject", "session"]
    exclude_cols = meta_cols + ["total_volume_all_bundles", "mean_bundle_volume"]
    volume_cols = [col for col in df.columns if col not in exclude_cols]

    # Count NaNs per bundle column
    missing_counts = df[volume_cols].isna().sum()

    # Create new row with missing counts
    new_row = {
        col: (missing_counts[col] if col in missing_counts else pd.NA)
        for col in df.columns
    }
    new_row["subject"] = "num_subjects_with_missing_bundle"
    new_row["session"] = pd.NA

    # Append to DataFrame and save
    df_with_row = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df_with_row.to_csv(
        os.path.join(output_path, "qsirecon_DSIStudio_missing_bundle_column_sum.csv"),
        index=False,
    )

    # Create visualization
    plt.ion()
    sns.displot(missing_counts, kde=False, bins=20)
    plt.title("Number of Subjects with Missing Data per Bundle")
    plt.xlabel("Number of Missing Subjects")
    plt.ylabel("Bundle Count")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            output_path, "qsirecon_DSIStudio_missing_bundle_column_distribution.png"
        ),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()


# -------------------------------
# Step 4: Analyze Bundle Outliers
# -------------------------------
def analyze_bundle_outliers(df):
    """Analyze and identify outliers in bundle volumes."""
    print("\nAnalyzing bundle outliers...")

    # Define columns
    meta_cols = ["subject", "session"]
    exclude_cols = meta_cols + ["total_volume_all_bundles", "mean_bundle_volume"]
    volume_cols = [col for col in df.columns if col not in exclude_cols]

    # Compute column-wise stats
    col_means = df[volume_cols].mean()
    col_stds = df[volume_cols].std()
    upper_thresh = col_means + 3 * col_stds
    lower_thresh = col_means - 3 * col_stds

    # Flag outliers and NaNs
    outlier_df = df.copy()
    outlier_matrix = pd.DataFrame(0, index=df.index, columns=volume_cols)

    for col in volume_cols:
        outlier_matrix[col] = (
            (df[col].isna())  # Flag NaN values
            | (df[col] >= upper_thresh[col])
            | (df[col] <= lower_thresh[col])
        ).astype(int)

    # Add binary flags and compute summary metrics
    outlier_df.update(outlier_matrix)
    outlier_df["num_row_outliers"] = outlier_matrix.sum(axis=1)
    outlier_df["num_missing_bundles"] = df[volume_cols].isna().sum(axis=1)

    # Save results
    outlier_df.to_csv(
        os.path.join(output_path, "qsirecon_DSIStudio_row_sum_bundle_volume.csv"),
        index=False,
    )

    # Create visualization
    plt.ion()
    sns.displot(outlier_df["num_row_outliers"], kde=True, bins=20)
    plt.title(
        "Outlier Bundle Count per Subject (greater or less than 3 SD from bundle mean or NaN)"
    )
    plt.xlabel("Number of Outlier Bundles")
    plt.ylabel("Subject Count")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            output_path, "qsirecon_DSIStudio_row_bundle_outlier_distribution.png"
        ),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()


# -------------------------------
# Step 5: Process QSIPrep QC
# -------------------------------
def process_qsiprep_qc():
    """Process and visualize QSIPrep QC metrics."""
    print("\nProcessing QSIPrep QC metrics...")

    fileNames_qc = sorted(
        glob(
            os.path.join(
                qsiprep_path,
                "sub-*",
                "ses-*",
                "dwi",
                "sub-*_ses-*_space-*_desc-image_qc.tsv",
            )
        )
    )

    df_all = []

    for fpath in fileNames_qc:
        # Load single-row coverage data
        df_qc = pd.read_csv(fpath, delimiter="\t")

        # Extract metadata from filename
        fname_parts = os.path.basename(fpath).split("_")
        metadata = {p.split("-")[0]: p.split("-")[1] for p in fname_parts[:-1]}

        # Combine metadata and QC values into one row
        df_row = pd.DataFrame(
            {**metadata, **df_qc.to_dict(orient="records")[0]}, index=[0]
        )
        df_all.append(df_row)

    # Combine all rows and save
    df_main_qc = pd.concat(df_all, ignore_index=True)
    df_main_qc.to_csv(os.path.join(output_path, "qsiprep_qc.csv"), index=False)

    # Create visualizations
    create_qsiprep_visualizations(df_main_qc)


def create_qsiprep_visualizations(df_main_qc):
    """Create visualizations for QSIPrep QC metrics."""
    # Plot 1: Neighborhood Correlation
    plt.ion()
    sns.set_context(font_scale=1.5)
    sns.displot(df_main_qc["raw_neighbor_corr"], kde=True, bins=20)
    plt.title("Mean Neighborhood Corr distribution")
    plt.xlabel("Mean Neighborhood Corr")
    plt.ylabel("Density")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_path, "qsiprep_neighborhood_corr_histogram.png"),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()

    # Plot 2: Mean FD
    plt.ion()
    sns.set_context(font_scale=1.5)
    sns.displot(df_main_qc["mean_fd"], kde=True, bins=20)
    plt.title("Mean FD distribution")
    plt.xlabel("Mean FD")
    plt.ylabel("Density")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_path, "qsiprep_fd_histogram.png"),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()

    # Plot 3: FD vs Neighborhood Correlation
    plt.ion()
    sns.set(style="whitegrid")
    sns.set_context(font_scale=1.5)
    sns.scatterplot(
        data=df_main_qc,
        x="mean_fd",
        y="raw_neighbor_corr",
        s=50,
        alpha=0.7,
        edgecolor="k",
    )
    plt.title("Mean FD vs. Raw Neighborhood Correlation")
    plt.xlabel("Mean Framewise Displacement (FD)")
    plt.ylabel("Raw Neighborhood Correlation")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_path, "qsiprep_scatter_meanfd_vs_neighborcorr.png"),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()


# -------------------------------
# Main Execution
# -------------------------------
def main():
    """Main execution function."""
    print("Starting QSI QC Processing Pipeline...")

    # Step 1: Process bundle stats
    process_bundle_stats()

    # Step 2: Concatenate volume stats
    df_concat = concatenate_volume_stats()

    if df_concat is not None:
        # Step 3: Analyze missing data
        analyze_missing_data(df_concat)

        # Step 4: Analyze bundle outliers
        analyze_bundle_outliers(df_concat)

    # Step 5: Process QSIPrep QC
    process_qsiprep_qc()

    print("\nQSI QC Processing Pipeline completed!")


if __name__ == "__main__":
    main()
