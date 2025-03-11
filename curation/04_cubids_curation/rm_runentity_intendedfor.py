#!/usr/bin/env python3
import os
import json
import pandas as pd
import re
import subprocess
from pathlib import Path

def update_intended_for(bids_dir, old_path, new_path):
    """Update IntendedFor references in fieldmap JSON files"""
    # Extract subject ID from the path
    match = re.search(r'(/sub-[^/]+/)', old_path)
    if not match:
        print(f"Could not extract subject ID from path: {old_path}")
        return

    subject_id = match.group(1).strip('/')
    subject_path = match.group(1)
    fmap_dir = os.path.join(bids_dir, subject_path.lstrip('/'), 'ses-1/fmap')

    if not os.path.exists(fmap_dir):
        print(f"No fieldmap directory found for {subject_path}")
        return

    # Get relative paths for IntendedFor field (relative to subject directory)
    # Strip the subject directory prefix to match IntendedFor format
    old_rel_path = re.sub(f'^/?{subject_id}/', '', old_path.lstrip('/'))
    new_rel_path = re.sub(f'^/?{subject_id}/', '', new_path.lstrip('/'))

    # Extract the task and acquisition from the old path to help with matching
    task_acq_match = re.search(r'task-([^_]+)_acq-([^_]+)', old_rel_path)
    if task_acq_match:
        task = task_acq_match.group(1)
        acq = task_acq_match.group(2)
        run_pattern = f"task-{task}_acq-{acq}_run-\\d+_bold\\.nii\\.gz$"
    else:
        run_pattern = r"_run-\d+_bold\.nii\.gz$"

    print(f"Looking to replace paths matching: {run_pattern}")
    print(f"New path will be: {new_rel_path}")

    # Process each fieldmap JSON file
    for json_file in Path(fmap_dir).glob('*{magnitude1,magnitude2,phasediff}.json'):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Skip if no IntendedFor field
            if 'IntendedFor' not in data:
                continue

            # Check if any path in IntendedFor matches our pattern
            updated = False
            for i, path in enumerate(data['IntendedFor']):
                if re.search(run_pattern, path):
                    print(f"  Found match: {path}")
                    data['IntendedFor'][i] = new_rel_path
                    updated = True

            if updated:
                print(f"Updating IntendedFor in {json_file}")
                with open(json_file, 'w') as f:
                    json.dump(data, f, indent=2, sort_keys=True)

                # Add the updated JSON to git
                subprocess.run(['git', 'add', str(json_file)], check=True)
                print(f"Added updated fieldmap JSON to git: {json_file}")

        except Exception as e:
            print(f"Error updating {json_file}: {e}")

def process_files(bids_dir, tsv_path):
    # Target KeyParamGroup patterns
    target_patterns = [
        'datatype-func_run-02_suffix-bold_task-rest_acquisition-multiband__1',
        'datatype-func_run-02_suffix-bold_task-face_acquisition-singleband__1',
        'datatype-func_run-02_suffix-bold_task-fracback_acquisition-singleband__1'
    ]

    # Read the TSV file
    try:
        df = pd.read_csv(tsv_path, sep='\t')
    except Exception as e:
        print(f"Error reading TSV file: {e}")
        return

    # Check if required columns exist
    if 'KeyParamGroup' not in df.columns or 'FilePath' not in df.columns:
        print("Error: TSV file must contain 'KeyParamGroup' and 'FilePath' columns")
        return

    # Filter rows matching target patterns
    matching_rows = df[df['KeyParamGroup'].isin(target_patterns)]

    if matching_rows.empty:
        print("No matching rows found in the TSV file")
        return

    print(f"Found {len(matching_rows)} matching rows")

    # Process each matching row
    for _, row in matching_rows.iterrows():
        # Get the full file path
        file_path = os.path.join(bids_dir, row['FilePath'].lstrip('/'))

        # Get the JSON sidecar path
        json_path = re.sub(r'\.nii\.gz$', '.json', file_path)

        # Check if files exist
        if not os.path.exists(file_path):
            print(f"Warning: File not found: {file_path}")
            continue

        if not os.path.exists(json_path):
            print(f"Warning: JSON sidecar not found: {json_path}")
            continue

        # Create new filenames by removing run-0* entity
        dir_name = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        new_file_name = re.sub(r'_run-0\d+', '', file_name)
        new_file_path = os.path.join(dir_name, new_file_name)

        new_json_name = re.sub(r'_run-0\d+', '', os.path.basename(json_path))
        new_json_path = os.path.join(os.path.dirname(json_path), new_json_name)

        # Check if destination files already exist
        if os.path.exists(new_file_path):
            print(f"Warning: Destination file already exists: {new_file_path}")
            continue

        if os.path.exists(new_json_path):
            print(f"Warning: Destination JSON already exists: {new_json_path}")
            continue

        try:
            # Rename the main file
            print(f"Renaming: {file_path} -> {new_file_path}")
            subprocess.run(['git', 'mv', file_path, new_file_path], check=True)

            # Rename the JSON sidecar
            print(f"Renaming: {json_path} -> {new_json_path}")
            subprocess.run(['git', 'mv', json_path, new_json_path], check=True)

            # Update IntendedFor references in fieldmap JSONs
            update_intended_for(bids_dir, row['FilePath'], new_file_path.replace(bids_dir, ''))

            print(f"Successfully processed: {row['FilePath']}")

        except subprocess.CalledProcessError as e:
            print(f"Error processing {row['FilePath']}: {e}")

def main():
    print("BIDS IntendedFor Path Updater")
    print("=============================")

    # Get input paths
    bids_dir = input("Enter the path to the BIDS directory: ").strip()
    tsv_path = input("Enter the path to the files.tsv file: ").strip()

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