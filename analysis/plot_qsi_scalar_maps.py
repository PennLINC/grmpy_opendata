"""Plot scalar maps from QSIRecon."""

import os
from glob import glob

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import templateflow.api as tflow
import pandas as pd
from nilearn import image, maskers, plotting


if __name__ == "__main__":
    in_dir = "/cbica/projects/grmpy/data/derivatives/qsirecon/derivatives"
    out_dir = "/cbica/projects/grmpy/code/analysis/plots"
    template = tflow.get(
        "MNI152NLin2009cAsym",
        resolution="01",
        desc="brain",
        suffix="T1w",
        extension="nii.gz",
    )
    mask = tflow.get(
        "MNI152NLin2009cAsym",
        resolution="01",
        desc="brain",
        suffix="mask",
        extension="nii.gz",
    )

    excluded_scans = pd.read_csv(
        "/cbica/projects/grmpy/code/curation/06_QC/data/final_qc/diffusion_qc.csv"
    )  # load csv
    excluded_scans = set(
        excluded_scans.loc[
            excluded_scans["qc_determination_scalar_maps"]
            .astype(str)
            .str.strip()
            .eq("fail"),
            ["participant_id", "session_id"],
        ].itertuples(index=False, name=None)
    )
    print(f"Total excluded scans: {len(excluded_scans)}")

    patterns = {
        "DSIStudio Tensor FA": "qsirecon-DSIStudio/sub-*/ses-*/dwi/*_space-MNI152NLin2009cAsym_model-tensor_param-fa_dwimap.nii.gz",
        "DSIStudio GQI GFA": "qsirecon-DSIStudio/sub-*/ses-*/dwi/*_space-MNI152NLin2009cAsym_model-gqi_param-gfa_dwimap.nii.gz",
        "NODDI ICVF": "qsirecon-NODDI/sub-*/ses-*/dwi/*_space-MNI152NLin2009cAsym_model-noddi_param-icvf_dwimap.nii.gz",
        "MAPMRI RTAP": "qsirecon-TORTOISE_model-MAPMRI/sub-*/ses-*/dwi/*_space-MNI152NLin2009cAsym_model-mapmri_param-rtap_dwimap.nii.gz",
        "DKI MK": "qsirecon-DIPYDKI/sub-*/ses-*/dwi/*_space-MNI152NLin2009cAsym_model-dki_param-mk_dwimap.nii.gz",
    }
    for title, pattern in patterns.items():
        # Get all scalar maps
        scalar_maps = sorted(glob(os.path.join(in_dir, pattern)))
        print(f"Total {title} maps: {len(scalar_maps)}")
        scalar_maps = [
            f
            for f in scalar_maps
            if tuple(os.path.normpath(f).split(os.sep)[-4:-2]) not in excluded_scans
        ]
        print(f"Total {title} maps after exclusion: {len(scalar_maps)}")

        mean_img = image.mean_img(scalar_maps, copy_header=True)
        sd_img = image.math_img("np.std(img, axis=3)", img=scalar_maps)

        # Mask out non-brain voxels
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
        vmax0 = np.round(np.percentile(mean_img.get_fdata(), 98), 2)
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
        vmax1 = np.round(np.percentile(sd_img.get_fdata(), 98), 2)
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
            os.path.join(out_dir, f"QSIRecon_{title.replace(' ', '_')}.pdf"),
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
            os.path.join(out_dir, f"QSIRecon_{title.replace(' ', '_')}_colorbar.pdf"),
            bbox_inches="tight",
        )
        plt.close()
