from glob import glob
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if __name__ == "__main__":
    # Load parcel dseg info
    dseg_file = (
        "/cbica/projects/grmpy/data/derivatives/xcpd/atlases/atlas-4S1056Parcels/"
        "atlas-4S1056Parcels_dseg.tsv"
    )
    dseg_df = pd.read_table(dseg_file)

    atlas_mapper = {
        "CIT168Subcortical": "Subcortical",
        "ThalamusHCP": "Thalamus",
        "SubcorticalHCP": "Subcortical",
    }
    network_labels = dseg_df["network_label"].fillna(dseg_df["atlas_name"]).tolist()
    network_labels = [atlas_mapper.get(net, net) for net in network_labels]

    # Determine order of nodes while retaining original order of networks
    unique_labels = []
    for label in network_labels:
        if label not in unique_labels:
            unique_labels.append(label)

    mapper = {label: f"{i:03d}_{label}" for i, label in enumerate(unique_labels)}
    mapped_network_labels = [mapper[label] for label in network_labels]
    community_order = np.argsort(mapped_network_labels)

    # Get the community name associated with each network
    labels = np.array(network_labels)[community_order]
    unique_labels = []
    for label in labels:
        if label not in unique_labels:
            unique_labels.append(label)

    # Find the locations for the community-separating lines
    break_idx = [0]
    end_idx = None
    for label in unique_labels:
        start_idx = np.where(labels == label)[0][0]
        if end_idx:
            break_idx.append(np.nanmean([start_idx, end_idx]))
        end_idx = np.where(labels == label)[0][-1]
    break_idx.append(len(labels))
    break_idx = np.array(break_idx)

    # Label positions
    label_idx = np.nanmean(np.vstack((break_idx[1:], break_idx[:-1])), axis=0)

    # Find correlation matrices
    corrmats = sorted(
        glob(
            "/cbica/projects/grmpy/data/derivatives/xcpd/sub-*/ses-*/func/"
            "*seg-4S1056Parcels_stat-pearsoncorrelation_relmat.tsv"
        )
    )
    corrmat_scan_keys = {}
    for cm in corrmats:
        entities = {}
        for part in cm.rsplit("/", 1)[-1].split("_"):
            if "-" in part:
                key, value = part.split("-", 1)
                entities[key] = value.removesuffix(".tsv")
        corrmat_scan_keys[cm] = (
            cm.split("/")[-5],
            entities.get("task"),
            entities.get("acq"),
        )

    excluded_scans = pd.read_csv(
        "/cbica/projects/grmpy/code/curation/06_QC/data/final_qc/fmri_qc.csv"
    )
    excluded_scans = set(
        excluded_scans.loc[
            excluded_scans["qc_determination"].astype(str).str.strip().eq("fail"),
            ["participant_id", "session_id", "task", "acq"],
        ].itertuples(index=False, name=None)
    )
    print(f"Total excluded scans: {len(excluded_scans)}")

    # --- Exclude regions based on coverage ---
    excluded_regions = set(["RH_Cont_Cing_1", "RH_Vis_33"])
    # Get region label index positions
    region_labels = dseg_df["label"].tolist()
    exclude_indices = [
        i for i, name in enumerate(region_labels) if name in excluded_regions
    ]

    for task in [
        "rest_acq-multiband",
        "rest_acq-singleband",
        "fracback",
        "face",
    ]:
        # --- Count total before filtering ---
        selected_corrmats = [cm for cm in corrmats if f"task-{task}" in cm]
        print(f"Total {task} scans found: {len(selected_corrmats)}")

        # --- Filter correlation matrices ---
        selected_corrmats = [
            cm
            for cm in selected_corrmats
            if corrmat_scan_keys[cm] not in excluded_scans
        ]
        print(f"Included scans after exclusion: {len(selected_corrmats)}")

        # --- Load matrices ---
        arrs = [
            pd.read_table(cm, index_col="Node").to_numpy() for cm in selected_corrmats
        ]
        arr_3d = np.dstack(arrs)
        arr_3d = np.clip(arr_3d, -0.999999, 0.999999)
        print(f"Correlation array shape: {arr_3d.shape}")

        arr_3d_z = np.arctanh(arr_3d)

        # --- Compute mean (z -> r) ---
        mean_arr_z = np.nanmean(arr_3d_z, axis=2)
        mean_arr_z = mean_arr_z[community_order, :][:, community_order]
        np.fill_diagonal(mean_arr_z, 0)
        mean_arr_r = np.tanh(mean_arr_z)

        # Remap excluded region indices through community_order
        exclude_indices_reordered = [
            np.where(community_order == idx)[0][0]
            for idx in exclude_indices
            if idx in community_order
        ]

        # Apply exclusions AFTER final plot space
        mean_arr_r[exclude_indices_reordered, :] = np.nan
        mean_arr_r[:, exclude_indices_reordered] = np.nan

        # --- Plotting settings ---
        # save out text as text
        import matplotlib as mpl

        mpl.rcParams["pdf.fonttype"] = 42  # keep text as TrueType
        mpl.rcParams["ps.fonttype"] = 42
        mpl.rcParams["svg.fonttype"] = "none"

        # --- Plot mean matrix ---
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.set_facecolor("white")
        cmap = mpl.cm.get_cmap("seismic").copy()
        cmap.set_bad(color="none")  # Transparent for NaN
        img = ax.imshow(mean_arr_r, cmap=cmap, vmin=-1, vmax=1)
        for idx in break_idx[1:-1]:
            ax.axvline(idx, color="black")
            ax.axhline(idx, color="black")
        ax.set_yticks(label_idx)
        ax.set_xticks(label_idx)
        ax.set_yticklabels(unique_labels)
        ax.set_xticklabels(unique_labels, rotation=90)
        fig.tight_layout()
        fig.savefig(
            f"/cbica/projects/grmpy/code/analysis/plots/task-{task.replace('_acq-', '-')}_mean.pdf"
        )
        plt.close()

        # --- Plot colorbars ---
        fig, axs = plt.subplots(1, 1, figsize=(15, 2))
        # Mean
        norm_mean = mpl.colors.Normalize(vmin=-1, vmax=1)
        fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm_mean, cmap="seismic"),
            cax=axs,
            orientation="horizontal",
        ).set_ticks([-1, 0, 1])
        fig.tight_layout()
        fig.savefig(
            f"/cbica/projects/grmpy/code/analysis/plots/task-{task.replace('_acq-', '-')}_colorbar.pdf",
            bbox_inches="tight",
        )
        plt.close()
