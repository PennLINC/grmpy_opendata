######Create statistical null
import os
from neuromaps import datasets, nulls, resampling
from netneurotools import datasets as nntdata
from neuromaps.parcellate import Parcellater
from neuromaps.images import dlabel_to_gifti, load_gifti
from neuromaps import stats
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from nilearn import plotting

grmpy = "/cbica/projects/grmpy/data/derivatives/fracback-rtdur/group-twoBackMinusZeroBack/contrast-twobackminuszeroback_stat-z_statmap.nii.gz"
pnc = "/cbica/projects/grmpy/pnc/group_zmap_MNI.nii.gz"
grmpy, pnc = resampling.resample_images(
    src=grmpy,
    trg=pnc,
    resampling="transform_to_alt",
    alt_spec=("fsLR", "32k"),
    src_space="MNI152",
    trg_space="MNI152",
)


schaefer = nntdata.fetch_schaefer2018("fslr32k")["400Parcels7Networks"]
parcimg = dlabel_to_gifti(schaefer)
parc = Parcellater(parcimg, "fsLR")
fslr = datasets.fetch_fslr(density="32k")

grmpy_parcellated_data = parc.fit_transform(grmpy, "fsLR")
pnc_parcellated_data = parc.fit_transform(pnc, "fsLR")

rotated = nulls.alexander_bloch(
    grmpy_parcellated_data,
    atlas="fsLR",
    density="32k",
    n_perm=10000,
    seed=1234,
    parcellation=parcimg,
)
print(rotated.shape)

######Compare images
corr, pval = stats.compare_images(
    grmpy_parcellated_data, pnc_parcellated_data, nulls=rotated
)
print(f"r = {corr:.3f}, p = {pval:.3f}")


######Plot as scatterplot
x = grmpy_parcellated_data
y = pnc_parcellated_data

mask = np.isfinite(x) & np.isfinite(y)
x = x[mask]
y = y[mask]

plt.figure(figsize=(4, 4))
print("x/y n:", x.size, y.size)

sns.regplot(
    x=x,
    y=y,
    scatter_kws={
        "s": 12,
        "alpha": 0.6,
        "color": "royalblue",
        "edgecolor": "none",
    },
    line_kws={
        "linewidth": 2,
    },
    ci=None,
)

plt.title(f"r = {corr:.3f}, p(spin) = {pval:.4f}")
plt.xlabel("grmpy")
plt.ylabel("pnc")
plt.tight_layout()

out_dir = "/cbica/projects/grmpy/code/analysis/task_glm/figures"
os.makedirs(out_dir, exist_ok=True)

plt.savefig(
    os.path.join(out_dir, "grmpy_pnc_scatterplot.pdf"),
    bbox_inches="tight",
    transparent=True,
)
plt.close()


######Parcellated surface figures
def flatten_parcellated(arr):
    arr = np.asarray(arr).squeeze()
    if arr.ndim != 1:
        arr = arr.reshape(-1)
    return arr


def parcels_to_vertices(parcel_values, parcimg):
    parcel_values = flatten_parcellated(parcel_values)

    lh_labels = np.asarray(load_gifti(parcimg[0]).agg_data()).squeeze().astype(int)
    rh_labels = np.asarray(load_gifti(parcimg[1]).agg_data()).squeeze().astype(int)

    all_ids = np.unique(np.concatenate([lh_labels, rh_labels]))
    all_ids = all_ids[all_ids != 0]
    all_ids = np.sort(all_ids)

    if len(all_ids) != len(parcel_values):
        raise ValueError(
            f"Number of parcel IDs on surface ({len(all_ids)}) does not match "
            f"number of parcel values ({len(parcel_values)})."
        )

    id_to_value = {pid: val for pid, val in zip(all_ids, parcel_values)}

    lh_data = np.full(lh_labels.shape, np.nan, dtype=float)
    rh_data = np.full(rh_labels.shape, np.nan, dtype=float)

    for pid, val in id_to_value.items():
        lh_data[lh_labels == pid] = val
        rh_data[rh_labels == pid] = val

    return lh_data, rh_data


def plot_parcellated_map(lh_data, rh_data, title, out_file, cmap="cold_hot"):
    fig = plt.figure(figsize=(12, 8))

    ax1 = fig.add_subplot(2, 2, 1, projection="3d")
    plotting.plot_surf_stat_map(
        surf_mesh=fslr["inflated"][0],
        stat_map=lh_data,
        hemi="left",
        view="lateral",
        bg_map=fslr["sulc"][0],
        colorbar=True,
        cmap=cmap,
        title=f"{title} (LH lateral)",
        axes=ax1,
        darkness=None,
    )

    ax2 = fig.add_subplot(2, 2, 2, projection="3d")
    plotting.plot_surf_stat_map(
        surf_mesh=fslr["inflated"][1],
        stat_map=rh_data,
        hemi="right",
        view="lateral",
        bg_map=fslr["sulc"][1],
        colorbar=False,
        cmap=cmap,
        title=f"{title} (RH lateral)",
        axes=ax2,
        darkness=None,
    )

    ax3 = fig.add_subplot(2, 2, 3, projection="3d")
    plotting.plot_surf_stat_map(
        surf_mesh=fslr["inflated"][0],
        stat_map=lh_data,
        hemi="left",
        view="medial",
        bg_map=fslr["sulc"][0],
        colorbar=False,
        cmap=cmap,
        title=f"{title} (LH medial)",
        axes=ax3,
        darkness=None,
    )

    ax4 = fig.add_subplot(2, 2, 4, projection="3d")
    plotting.plot_surf_stat_map(
        surf_mesh=fslr["inflated"][1],
        stat_map=rh_data,
        hemi="right",
        view="medial",
        bg_map=fslr["sulc"][1],
        colorbar=False,
        cmap=cmap,
        title=f"{title} (RH medial)",
        axes=ax4,
        darkness=None,
    )

    plt.savefig(
        out_file, bbox_inches="tight", dpi=300, facecolor="white", transparent=False
    )
    plt.close(fig)


for name, parcel_data, title in [
    ("grmpy", grmpy_parcellated_data, "GRMPY 2-back > 0-back (parcellated)"),
    ("pnc", pnc_parcellated_data, "PNC 2-back > 0-back (parcellated)"),
]:
    lh_data, rh_data = parcels_to_vertices(parcel_data, parcimg)
    fig_file = os.path.join(out_dir, f"{name}_fsLR32k_Schaefer400_surface.pdf")
    plot_parcellated_map(lh_data, rh_data, title, fig_file)
    print(f"Saved parcellated surface figure: {fig_file}")
