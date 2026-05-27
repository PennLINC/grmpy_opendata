######Create statistical null
import os
from neuromaps import datasets, images, nulls, resampling, transforms
from netneurotools import datasets as nntdata
from neuromaps.parcellate import Parcellater
from neuromaps.images import dlabel_to_gifti
from neuromaps import stats
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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
