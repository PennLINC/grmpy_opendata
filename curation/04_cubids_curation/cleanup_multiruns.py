#!/usr/bin/env python3
import os
import subprocess
import pandas as pd
import re

def process_files(bids_dir, tsv_path):
    # Read the TSV file
    try:
        df = pd.read_csv(tsv_path, sep='\t')
    except Exception as e:
        print(f"Error reading TSV file: {e}")
        return

    # Check if required columns exist
    if 'DROP' not in df.columns or 'FilePath' not in df.columns:
        print("Error: TSV file must contain 'DROP' and 'FilePath' columns")
        return

    # Process each row
    for _, row in df.iterrows():
        # Skip rows where DROP is not 0 or 1
        if pd.isna(row['DROP']) or (row['DROP'] != 0 and row['DROP'] != 1):
            continue

        # Get the full file path
        file_path = os.path.join(bids_dir, row['FilePath'].lstrip('/'))

        # Check if file exists
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            continue

        if row['DROP'] == 1:
            # Remove file with git rm
            try:
                print(f"Removing file: {file_path}")
                subprocess.run(['git', 'rm', file_path], check=True)
                print(f"Successfully removed: {file_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error removing file {file_path}: {e}")

        elif row['DROP'] == 0:
            # Rename file to remove run-0*_ entity
            try:
                # Create new filename by removing run-0*_ pattern
                dir_name = os.path.dirname(file_path)
                file_name = os.path.basename(file_path)
                new_file_name = re.sub(r'_run-0\d+_', '_', file_name)
                new_file_path = os.path.join(dir_name, new_file_name)

                # Check if destination already exists
                if os.path.exists(new_file_path):
                    print(f"Warning: Destination file already exists: {new_file_path}")
                    continue

                print(f"Renaming: {file_path} -> {new_file_path}")

                # Use git mv to rename the file
                subprocess.run(['git', 'mv', file_path, new_file_path], check=True)
                print(f"Successfully renamed to: {new_file_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error renaming file {file_path}: {e}")

def main():
    print("BIDS File Cleanup Script")
    print("=======================")

    # Get input paths
    bids_dir = input("Enter the path to the BIDS directory: ").strip()
    tsv_path = input("Enter the path to the TSV file: ").strip()

    # Validate inputs
    if not os.path.isdir(bids_dir):
        print(f"Error: BIDS directory not found: {bids_dir}")
        return

    if not os.path.isfile(tsv_path):
        print(f"Error: TSV file not found: {tsv_path}")
        return

    # Process the files
    process_files(bids_dir, tsv_path)
    print("Processing complete!")

if __name__ == "__main__":
    main()