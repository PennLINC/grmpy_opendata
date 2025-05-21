#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path


def create_aslcontext_tsv(json_path, first_volume_type):
    """Creates an aslcontext.tsv file based on ASL JSON metadata."""
    try:
        # Read the ASL JSON file
        with open(json_path, "r") as f:
            data = json.load(f)

        # Check if NumVolumes exists
        if "NumVolumes" not in data:
            print(
                f"Warning: 'NumVolumes' not found in {json_path}. Cannot create aslcontext.tsv."
            )
            return

        num_volumes = int(data["NumVolumes"])

        # Create the corresponding aslcontext.tsv file path
        tsv_path = str(json_path).replace("_asl.json", "_aslcontext.tsv")

        # Create the aslcontext.tsv file
        with open(tsv_path, "w") as f:
            # Write header
            f.write("volume_type\n")

            # Write alternating volume types
            current_type = first_volume_type
            for i in range(num_volumes):
                f.write(f"{current_type}\n")
                # Toggle between label and control
                current_type = "control" if current_type == "label" else "label"

        print(f"Created: {tsv_path} with {num_volumes} volumes")

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}")
    except Exception as e:
        print(f"Error processing {json_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Create ASL context TSV files from ASL JSON metadata in a BIDS directory."
    )
    parser.add_argument("bids_dir", type=str, help="Path to the BIDS directory.")
    parser.add_argument(
        "first_volume_type",
        type=str,
        choices=["label", "control"],
        help="Specify whether 'label' or 'control' comes first in the sequence.",
    )
    args = parser.parse_args()

    bids_path = Path(args.bids_dir)
    first_volume_type = args.first_volume_type

    if not bids_path.is_dir():
        print(f"Error: BIDS directory not found at {args.bids_dir}")
        return

    # Find all subject directories (sub-*)
    subject_dirs = [
        d for d in bids_path.iterdir() if d.is_dir() and d.name.startswith("sub-")
    ]

    for subj_dir in subject_dirs:
        # Find all session directories in this subject
        session_dirs = [
            d for d in subj_dir.iterdir() if d.is_dir() and d.name.startswith("ses-")
        ]

        for ses_dir in session_dirs:
            perf_dir = ses_dir / "perf"
            if perf_dir.is_dir():
                print(f"Processing: {perf_dir}")

                # Process ASL JSON files
                for asl_json_path in perf_dir.glob("*_asl.json"):
                    create_aslcontext_tsv(asl_json_path, first_volume_type)
            else:
                print(f"Skipping {ses_dir}: No perf directory found.")


if __name__ == "__main__":
    main()
