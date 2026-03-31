"""Create group mean ALFF/ReHo dscalars and surface plots."""

import os
import re
from glob import glob

import matplotlib as mpl
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pandas as pd
from brainmontage import create_montage_figure
from brainmontage.brainmontage import clear_cache


def normalize_acq(acq):
    if pd.isna(acq):
        return None
    acq = str(acq).replace("acq-", "")
    acq = re.split(r"VARIANT", acq, maxsplit=1)[0]
    return acq.strip()


def get_entities(fname):
    entities = {}
    for part in fname.split("_"):
        if "-" in part:
            key, value = part.split("-", 1)
            entities[key] = value.replace(".nii.gz", "").replace(".nii", "")
    return entities


def get_plot_lims(metric, ciftidata):
    ciftidata = ciftidata[np.isfinite(ciftidata)]
    if metric == "alff":
        low, high = np.nanpercentile(ciftidata, [0.5, 99.5])
    elif metric == "reho":
        low = 0.4
        high = np.nanmax(ciftidata)
        if high <= low:
            low, high = np.nanpercentile(ciftidata, [0.5, 99.5])
    return low, high


if __name__ == "__main__":
    in_dir = "/cbica/projects/grmpy/data/derivatives/xcp-d"
    if not os.path.exists(in_dir):
        in_dir = "/cbica/projects/grmpy/data/derivatives/xcpd"

    scalar_out_dir = "/cbica/projects/grmpy/code/analysis/group_scalars"
    plot_out_dir = "/cbica/projects/grmpy/code/analysis/plots"
    os.makedirs(scalar_out_dir, exist_ok=True)
    os.makedirs(plot_out_dir, exist_ok=True)

    excluded_scans = pd.read_csv(
        "/cbica/projects/grmpy/code/curation/06_QC/data/final_qc/fmri_qc.csv"
    )
    excluded_scans["acq_norm"] = excluded_scans["acq"].map(normalize_acq)
    excluded_scans = set(
        excluded_scans.loc[
            excluded_scans["qc_determination"].astype(str).str.strip().eq("fail"),
            ["participant_id", "session_id", "task", "acq_norm"],
        ].itertuples(index=False, name=None)
    )
    print(f"Total excluded scans: {len(excluded_scans)}")

    patterns = {
        "alff": "sub-*/ses-*/func/*task-rest*acq-{acq}*space-fsLR_den-91k_stat-alff_boldmap.dscalar.nii",
        "reho": "sub-*/ses-*/func/*task-rest*acq-{acq}*space-fsLR_den-91k_stat-reho_boldmap.dscalar.nii",
    }

    for metric, search_patterns in patterns.items():
        for acq in ["singleband", "multiband"]:
            # Get all scalar maps
            scalar_maps = []
            for pattern in search_patterns:
                scalar_maps.extend(glob(os.path.join(in_dir, pattern.format(acq=acq))))
            scalar_maps = sorted(set(scalar_maps))
            print(f"Total {metric} {acq} maps found: {len(scalar_maps)}")

            scalar_maps = [
                f
                for f in scalar_maps
                if (
                    os.path.normpath(f).split(os.sep)[-4],
                    os.path.normpath(f).split(os.sep)[-3],
                    get_entities(os.path.basename(f)).get("task"),
                    normalize_acq(get_entities(os.path.basename(f)).get("acq")),
                )
                not in excluded_scans
            ]
            print(f"Total {metric} {acq} maps after exclusion: {len(scalar_maps)}")

            arrs = [
                np.asarray(nib.load(scalar_map).get_fdata(), dtype=np.float32)
                for scalar_map in scalar_maps
            ]
            arr_3d = np.stack(arrs, axis=0)
            mean_arr = np.nanmean(arr_3d, axis=0).astype(np.float32)
            print(f"{metric} {acq} array shape: {arr_3d.shape}")

            out_file = os.path.join(
                scalar_out_dir,
                f"group-{metric}_task-rest_acq-{acq}_space-fsLR_den-91k_stat-mean.dscalar.nii",
            )
            ref_img = nib.load(scalar_maps[0])
            out_img = nib.Cifti2Image(
                mean_arr,
                header=ref_img.header,
                nifti_header=ref_img.nifti_header,
            )
            nib.save(out_img, out_file)
            print(f"Saved {out_file}")

            # --- Plotting settings ---
            # save out text as text
            import matplotlib as mpl

            mpl.rcParams["pdf.fonttype"] = 42  # keep text as TrueType
            mpl.rcParams["ps.fonttype"] = 42
            mpl.rcParams["svg.fonttype"] = "none"

            ciftidata = np.asarray(nib.load(out_file).get_fdata(), dtype=np.float32)[
                0, :
            ]
            ciftidata[ciftidata == 0] = np.nan
            low, high = get_plot_lims(metric, ciftidata)

            clear_cache("facemap")
            create_montage_figure(
                roivals=ciftidata,
                atlasname="cifti91k",
                colormap="turbo",
                clim=[low, high],
                add_colorbar=False,
                upscale_factor=2,
                viewnames=["lateral", "medial"],
                face_mode="best",
                outputimagefile=os.path.join(
                    plot_out_dir, f"{os.path.basename(out_file)}_montage.pdf"
                ),
            )

            fig, ax = plt.subplots(figsize=(0.4, 4))
            norm = mpl.colors.Normalize(vmin=low, vmax=high)
            cb = mpl.colorbar.ColorbarBase(
                ax, cmap=plt.get_cmap("turbo"), norm=norm, orientation="vertical"
            )
            cb.set_ticks([low, (low + high) / 2, high])
            cb.set_ticklabels([f"{low:.2f}", f"{(low + high) / 2:.2f}", f"{high:.2f}"])
            cb.ax.tick_params(labelsize=10)
            cb.set_label(metric, fontsize=12)
            fig.savefig(
                os.path.join(
                    plot_out_dir,
                    os.path.basename(out_file).replace(".dscalar.nii", "_colorbar.pdf"),
                ),
                format="pdf",
                bbox_inches="tight",
            )
            plt.close(fig)
