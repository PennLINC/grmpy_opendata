#!/usr/bin/env python
"""Run second-level GLM for n-back task across all subjects."""

from pathlib import Path

import numpy as np
import pandas as pd
from nilearn.glm.second_level import SecondLevelModel
from nilearn.image import load_img
from nilearn.interfaces.bids import save_glm_to_bids


CONTRAST_LABELS = [
    "twoBack",
    "oneBack",
    "zeroBack",
    "twoBackMinusZeroBack",
    "twoBackMinusOneBack",
    "oneBackMinusZeroBack",
]
MODEL_TYPES = ["rtdur", "nortdur"]
group_mask_img = load_img(
    "/cbica/projects/grmpy/templateflow/"
    "tpl-MNI152NLin6Asym/tpl-MNI152NLin6Asym_res-02_desc-brain_mask.nii.gz"
)
bg_img = load_img(
    "/cbica/projects/grmpy/templateflow/"
    "tpl-MNI152NLin6Asym/tpl-MNI152NLin6Asym_res-02_desc-brain_T1w.nii.gz"
)

for model_type in MODEL_TYPES:
    firstlevel_dir = Path(
        f"/cbica/projects/grmpy/analysis/task_glm/first-level/results/fracback-{model_type}"
    )
    for contrast_label in CONTRAST_LABELS:
        print("\n====================================================")
        print(f"Running group model for contrast: {contrast_label}")
        print("====================================================\n")

        group_out_dir = Path(
            f"/cbica/projects/grmpy/analysis/task_glm/second-level/fracback-{model_type}/group-{contrast_label}"
        )
        group_out_dir.mkdir(exist_ok=True, parents=True)

        print(f"MODEL TYPE: {model_type}")
        print(f"Reading first-level maps from: {firstlevel_dir}")
        print(f"Writing second-level outputs to: {group_out_dir}")

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

        # ----- QC: drop maps that are all-nan or constant -----
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

        # Design matrix
        design_matrix = pd.DataFrame(
            {"intercept": [1.0] * len(effect_maps)},
            index=subject_labels,
        )

        # Fit second-level
        model = SecondLevelModel(mask_img=group_mask_img, minimize_memory=False)
        model = model.fit(effect_maps, design_matrix=design_matrix)

        # Save results
        contrasts = {contrast_label: "intercept"}

        save_glm_to_bids(
            model=model,
            contrasts=contrasts,
            out_dir=group_out_dir,
            threshold=0.001,  # <-- p-value threshold
            height_control="fpr",  # <-- interpret threshold as p
            cluster_threshold=10,
            bg_img=bg_img,
            two_sided=True,
        )

        print(f"\nSaved second-level outputs to:\n  {group_out_dir}\n")
