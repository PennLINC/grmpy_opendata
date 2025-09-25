import glob
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os


def setup_paths():
    """Set up all required paths for input and output"""
    project_path = "/cbica/projects/grmpy/"
    inpath_qc = os.path.join(project_path, "data/derivatives/xcpd/")
    outpath = os.path.join(project_path, "code/curation/06_QC/data/")
    os.makedirs(outpath, exist_ok=True)

    return {
        "inpath_qc": inpath_qc,
        "outpath": outpath,
        "coverage_csv": os.path.join(outpath, "xcpd_4S1056Parcels_qc_coverage.csv"),
        "col_sums_csv": os.path.join(
            outpath, "xcpd_4S1056Parcels_qc_coverage_col_sums.csv"
        ),
        "row_sums_csv": os.path.join(
            outpath, "xcpd_4S1056Parcels_qc_coverage_row_sums.csv"
        ),
        "fd_csv": os.path.join(outpath, "xcpd_qc_median_fd.csv"),
    }


def collect_coverage_data(inpath_qc):
    """Collect and concatenate coverage data from individual files"""
    fileNames_qc = sorted(
        glob.glob(
            os.path.join(
                inpath_qc,
                "sub-*",
                "ses-*",
                "func",
                "sub-*_ses-*_task-*_space-*_seg-4S1056Parcels_stat-coverage_bold.tsv",
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

    return pd.concat(df_all, ignore_index=True)


def analyze_column_coverage(df, paths):
    """Analyze coverage by column (parcels) and create visualizations"""
    # Metadata columns to exclude
    metadata_cols = ["sub", "ses", "task", "space", "seg", "stat", "acq"]

    # Identify parcel columns
    parcel_cols = [col for col in df.columns if col not in metadata_cols]

    # Calculate column sums: count of values < 0.5 per parcel
    col_sums = (df[parcel_cols] < 0.5).sum()

    # Add column sums row to dataframe
    col_sum_row = {col: "" for col in metadata_cols}
    col_sum_row["sub"] = "col_sum"
    col_sum_row.update(col_sums.to_dict())
    df_with_sums = pd.concat([df, pd.DataFrame([col_sum_row])], ignore_index=True)

    # Save updated CSV
    df_with_sums.to_csv(paths["col_sums_csv"], index=False)

    # Create visualizations
    create_column_visualizations(col_sums, paths["outpath"])

    return df_with_sums, col_sums


def analyze_row_coverage(df, paths):
    """Analyze coverage by row (subjects) and create visualizations"""
    # Metadata columns to exclude
    metadata_cols = ["sub", "ses", "task", "space", "seg", "stat", "acq"]

    # Identify parcel columns
    parcel_cols = [col for col in df.columns if col not in metadata_cols]

    # Compute row sum: count of parcel values < 0.5
    df["row_sum"] = (df[parcel_cols] < 0.5).sum(axis=1)

    # Save updated CSV
    df.to_csv(paths["row_sums_csv"], index=False)

    # Create visualizations
    create_row_visualizations(df["row_sum"], paths["outpath"])

    return df


def create_column_visualizations(col_sums, output_dir):
    """Create visualizations for column-wise analysis"""
    # Histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(
        col_sums.values,
        bins=range(int(col_sums.min()), int(col_sums.max()) + 2),
        discrete=True,
        color="darkorange",
        edgecolor="black",
    )
    plt.title("Histogram of Column Sum (< 0.5 Coverage Count per Parcel)")
    plt.xlabel("Number of Rows with Parcel Value < 0.5")
    plt.ylabel("Number of Parcels")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "xcpd_4S1056Parcels_coverage_col_sum_histogram.png")
    )
    plt.close()

    # Bar plot
    col_sum_counts = col_sums.value_counts().sort_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(x=col_sum_counts.index, y=col_sum_counts.values, color="steelblue")
    plt.title("Bar Plot of Column Sums (< 0.5 Coverage Count per Parcel)")
    plt.xlabel("Number of Rows with Parcel Value < 0.5")
    plt.ylabel("Number of Parcels")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "xcpd_4S1056Parcels_coverage_col_sum_barplot.png")
    )
    plt.close()


def create_row_visualizations(row_sums, output_dir):
    """Create visualizations for row-wise analysis"""
    # Determine observed range
    row_sum_min = row_sums.min()
    row_sum_max = row_sums.max()
    bins = range(int(row_sum_min), int(row_sum_max) + 2)

    # Regular histogram
    sns.set(style="whitegrid")
    plt.figure(figsize=(10, 6))
    sns.histplot(row_sums, bins=bins, kde=False, color="steelblue", edgecolor="black")
    plt.title("Histogram of Row Sum (< 0.5 Parcel Values)")
    plt.xlabel("Number of Parcel Values < 0.5")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "xcpd_4S1056Parcels_coverage_row_sum_histogram.png")
    )
    plt.close()

    # Log-scaled histogram
    plt.figure(figsize=(10, 6))
    sns.histplot(
        row_sums,
        bins=bins,
        kde=False,
        color="darkorange",
        edgecolor="black",
        log_scale=(False, True),
    )
    plt.title("Histogram of Row Sum (Log-Scaled Y-Axis)")
    plt.xlabel("Number of Parcel Values < 0.5")
    plt.ylabel("Log-scaled Frequency")
    plt.tight_layout()
    plt.savefig(
        os.path.join(
            output_dir, "xcpd_4S1056Parcels_coverage_row_sum_histogram_log.png"
        )
    )
    plt.close()

    # Bar plot
    row_sum_counts = row_sums.value_counts().sort_index()
    plt.figure(figsize=(10, 6))
    sns.barplot(
        x=row_sum_counts.index,
        y=row_sum_counts.values,
        color="mediumseagreen",
        edgecolor="black",
    )
    plt.title("Bar Plot of Row Sum Values (< 0.5 Parcels)")
    plt.xlabel("Row Sum")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "xcpd_4S1056Parcels_coverage_row_sum_barplot.png")
    )
    plt.close()


def analyze_median_fd(paths):
    """Analyze median framewise displacement and create visualization"""
    # Get all filenames for motion data
    fileNames_qc = sorted(
        glob.glob(
            os.path.join(
                paths["inpath_qc"], "sub-*/ses-*/func/sub-*_ses-*_task-*_motion.tsv"
            )
        )
    )

    # Get subject IDs based on filenames
    subjList_qc = [
        fileNames_qc[s].split("/")[-1].split("_")[0] for s in range(len(fileNames_qc))
    ]

    # Check filenames to define number of columns
    check_filename = [
        len(fileNames_qc[iSubj].split("/")[-1].split("_"))
        for iSubj in range(len(subjList_qc))
    ]
    unique_namelength = np.unique(np.array(check_filename))
    maxidx = np.where(np.array(check_filename) == unique_namelength.max())[0][0]

    # Generate empty main df for qc
    split_name = fileNames_qc[maxidx].split("/")[-1].split("_")
    col_names_max = [split_title.split("-")[0] for split_title in split_name[:-1]]
    subj_qc = pd.read_csv(fileNames_qc[maxidx], delimiter="\t")
    df_main_qc = pd.DataFrame(columns=list(col_names_max) + list(subj_qc.columns))

    # Fill in the main qc df
    for iSubj in range(len(subjList_qc)):
        # Load each subject file
        subj_qc = pd.read_csv(fileNames_qc[iSubj], delimiter="\t")
        # Calculate the median across rows
        median_series = subj_qc.median(axis=0)
        # Convert to dataframe with one row
        subj_qc_median = pd.DataFrame(median_series).T
        subj_qc_median = subj_qc_median.reset_index(drop=True)

        # Get column values from filenames
        split_name = fileNames_qc[iSubj].split("/")[-1].split("_")
        col_names = [split_title.split("-")[0] for split_title in split_name[:-1]]
        df_temp = pd.DataFrame(columns=col_names)
        col_vals = [split_title.split("-")[1] for split_title in split_name[:-1]]
        df_temp.loc[0] = col_vals

        # Combine filename info with qc info
        df_subj_qc = pd.concat([df_temp, subj_qc_median], axis=1)
        df_main_qc = pd.concat([df_main_qc, df_subj_qc], ignore_index=True)

    # Save concatenated data
    df_main_qc.to_csv(paths["fd_csv"], index=False)

    # Create visualization
    plt.figure(figsize=(10, 6))
    sns.displot(df_main_qc["framewise_displacement"], kde=True, bins=20)
    plt.title("Median FD distribution")
    plt.xlabel("Median FD")
    plt.ylabel("Density")
    plt.tight_layout()
    plt.savefig(
        os.path.join(paths["outpath"], "xcpd_qc_histogram_median_fd.png"),
        bbox_inches="tight",
        dpi=300,
        transparent=True,
    )
    plt.close()

    return df_main_qc


def main():
    """Main execution function"""
    # Setup paths
    paths = setup_paths()

    # Step 1: Analyze median framewise displacement
    print("Analyzing median framewise displacement...")
    analyze_median_fd(paths)
    print(f"Median FD analysis saved to: {paths['fd_csv']}")

    # Step 2: Collect and concatenate coverage data
    print("\nCollecting coverage data...")
    df_coverage = collect_coverage_data(paths["inpath_qc"])
    df_coverage.to_csv(paths["coverage_csv"], index=False)
    print(f"Coverage data saved to: {paths['coverage_csv']}")

    # Step 3: Analyze column coverage
    print("\nAnalyzing column coverage...")
    df_with_col_sums, col_sums = analyze_column_coverage(df_coverage, paths)
    print(f"Column analysis saved to: {paths['col_sums_csv']}")

    # Step 4: Analyze row coverage
    print("\nAnalyzing row coverage...")
    analyze_row_coverage(df_coverage, paths)
    print(f"Row analysis saved to: {paths['row_sums_csv']}")

    print("\nAnalysis complete! All files have been saved to:", paths["outpath"])


if __name__ == "__main__":
    main()
