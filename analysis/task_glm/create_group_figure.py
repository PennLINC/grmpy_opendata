import os
from pathlib import Path
from nilearn import plotting
from nilearn.image import load_img
import templateflow.api as tflow

# Path to output directory
out_dir = Path("/cbica/projects/grmpy/code/analysis/task_glm/figures")

os.environ["TEMPLATEFLOW_HOME"] = "/cbica/projects/grmpy/templateflow"


bg_img = load_img(
    tflow.get("MNI152NLin6Asym", resolution=2, desc="brain", suffix="T1w")
)

MODEL_TYPES = ["fracback-nortdur", "fracback-rtdur"]

CONTRASTS = [
    {
        "contrast_dir": "group-twoBackMinusZeroBack",
        "stat_file": "contrast-twobackminuszeroback_stat-z_statmap.nii.gz",
        "title": "2-back > 0-back",
        "label": "twoBackMinusZeroBack",
    },
    {
        "contrast_dir": "group-twoBackMinusOneBack",
        "stat_file": "contrast-twobackminusoneback_stat-z_statmap.nii.gz",
        "title": "2-back > 1-back",
        "label": "twoBackMinusOneBack",
    },
    {
        "contrast_dir": "group-oneBackMinusZeroBack",
        "stat_file": "contrast-onebackminuszeroback_stat-z_statmap.nii.gz",
        "title": "1-back > 0-back",
        "label": "oneBackMinusZeroBack",
    },
    {
        "contrast_dir": "group-twoBack",
        "stat_file": "contrast-twoback_stat-z_statmap.nii.gz",
        "title": "2-back > baseline",
        "label": "twoBack",
    },
    {
        "contrast_dir": "group-oneBack",
        "stat_file": "contrast-oneback_stat-z_statmap.nii.gz",
        "title": "1-back > baseline",
        "label": "oneBack",
    },
    {
        "contrast_dir": "group-zeroBack",
        "stat_file": "contrast-zeroback_stat-z_statmap.nii.gz",
        "title": "0-back > baseline",
        "label": "zeroBack",
    },
]

for model_type in MODEL_TYPES:
    for contrast in CONTRASTS:
        group_zmap = (
            Path("/cbica/projects/grmpy/data/derivatives")
            / model_type
            / contrast["contrast_dir"]
            / "group"
            / contrast["stat_file"]
        )

        stat_img = load_img(group_zmap)

        model_label = "RTDur" if "rtdur" in model_type else "noRTDur"

        plotting.plot_stat_map(
            stat_img,
            bg_img=bg_img,
            display_mode="z",
            cut_coords=(-36, -20, -6, 6, 30, 52, 64),
            threshold=3.09,
            black_bg=False,
            title=f"{model_label}: {contrast['title']}",
            output_file=str(out_dir / f"{model_label}_{contrast['label']}_statmap.pdf"),
        )
