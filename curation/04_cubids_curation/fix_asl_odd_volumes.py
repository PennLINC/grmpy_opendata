#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Optional

import nibabel as nib
import numpy as np


def get_num_volumes_from_json(json_path: Path) -> Optional[int]:
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        if "NumVolumes" in data and isinstance(data["NumVolumes"], (int, float)):
            return int(data["NumVolumes"])
        # Fallback: try to infer from aslcontext if present
        tsv_path = json_path.with_name(
            json_path.name.replace("_asl.json", "_aslcontext.tsv")
        )
        if tsv_path.exists():
            with open(tsv_path, "r") as f:
                lines = [ln.strip() for ln in f.readlines() if ln.strip()]
            # first line is header
            if len(lines) >= 2:
                return len(lines) - 1
    except Exception as exc:
        print(f"Error reading {json_path}: {exc}")
    return None


def save_trimmed_last_volume(nifti_path: Path, out_path: Optional[Path] = None) -> int:
    img = nib.load(str(nifti_path))
    data = img.get_fdata()

    # Ensure 4D
    if data.ndim != 4 or data.shape[3] < 1:
        raise ValueError(
            f"Expected 4D ASL image, got shape {data.shape} for {nifti_path}"
        )

    num_volumes = data.shape[3]
    trimmed_data = data[..., : num_volumes - 1]

    new_img = nib.Nifti1Image(trimmed_data, img.affine, img.header)
    # Update header dim to reflect new number of volumes
    new_img.header.set_data_shape(trimmed_data.shape)

    target_path = out_path if out_path is not None else nifti_path
    nib.save(new_img, str(target_path))
    return num_volumes - 1


def rewrite_aslcontext(tsv_path: Path, num_volumes: int, first: str = "label") -> None:
    with open(tsv_path, "w") as f:
        f.write("volume_type\n")
        current = first
        for _ in range(num_volumes):
            f.write(f"{current}\n")
            current = "control" if current == "label" else "label"


def update_asl_json(json_path: Path, num_volumes: int) -> None:
    with open(json_path, "r") as f:
        data = json.load(f)

    data["NumVolumes"] = int(num_volumes)
    # TotalAcquiredPairs is NumVolumes/2 if alternating label/control
    data["TotalAcquiredPairs"] = float(num_volumes) / 2.0

    with open(json_path, "w") as f:
        json.dump(data, f, sort_keys=True, indent=4)


def process_asl(
    asl_nii_path: Path, first_volume_type: str = "label", dry_run: bool = False
) -> None:
    json_path = asl_nii_path.with_suffix("").with_suffix("")  # handle .nii.gz
    json_path = Path(str(json_path) + "_asl.json")
    if not json_path.exists():
        # Try straightforward replacement of suffix
        json_guess = asl_nii_path.name.replace("_asl.nii.gz", "_asl.json")
        candidate = asl_nii_path.parent / json_guess
        if candidate.exists():
            json_path = candidate
        else:
            print(f"Skipping {asl_nii_path}: missing sidecar JSON")
            return

    tsv_path = Path(str(json_path).replace("_asl.json", "_aslcontext.tsv"))

    num_volumes = get_num_volumes_from_json(json_path)

    if num_volumes is None:
        # Fall back to reading from nifti
        try:
            img = nib.load(str(asl_nii_path))
            shape = img.shape
            if len(shape) == 4:
                num_volumes = shape[3]
            else:
                print(f"Skipping {asl_nii_path}: non-4D image shape {shape}")
                return
        except Exception as exc:
            print(f"Skipping {asl_nii_path}: cannot infer volumes ({exc})")
            return

    is_odd = (num_volumes % 2) == 1

    if is_odd:
        print(f"Odd volume count detected ({num_volumes}) for {asl_nii_path}")
        if not dry_run:
            new_num = save_trimmed_last_volume(asl_nii_path)
            update_asl_json(json_path, new_num)
            rewrite_aslcontext(tsv_path, new_num, first=first_volume_type)
            print(f"Trimmed last volume. New count: {new_num}")
        else:
            print(f"[DRY-RUN] Would trim last volume for {asl_nii_path}")
    else:
        print(
            f"Even volume count ({num_volumes}) for {asl_nii_path}. Ensuring aslcontext matches."
        )
        if not dry_run:
            # Ensure aslcontext exists and matches length
            rewrite_aslcontext(tsv_path, num_volumes, first=first_volume_type)
            # Ensure JSON has consistent values
            update_asl_json(json_path, num_volumes)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Trim odd final volume from ASL series and regenerate aslcontext.tsv and sidecar JSON."
        )
    )
    parser.add_argument("bids_dir", type=str, help="Path to the BIDS directory")
    parser.add_argument(
        "--first",
        choices=["label", "control"],
        default="label",
        help="First volume type in the alternating sequence",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write any changes; just report actions",
    )
    args = parser.parse_args()

    bids_path = Path(args.bids_dir)
    if not bids_path.exists():
        print(f"BIDS directory not found: {bids_path}")
        return

    # Traverse all subjects and sessions
    subject_dirs = [
        d for d in bids_path.iterdir() if d.is_dir() and d.name.startswith("sub-")
    ]
    for subj in subject_dirs:
        # Prefer all sessions if present; fall back to direct perf under subject if used
        ses_dirs = [
            d for d in subj.iterdir() if d.is_dir() and d.name.startswith("ses-")
        ]
        if not ses_dirs:
            ses_dirs = [subj]

        for ses in ses_dirs:
            perf_dir = ses / "perf"
            if not perf_dir.is_dir():
                continue

            for asl_nii in sorted(perf_dir.glob("*_asl.nii.gz")):
                process_asl(asl_nii, first_volume_type=args.first, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
