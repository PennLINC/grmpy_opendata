#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import re


def update_asl_json(json_path):
    """Updates metadata in an ASL JSON file."""
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        updated = False

        # Update TotalAcquiredPairs
        if "NumVolumes" in data:
            total_acquired_pairs = data["NumVolumes"] / 2
            if data.get("TotalAcquiredPairs") != total_acquired_pairs:
                data["TotalAcquiredPairs"] = total_acquired_pairs
                updated = True
        else:
            print(
                f"Warning: 'NumVolumes' not found in {json_path}. Cannot calculate 'TotalAcquiredPairs'."
            )

        # Update RepetitionTimePreparation
        if "RepetitionTime" in data:
            if data.get("RepetitionTimePreparation") != data["RepetitionTime"]:
                data["RepetitionTimePreparation"] = data["RepetitionTime"]
                updated = True
        else:
            print(
                f"Warning: 'RepetitionTime' not found in {json_path}. Cannot set 'RepetitionTimePreparation'."
            )

        # Update AcquisitionVoxelSize
        if all(k in data for k in ("VoxelSizeDim1", "VoxelSizeDim2", "VoxelSizeDim3")):
            acq_voxel_size = [
                data["VoxelSizeDim1"],
                data["VoxelSizeDim2"],
                data["VoxelSizeDim3"],
            ]
            if data.get("AcquisitionVoxelSize") != acq_voxel_size:
                data["AcquisitionVoxelSize"] = acq_voxel_size
                updated = True
        else:
            print(
                f"Warning: VoxelSizeDim keys not found in {json_path}. Cannot set 'AcquisitionVoxelSize'."
            )

        if updated:
            with open(json_path, "w") as f:
                json.dump(data, f, sort_keys=True, indent=4)
            print(f"Updated: {json_path}")
        # else:
        # print(f"No updates needed for: {json_path}")

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}")
    except Exception as e:
        print(f"Error processing {json_path}: {e}")


def update_m0_json(json_path):
    """Updates metadata in an M0 JSON file."""
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        updated = False

        # Update IntendedFor
        if "IntendedFor" in data:
            original_intended_for = data["IntendedFor"]
            intended_for_list = None
            was_originally_list = False

            # Ensure IntendedFor is processed as a list
            if isinstance(original_intended_for, str):
                intended_for_list = [original_intended_for]
                was_originally_list = False
            elif isinstance(original_intended_for, list):
                intended_for_list = original_intended_for
                was_originally_list = True
            else:
                print(
                    f"Warning: 'IntendedFor' in {json_path} is neither string nor list. Skipping update."
                )

            # Process the list if it's valid
            if intended_for_list is not None:
                updated_intended_for = []
                path_changed = False
                for current_path in intended_for_list:
                    # Replace ses-* with ses-1
                    # Use a more specific regex to avoid accidental replacements
                    updated_path = re.sub(
                        r"ses-(?!1\b)[a-zA-Z0-9]+", "ses-1", current_path
                    )
                    updated_intended_for.append(updated_path)
                    if updated_path != current_path:
                        path_changed = True

                # Update only if a path changed or if it wasn't a list originally (to enforce list format)
                if path_changed or not was_originally_list:
                    # Always store as a list, even if only one entry
                    data["IntendedFor"] = updated_intended_for
                    updated = True

        else:
            print(f"Warning: 'IntendedFor' not found in {json_path}. Skipping update.")

        # Update RepetitionTimePreparation
        if "RepetitionTime" in data:
            if data.get("RepetitionTimePreparation") != data["RepetitionTime"]:
                data["RepetitionTimePreparation"] = data["RepetitionTime"]
                updated = True
        else:
            print(
                f"Warning: 'RepetitionTime' not found in {json_path}. Cannot set 'RepetitionTimePreparation'."
            )

        # Update AcquisitionVoxelSize
        if all(k in data for k in ("VoxelSizeDim1", "VoxelSizeDim2", "VoxelSizeDim3")):
            acq_voxel_size = [
                data["VoxelSizeDim1"],
                data["VoxelSizeDim2"],
                data["VoxelSizeDim3"],
            ]
            if data.get("AcquisitionVoxelSize") != acq_voxel_size:
                data["AcquisitionVoxelSize"] = acq_voxel_size
                updated = True
        else:
            print(
                f"Warning: VoxelSizeDim keys not found in {json_path}. Cannot set 'AcquisitionVoxelSize'."
            )

        if updated:
            with open(json_path, "w") as f:
                # Ensure indent is 4 spaces as commonly used in BIDS
                json.dump(data, f, sort_keys=True, indent=4)
            print(f"Updated: {json_path}")
        # else:
        # print(f"No updates needed for: {json_path}")

    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {json_path}")
    except Exception as e:
        print(f"Error processing {json_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Update ASL and M0 JSON metadata in a BIDS directory."
    )
    parser.add_argument("bids_dir", type=str, help="Path to the BIDS directory.")
    args = parser.parse_args()

    bids_path = Path(args.bids_dir)

    if not bids_path.is_dir():
        print(f"Error: BIDS directory not found at {args.bids_dir}")
        return

    # Find all subject directories (sub-*)
    subject_dirs = [
        d for d in bids_path.iterdir() if d.is_dir() and d.name.startswith("sub-")
    ]

    for subj_dir in subject_dirs:
        perf_dir = subj_dir / "ses-1" / "perf"
        if perf_dir.is_dir():
            print(f"Processing: {perf_dir}")

            # Process ASL JSON files
            for asl_json_path in perf_dir.glob("*_asl.json"):
                update_asl_json(asl_json_path)

            # Process M0 JSON files
            for m0_json_path in perf_dir.glob("*_m0scan.json"):
                update_m0_json(m0_json_path)
        # else:
        # print(f"Skipping {subj_dir.name}: No ses-1/perf directory found.")


if __name__ == "__main__":
    main()
