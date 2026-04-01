"""Create surface montage PDFs for XCP-D atlas files."""

import os
from glob import glob

import matplotlib as mpl
import nibabel as nib
import numpy as np
from brainmontage import create_montage_figure
from brainmontage.brainmontage import clear_cache


def get_input_dir():
    atlas_dir = "/cbica/projects/grmpy/data/derivatives/xcpd/atlases"
    if not os.path.exists(atlas_dir):
        raise FileNotFoundError(f"Could not find atlas directory: {atlas_dir}")
    return atlas_dir


def get_label_range(atlas_file):
    data = np.asarray(nib.load(atlas_file).get_fdata())
    finite_vals = data[np.isfinite(data)]
    finite_vals = finite_vals[finite_vals > 0]
    if finite_vals.size == 0:
        return None

    max_label = int(np.nanmax(finite_vals))
    if max_label < 1:
        return None
    return np.arange(max_label) + 1


if __name__ == "__main__":
    in_dir = get_input_dir()
    out_dir = "/cbica/projects/grmpy/code/analysis/plots"
    os.makedirs(out_dir, exist_ok=True)

    atlas_files = sorted(glob(os.path.join(in_dir, "atlas-*", "*.nii*")))
    atlas_files = [
        atlas_file
        for atlas_file in atlas_files
        if (
            atlas_file.endswith(".dlabel.nii")
            or atlas_file.endswith(".dscalar.nii")
            or atlas_file.endswith(".nii")
            or atlas_file.endswith(".nii.gz")
        )
        and "atlas-Gordon" not in atlas_file
        and "atlas-HCP" not in atlas_file
    ]
    print(f"Total atlas files found: {len(atlas_files)}")

    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["svg.fonttype"] = "none"

    for atlas_file in atlas_files:
        roivals = get_label_range(atlas_file)
        if roivals is None:
            print(f"Skipping {atlas_file}: no positive labels found")
            continue

        atlas_name = os.path.basename(atlas_file)
        if atlas_name.endswith(".nii.gz"):
            atlas_name = atlas_name[: -len(".nii.gz")]
        elif atlas_name.endswith(".nii"):
            atlas_name = atlas_name[: -len(".nii")]

        out_file = os.path.join(out_dir, f"{atlas_name}_montage.pdf")
        clear_cache("facemap")
        create_montage_figure(
            roivals=roivals,
            atlasname="cifti91k",
            subparcfile=atlas_file,
            viewnames=["lateral", "medial"],
            surftype="infl",
            clim=[0, int(np.nanmax(roivals))],
            colormap="random",
            face_mode="best",
            upscale_factor=2,
            add_colorbar=False,
            outputimagefile=out_file,
        )
        print(f"Saved {out_file}")
