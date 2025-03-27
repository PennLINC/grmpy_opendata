#!/usr/bin/env python3

import os
import shutil
import re
import glob
from pathlib import Path


def copy_and_rename_perfusion_data():
    # Source and destination base directories
    source_base = "/cbica/projects/grmpy/aslprep_proj_data"
    dest_base = "/cbica/projects/grmpy/data/bids_datalad"

    # Find all subject directories in the source
    subject_dirs = glob.glob(f"{source_base}/sub-*")

    for subject_dir in subject_dirs:
        # Extract subject ID
        subject_id = os.path.basename(subject_dir)

        # Since there's only 1 session directory per subject, we can simplify
        # Find the single session directory for this subject
        session_dirs = glob.glob(f"{subject_dir}/ses-*/perf")

        if not session_dirs:
            print(f"No perfusion data found for {subject_id}")
            continue

        # Use the first (and only) session directory
        perf_dir = session_dirs[0]

        # Create destination directory
        dest_dir = f"{dest_base}/{subject_id}/ses-1/perf"
        os.makedirs(dest_dir, exist_ok=True)

        # Find all files in the perfusion directory
        perf_files = glob.glob(f"{perf_dir}/*")

        for src_file in perf_files:
            filename = os.path.basename(src_file)

            # Replace the session entity with ses-1
            new_filename = re.sub(r"ses-\d+", "ses-1", filename)

            # Create the destination path
            dest_file = os.path.join(dest_dir, new_filename)

            # Copy the file
            shutil.copy2(src_file, dest_file)
            print(f"Copied: {src_file} -> {dest_file}")


if __name__ == "__main__":
    print("Starting perfusion data copy process...")
    copy_and_rename_perfusion_data()
    print("Perfusion data copy complete!")
