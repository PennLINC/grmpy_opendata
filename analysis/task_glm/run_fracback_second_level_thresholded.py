#!/usr/bin/env python
"""Run second-level non-parametric GLM for n-back task across all subjects."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import templateflow.api as tflow
from scipy.stats import t as t_dist, norm
from nilearn.glm.second_level import non_parametric_inference
from nilearn.image import load_img, math_img, get_data, new_img_like

os.environ["TEMPLATEFLOW_HOME"] = "/cbica/projects/grmpy/templateflow"

CONTRAST_LABELS = [
    "twoBack",
    "zeroBack",
    "oneBack",
    "twoBackMinusZeroBack",
    "twoBackMinusOneBack",
    "oneBackMinusZeroBack",
]
MODEL_TYPES = ["rtdur", "nortdur"]

group_mask_img = load_img(
    tflow.get("MNI152NLin6Asym", resolution=2, desc="brain", suffix="mask")
)
bg_img = load_img(
    tflow.get("MNI152NLin6Asym", resolution=2, desc="brain", suffix="T1w")
)

ALPHA = 0.05
NEG_LOG10_ALPHA = -np.log10(ALPHA)

for model_type in MODEL_TYPES:
    firstlevel_dir = Path(
        f"/cbica/projects/grmpy/data/derivatives/fracback-{model_type}"
    )

    for contrast_label in CONTRAST_LABELS:
        print("\n====================================================")
        print(f"Running group model for contrast: {contrast_label}")
        print("====================================================\n")

        group_out_dir = Path(
            f"/cbica/projects/grmpy/data/derivatives/fracback-{model_type}/group-{contrast_label}"
        )
        group_out_dir.mkdir(exist_ok=True, parents=True)

        print(f"MODEL TYPE: {model_type}")
        print(f"Reading first-level maps from: {firstlevel_dir}")
        print(f"Writing thresholded second-level outputs to: {group_out_dir}")

        pattern = (
            "sub-*/sub-*_task-nback_space-MNI152NLin6Asym_"
            f"contrast-{contrast_label}_stat-effect_statmap.nii.gz"
        )

        effect_maps = sorted(firstlevel_dir.glob(pattern))
        if len(effect_maps) == 0:
            raise RuntimeError(
                f"No first-level maps found for contrast '{contrast_label}' with pattern:\n  {pattern}"
            )

        print(f"Found {len(effect_maps)} maps before QC.")

        good_maps = []
        good_subs = []

        for p in effect_maps:
            img = load_img(p)
            data = img.get_fdata()

            if not np.isfinite(data).any():
                print(f"[DROP] {p} is all non-finite.")
                continue

            if np.nanstd(data) == 0:
                print(f"[DROP] {p} is constant/zero.")
                continue

            good_maps.append(p)
            good_subs.append(p.name.split("_")[0].replace("sub-", ""))

        effect_maps = good_maps
        subject_labels = good_subs

        print(f"Kept {len(effect_maps)} maps after QC.")

        if len(effect_maps) < 2:
            raise RuntimeError(
                f"Need at least 2 valid subjects for group model of {contrast_label} "
                f"(found {len(effect_maps)})."
            )

        design_matrix = pd.DataFrame(
            {"intercept": [1.0] * len(effect_maps)},
            index=subject_labels,
        )

        results = non_parametric_inference(
            second_level_input=effect_maps,
            design_matrix=design_matrix,
            second_level_contrast="intercept",
            mask=group_mask_img,
            model_intercept=False,
            n_perm=10000,
            two_sided_test=True,
            threshold=0.001,
            tfce=False,
            n_jobs=4,
            random_state=12345,
            verbose=1,
        )

        # Threshold t-map using voxelwise FWE-corrected permutation p-values
        thresholded_t_img = math_img(
            f"np.where(logp >= {NEG_LOG10_ALPHA}, t, 0)",
            t=results["t"],
            logp=results["logp_max_t"],
        )

        # Convert t-map to approximate z-map
        df = len(effect_maps) - design_matrix.shape[1]
        t_data = get_data(results["t"])
        p_one_sided = t_dist.sf(np.abs(t_data), df)
        z_data = np.sign(t_data) * norm.isf(p_one_sided)
        z_img = new_img_like(results["t"], z_data)

        # Threshold z-map using the same voxelwise FWE mask
        thresholded_z_img = math_img(
            f"np.where(logp >= {NEG_LOG10_ALPHA}, z, 0)",
            z=z_img,
            logp=results["logp_max_t"],
        )

        contrast_out = contrast_label.lower()

        thresholded_t_img.to_filename(
            group_out_dir
            / f"contrast-{contrast_out}_stat-t_desc-thresholded_statmap.nii.gz"
        )

        thresholded_z_img.to_filename(
            group_out_dir
            / f"contrast-{contrast_out}_stat-z_desc-thresholded_statmap.nii.gz"
        )

        print(f"\nSaved thresholded t-map and z-map to:\n  {group_out_dir}\n")

print("\nDone.\n")
