"""Plot CBF maps from ASLPrep."""

import os
from glob import glob

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import templateflow.api as tflow
import pandas as pd
from nilearn import image, maskers, plotting


if __name__ == "__main__":
    in_dir = "/cbica/projects/grmpy/data/derivatives/aslprep/"
    out_dir = "/cbica/projects/grmpy/code/analysis/plots"
    template = tflow.get(
        "MNI152NLin6Asym",
        resolution="01",
        desc="brain",
        suffix="T1w",
        extension="nii.gz",
    )
    mask = tflow.get(
        "MNI152NLin6Asym",
        resolution="01",
        desc="brain",
        suffix="mask",
        extension="nii.gz",
    )

    patterns = {
        "ASLPrep CBF": "sub-*/ses-*/perf/*_space-MNI152NLin6Asym_cbf.nii.gz",
        "BASIL ATT": "sub-*/ses-*/perf/*_space-MNI152NLin6Asym_desc-basil_att.nii.gz",
        "BASIL CBF": "sub-*/ses-*/perf/*_space-MNI152NLin6Asym_desc-basil_cbf.nii.gz",
        "BASIL GM CBF": "sub-*/ses-*/perf/*_space-MNI152NLin6Asym_desc-basilGM_cbf.nii.gz",
        "BASIL WM CBF": "sub-*/ses-*/perf/*_space-MNI152NLin6Asym_desc-basilWM_cbf.nii.gz",
    }
    excluded_scans = pd.read_csv(
        "/cbica/projects/grmpy/code/curation/06_QC/data/final_qc/asl_qc.csv"
    )
    excluded_scans = set(
        excluded_scans.loc[
            excluded_scans["qc_determination"].astype(str).str.strip().eq("fail"),
            ["participant_id", "session_id"],
        ].itertuples(index=False, name=None)
    )
    for title, pattern in patterns.items():
        # Get all scalar maps
        scalar_maps = sorted(glob(os.path.join(in_dir, pattern)))
        scalar_maps = [
            f
            for f in scalar_maps
            if tuple(os.path.normpath(f).split(os.sep)[-4:-2]) not in excluded_scans
        ]
        print(f"{title}: {len(scalar_maps)}")

        masker = maskers.NiftiMasker(mask, resampling_target="data")
        mean_img = image.mean_img(scalar_maps, copy_header=True)
        mean_img = masker.inverse_transform(masker.fit_transform(mean_img))
        sd_img = image.math_img("np.std(img, axis=3)", img=scalar_maps)
        sd_img = masker.inverse_transform(masker.transform(sd_img))

        # --- Plotting settings ---
        # save out text as text
        import matplotlib as mpl

        mpl.rcParams["pdf.fonttype"] = 42  # keep text as TrueType
        mpl.rcParams["ps.fonttype"] = 42
        mpl.rcParams["svg.fonttype"] = "none"

        # Plot mean and SD
        fig, axs = plt.subplots(2, 1, figsize=(10, 5))
        vmax0 = np.round(np.percentile(mean_img.get_fdata(), 98))
        plotting.plot_stat_map(
            mean_img,
            bg_img=template,
            display_mode="z",
            cut_coords=[-30, -15, 0, 15, 30, 45, 60],
            axes=axs[0],
            figure=fig,
            symmetric_cbar=False,
            vmin=0,
            vmax=vmax0,
            cmap="viridis",
            annotate=False,
            black_bg=False,
            resampling_interpolation="nearest",
            colorbar=False,
        )
        vmax1 = np.round(np.percentile(sd_img.get_fdata(), 98))
        plotting.plot_stat_map(
            sd_img,
            bg_img=template,
            display_mode="z",
            cut_coords=[-30, -15, 0, 15, 30, 45, 60],
            axes=axs[1],
            figure=fig,
            symmetric_cbar=False,
            vmin=0,
            vmax=vmax1,
            cmap="viridis",
            annotate=False,
            black_bg=False,
            resampling_interpolation="nearest",
            colorbar=False,
        )
        # fig.suptitle(title)
        fig.savefig(
            os.path.join(out_dir, f"aslprep_{title.replace(' ', '_')}.pdf"),
            bbox_inches="tight",
        )
        plt.close()

        # Plot the colorbars
        fig, axs = plt.subplots(2, 1, figsize=(10, 1.5))
        cmap = mpl.cm.viridis

        norm = mpl.colors.Normalize(vmin=0, vmax=vmax0)
        cbar = fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
            cax=axs[0],
            orientation="horizontal",
        )
        cbar.set_ticks([0, np.mean([0, vmax0]), vmax0])

        norm = mpl.colors.Normalize(vmin=0, vmax=vmax1)
        cbar = fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
            cax=axs[1],
            orientation="horizontal",
        )
        cbar.set_ticks([0, np.mean([0, vmax1]), vmax1])

        fig.tight_layout()
        fig.savefig(
            os.path.join(out_dir, f"aslprep_{title.replace(' ', '_')}_colorbar.pdf"),
            bbox_inches="tight",
        )
        plt.close()
