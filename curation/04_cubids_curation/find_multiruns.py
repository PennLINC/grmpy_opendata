#!/usr/bin/env python3
"""
Script to find files with multiple runs in a v#_files.tsv file.
Extracts rows where 'run' is contained in the FilePath column and outputs a sorted TSV.
Sorting is done by extracting the subject id from the file path, then by acquisition type,
with run-01 files appearing before run-02 files.
"""

import argparse
import pandas as pd
import os
import re


def find_multi_runs(input_file, output_file):
    """
    Find rows in a TSV file where 'run' is contained in the FilePath column.
    Sorts the filtered rows by subject id, then by acquisition type, with run numbers in ascending order.

    Parameters:
    -----------
    input_file : str
        Path to the input TSV file
    output_file : str
        Path to the output TSV file where the sorted, matching rows will be saved
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Read the TSV file
    print(f"Reading input file: {input_file}")
    df = pd.read_csv(input_file, sep="\t")

    # Get the last column (assumed to be FilePath)
    file_path_col = df.columns[-1]

    # Filter rows where 'run' is in the FilePath (case-insensitive)
    run_files = df[df[file_path_col].str.contains("run", case=False, na=False)]
    run_files = run_files.copy()  # avoid SettingWithCopyWarning

    # Extract the subject id from the file path
    run_files["subject_id"] = run_files[file_path_col].apply(lambda x: x.split("/")[1])

    # Extract acquisition type and suffix (everything after run-XX)
    def extract_acq_suffix(filepath):
        # Get the filename from the path
        filename = os.path.basename(filepath)
        # Extract everything after run-XX
        match = re.search(r"run-\d+_(.+)", filename)
        if match:
            return match.group(1)
        return ""  # Fallback if pattern not found

    run_files["acq_suffix"] = run_files[file_path_col].apply(extract_acq_suffix)

    # Extract the base part of the filename (before run-XX)
    def extract_base_name(filepath):
        # Get the filename from the path
        filename = os.path.basename(filepath)
        # Extract everything before run-XX
        match = re.search(r"(.+?)_run-\d+", filename)
        if match:
            return match.group(1)
        return filename  # Fallback if pattern not found

    run_files["base_name"] = run_files[file_path_col].apply(extract_base_name)

    # Extract run number for sorting
    def extract_run_num(filepath):
        match = re.search(r"run-(\d+)", filepath)
        if match:
            return int(match.group(1))
        return 999  # High number for files without run number

    run_files["run_num"] = run_files[file_path_col].apply(extract_run_num)

    # Sort the dataframe by subject_id, then by base_name, then by acq_suffix, then by run number
    run_files = run_files.sort_values(
        ["subject_id", "base_name", "acq_suffix", "run_num"]
    )

    # Remove the helper columns before saving
    run_files = run_files.drop(
        columns=["subject_id", "base_name", "acq_suffix", "run_num"]
    )

    # Save the sorted, filtered rows to a new TSV file
    print(f"Found {len(run_files)} files containing 'run' in the path")
    run_files.to_csv(output_file, sep="\t", index=False)
    print(f"Results saved to: {output_file}")

    return len(run_files)


def main():
    parser = argparse.ArgumentParser(
        description="Find files with multiple runs in a TSV file"
    )
    parser.add_argument("input_file", help="Path to the input TSV file")
    parser.add_argument("output_file", help="Path to the output TSV file")
    args = parser.parse_args()

    count = find_multi_runs(args.input_file, args.output_file)
    print(f"Total files with 'run' in path: {count}")


if __name__ == "__main__":
    main()
