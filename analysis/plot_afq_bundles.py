# Plot reconstructed individual bundles for a few subjects

# This script is run locally, not on cubic computing cluster. The first step before running this script is to datalad get, unzip, and copy over the necessary derivatives from cubic to local.
# Necessary derivatives: "sub-{subid}_ses-{sesid}_space-ACPC_desc-preproc_T1w.nii.gz” from qsiprep_anat outputs and the brain mask from qsiprep_anat outputs: sub-{sub-id}_ses-{ses-id}_space-ACPC_desc-brain_mask.nii.gz
# Create a new environment: micromamba create --name dipy python=3.11 nibabel numpy dipy fury matplotlib
#   pip install pyAFQ
#   micromamba activate dipy
# After these initial steps, then you can run this script.


import gzip
import shutil
from pathlib import Path

import nibabel as nb
import numpy as np
from AFQ.viz.utils import PanelFigure
from dipy.io.streamline import load_tck
from dipy.tracking.streamline import transform_streamlines
from fury import actor, window
from matplotlib.cm import tab20


def lines_as_tubes(sl, line_width, **kwargs):
    line_actor = actor.line(sl, **kwargs)
    line_actor.GetProperty().SetRenderLinesAsTubes(True)
    line_actor.GetProperty().SetLineWidth(line_width)
    return line_actor


def get_bundle_data(data_root, subid, sesid, bundle_name, reference):
    """
    Tries to load a bundle. Returns a Dipy TCK object on success, or None if missing/broken.
    """
    try:
        dwi_path = data_root / f"sub-{subid}" / f"ses-{sesid}" / "dwi"
        bundle_path = (
            dwi_path
            / f"sub-{subid}_ses-{sesid}_acq-multiband_dir-AP_space-ACPC_model-gqi_bundle-{bundle_name}_streamlines.tck"
        )
        bundle_path_gz = bundle_path.with_suffix(".tck.gz")

        if bundle_path.exists():
            return load_tck(bundle_path, reference=reference)
        elif bundle_path_gz.exists():
            # Decompress once so subsequent runs are fast
            try:
                with gzip.open(bundle_path_gz, "rb") as f_in, open(
                    bundle_path, "wb"
                ) as f_out:
                    shutil.copyfileobj(f_in, f_out)
                return load_tck(bundle_path, reference=reference)
            except Exception as e:
                print(f"  ! Failed to decompress/load {bundle_name}: {e}")
                return None
        else:
            print(f"  - Missing {bundle_name} at {bundle_path_gz}")
            return None
    except Exception as e:
        print(f"  ! Error loading {bundle_name}: {e}")
        return None


def visualize_bundles(
    data_root, out_dir, subid, sesid, out_png, interactive=False, camera_positions=None
):
    dwi_path = data_root / f"sub-{subid}" / f"ses-{sesid}" / "dwi"
    dwi_base = f"sub-{subid}_ses-{sesid}_acq-multiband_dir-AP_space-ACPC"
    t1w_base = f"sub-{subid}_ses-{sesid}_space-ACPC"

    fa_file = dwi_path / f"{dwi_base}_model-tensor_param-fa_dwimap.nii.gz"
    if not fa_file.exists():
        print(f"Could not find FA image at {fa_file}")
        return

    fa_img = nb.load(fa_file)

    # Bundle plan (name -> color)
    color_arc = tab20.colors[18]
    color_cst = tab20.colors[2]
    color_ifof = tab20.colors[8]
    bundle_plan = [
        ("AssociationArcuateFasciculusL", color_arc),
        ("AssociationArcuateFasciculusR", color_arc),
        ("ProjectionBrainstemCorticospinalTractL", color_cst),
        ("ProjectionBrainstemCorticospinalTractR", color_cst),
        ("AssociationInferiorFrontoOccipitalFasciculusL", color_ifof),
        ("AssociationInferiorFrontoOccipitalFasciculusR", color_ifof),
    ]

    print("Loading bundles (skipping any that are missing or invalid)...")
    loaded = []
    for bname, bcolor in bundle_plan:
        tck = get_bundle_data(data_root, subid, sesid, bname, fa_img)
        if tck is None:
            continue
        # Ensure RASmm and transform to T1w space
        try:
            tck.to_rasmm()
        except Exception as e:
            print(f"  ! {bname}: failed to convert to RASmm: {e}")
            continue
        try:
            t1w_img = nb.load(dwi_path / f"{t1w_base}_desc-preproc_T1w.nii.gz")
        except Exception as e:
            print(f"Could not load T1w for transform: {e}")
            return
        inv_affine = np.linalg.inv(t1w_img.affine)
        try:
            sl_in_t1w = transform_streamlines(tck.streamlines, inv_affine)
            loaded.append((bname, sl_in_t1w, bcolor))
            print(f"  ✓ Loaded {bname} ({len(tck.streamlines)} streamlines)")
        except Exception as e:
            print(f"  ! {bname}: failed to transform streamlines: {e}")

    print("Loading T1w and brain mask...")
    t1w_img = nb.load(dwi_path / f"{t1w_base}_desc-preproc_T1w.nii.gz")
    brain_mask_img = nb.load(dwi_path / f"{t1w_base}_desc-brain_mask.nii.gz")
    brain_mask_data = brain_mask_img.get_fdata()
    if np.count_nonzero(brain_mask_data) == 0:
        print("  ! Brain mask is empty; continuing without contour.")
    brain_mask_center = (
        np.array(np.where(brain_mask_data)).mean(axis=1)
        if np.count_nonzero(brain_mask_data)
        else np.array([0, 0, 0])
    )

    # Build scene
    scene = window.Scene()
    if np.count_nonzero(brain_mask_data):
        brain_actor = actor.contour_from_roi(
            brain_mask_data, color=[0, 0, 0], opacity=0.1
        )
        scene.add(brain_actor)

    # Add any bundles we successfully loaded
    if loaded:
        for bname, sl_in_t1w, bcolor in loaded:
            try:
                scene.add(lines_as_tubes(sl_in_t1w, 8, colors=bcolor))
            except Exception as e:
                print(f"  ! {bname}: failed to create/add actor: {e}")
    else:
        print("  - No bundles available to plot; will save brain-only images.")

    scene.background((1, 1, 1))

    if interactive:
        print("Launching interactive visualization window...")
        window.show(scene, size=(1200, 1200), reset_camera=False)
        return scene

    # If no camera_positions provided, use a sane default set
    if not camera_positions:
        camera_positions = {
            "lh_camera_position": {
                "offset": (360.0, 0.0, 0.0),
                "view_up": (0.0, 0.0, 1.0),
            },
            "rh_camera_position": {
                "offset": (-360.0, 0.0, 0.0),
                "view_up": (0.0, 0.0, 1.0),
            },
            "posterior_camera_position": {
                "offset": (0.0, 360.0, 0.0),
                "view_up": (0.0, 0.0, 1.0),
            },
            "superior_camera_position": {
                "offset": (0.0, 0.0, 360.0),
                "view_up": (0.0, -1.0, 0.0),
            },
        }

    images = []
    for name, cam in camera_positions.items():
        png_path = out_dir / f"{out_png}_{name}.png"
        cam_pos = {
            "position": tuple(np.array(cam["offset"]) + brain_mask_center),
            "focal_point": brain_mask_center,
            "view_up": cam["view_up"],
        }
        print(f"Setting camera: {name}")
        scene.set_camera(**cam_pos)
        try:
            window.record(
                scene=scene,
                out_path=str(png_path),
                size=(2400, 2400),
                reset_camera=False,
            )
            images.append(png_path)
        except Exception as e:
            print(f"  ! Failed to record image for {name}: {e}")

    if not images:
        print("  ! No images were saved.")
        return images

    pf = PanelFigure(1, len(images), 3 * len(images), 3)
    final_png = out_dir / f"{out_png}.png"
    for i, img in enumerate(images):
        pf.add_img(img, i, 0)
    pf.format_and_save_figure(final_png)
    print("Saved final figure to:", final_png)
    return images


if __name__ == "__main__":
    data_root = Path(
        "/Users/sps253/Documents/GIT/grmpy_opendata/ignore/qsi-data"
    )  # local path - replace
    out_dir = Path(
        "/Users/sps253/Documents/GIT/grmpy_opendata/analysis/plots"
    )  # local path - replace
    out_dir.mkdir(parents=True, exist_ok=True)

    camera_positions6 = {
        "lh_camera_position": {"offset": (360.0, 0.0, 0.0), "view_up": (0.0, 0.0, 1.0)},
        "rh_camera_position": {
            "offset": (-360.0, 0.0, 0.0),
            "view_up": (0.0, 0.0, 1.0),
        },
        "posterior_camera_position": {
            "offset": (0.0, 360.0, 0.0),
            "view_up": (0.0, 0.0, 1.0),
        },
        "superior_camera_position": {
            "offset": (0.0, 0.0, 360.0),
            "view_up": (0.0, -1.0, 0.0),
        },
    }

    print(f"Looking for subjects in {data_root}")
    subjects = [p.name for p in data_root.glob("sub-*") if p.is_dir()]
    print(f"Found {len(subjects)} subjects: {subjects}")

    for subject in subjects:
        subid = subject.replace("sub-", "")
        session_dirs = sorted((data_root / subject).glob("ses-*"))
        sesids = [s.name.replace("ses-", "") for s in session_dirs if s.is_dir()]
        print(f"\nSubject: {subject} has {len(sesids)} session(s): {sesids}")

        for sesid in sesids:
            try:
                print(f"\n→ Processing {subject} ses-{sesid}")
                images = visualize_bundles(
                    data_root=data_root,
                    out_dir=out_dir,
                    subid=subid,
                    sesid=sesid,
                    out_png=f"QSIRecon_DSIAutoTrack_{subject}_ses-{sesid}",
                    camera_positions=camera_positions6,
                )
                if images:
                    print(f"Saved panel for {subject} ses-{sesid}")
                else:
                    print(f"No images returned for {subject} ses-{sesid}")
            except Exception as e:
                # Absolute last-resort catch so a single bad session never halts the loop
                print(f"Error for {subject} ses-{sesid}: {e}")
