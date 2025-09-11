import pandas as pd
import os
import re
import subprocess
import argparse
import json


def post_cubids_processing(
    bids,
    summary_file,
    files_file,
    rename_log_file,
    search_term,
    delete_set_patterns=None,
    delete_log_file=None,
    acq_rename_map=None,
    dry_run=False,
):
    """
    Processes and renames files based on the RenameEntitySet column, filtering with the search term.
    Optionally deletes files based on delete_set_patterns.

    Args:
        bids (str): Path to the BIDS dataset.
        summary_file (str): Path to the summary TSV file.
        files_file (str): Path to the files TSV file.
        rename_log_file (str): Path to save the rename log TSV.
        search_term (str): Term used to filter RenameEntitySet column.
        delete_set_patterns (list or None): List of patterns to identify files for deletion (default is None).
        delete_log_file (str or None): Path to save the deletion log TSV (default is None).
        acq_rename_map (dict or None): Mapping for renaming long acquisition names to shorter versions (default is None).
    """

    # Load data
    df_summary = pd.read_csv(summary_file, sep="\t")
    df_files = pd.read_csv(files_file, sep="\t")

    # Clean RenameEntitySet column
    df_summary["RenameEntitySet"] = (
        df_summary["RenameEntitySet"].astype(str).str.strip()
    )
    df_filtered = df_summary[
        df_summary["RenameEntitySet"].str.contains(search_term, na=False)
    ]

    # Define patterns
    rename_set_patterns = list(df_filtered["RenameEntitySet"].unique())

    # If deletion patterns are provided, remove them from the rename set patterns
    if delete_set_patterns is not None:
        rename_set_patterns = [
            pattern
            for pattern in rename_set_patterns
            if pattern not in delete_set_patterns
        ]

    # Store renaming mappings
    rename_log = []

    def clean_filename(filename):
        """Collapses any double-underscores, etc."""
        return re.sub(r"__+", "_", filename)

    def unify_acq(existing_acq, new_acq):
        """Merges acquisition values while preventing redundancy."""
        if not existing_acq:
            return new_acq
        if new_acq in existing_acq:
            return existing_acq
        if existing_acq in new_acq:
            return new_acq
        return f"{existing_acq}_{new_acq}"

    def modify_acq(existing_acq, new_acq, acq_rename_map=None):
        """Dynamically merges existing and new acquisition strings and applies renaming mappings.

        The mapping is applied in descending order of key length to ensure that longer,
        more specific variant strings take precedence. After mapping, multiple 'VARIANT'
        tokens are merged so that only the first occurrence keeps the 'VARIANT' prefix.
        """

        def merge_variants(acq_str):
            # Split the string by the token "VARIANT".
            parts = acq_str.split("VARIANT")
            # If there's only one part, there's nothing to merge.
            if len(parts) < 2:
                return acq_str
            # Reassemble the string: keep the first occurrence as "VARIANT" + token,
            # then simply concatenate the rest (which removes the extra "VARIANT" prefixes).
            return parts[0] + "VARIANT" + "".join(parts[1:])

        # Default new_acq to an empty string if None.
        new_acq = new_acq or ""

        # Merge the existing and new acquisition strings using your unify_acq helper.
        merged_acq = unify_acq(existing_acq, new_acq)

        # Apply the renaming mapping if provided.
        if acq_rename_map:
            # Sort mapping items by descending key length to prioritize longer matches.
            for long_variant, short_variant in sorted(
                acq_rename_map.items(), key=lambda x: -len(x[0])
            ):
                # Remove word boundaries so the replacement works even when tokens are concatenated.
                pattern = re.escape(long_variant)
                merged_acq = re.sub(pattern, short_variant, merged_acq)

        # Merge multiple 'VARIANT' tokens: e.g. convert "VARIANTInferredbvecVARIANTVar1" to "VARIANTInferredbvecVar1"
        merged_acq = merge_variants(merged_acq)

        return merged_acq

    ##########################################################################################
    # Process each rename pattern
    ##########################################################################################
    for pattern in rename_set_patterns:
        print(f"\nProcessing pattern: {pattern}")

        matching_entries = df_summary[
            df_summary["RenameEntitySet"].str.startswith(pattern, na=False)
        ]
        if matching_entries.empty:
            print(f"  No matches found for pattern: {pattern}")
            continue

        for _, row in matching_entries.iterrows():
            rename_set = row["RenameEntitySet"]
            suffix_match = re.search(r"suffix-([^_]+)", rename_set)
            suffix = suffix_match.group(1) if suffix_match else ""

            acq_match = re.search(r"acquisition-([^_]+)", rename_set)
            acq = acq_match.group(1) if acq_match else ""

            key_param_group = df_summary.loc[
                df_summary.RenameEntitySet == rename_set, "KeyParamGroup"
            ].tolist()
            files = df_files[df_files["KeyParamGroup"].isin(key_param_group)][
                "FilePath"
            ]

            if files.empty:
                print(f"  No files found for RenameEntitySet: {rename_set}")
                continue

            for file in files:
                nii_path = os.path.join(bids, file.lstrip("/"))
                json_path = nii_path.replace(".nii.gz", ".json")

                bvec_path, bval_path = None, None
                if "dwi" in search_term and "epi" not in search_term:
                    bvec_path = nii_path.replace(".nii.gz", ".bvec")
                    bval_path = nii_path.replace(".nii.gz", ".bval")

                existing_acq_match = re.search(r"acq-([^_]+)", nii_path)
                existing_acq = existing_acq_match.group(1) if existing_acq_match else ""

                # Pass the acq_rename_map into modify_acq so mapping is applied only once
                new_acq_final = modify_acq(
                    existing_acq, acq, acq_rename_map=acq_rename_map
                )

                ################################################################################
                # Replace or insert 'acq-new_acq_final' in the file name
                ################################################################################
                if existing_acq_match:
                    new_nii_path = re.sub(
                        r"acq-[^_]+", f"acq-{new_acq_final}", nii_path
                    )
                else:
                    # Break apart the path to get directory and base filename
                    dir_name = os.path.dirname(nii_path)
                    base_name = os.path.basename(nii_path)

                    # Determine extension and the name without extension
                    if base_name.endswith(".nii.gz"):
                        ext = ".nii.gz"
                        name_no_ext = base_name[:-7]
                    elif base_name.endswith(".json"):
                        ext = ".json"
                        name_no_ext = base_name[:-5]
                    else:
                        ext = os.path.splitext(base_name)[1]
                        name_no_ext = os.path.splitext(base_name)[0]

                    # Check if filename contains "run-*" or "mt-off"/"mt-on"
                    token_match = re.search(
                        r"_(run-\d+|mt-(?:on|off))(?=_|$)", name_no_ext
                    )
                    if token_match:
                        insert_index = token_match.start()
                        new_name_no_ext = (
                            name_no_ext[:insert_index]
                            + f"_acq-{new_acq_final}"
                            + name_no_ext[insert_index:]
                        )
                    elif suffix:
                        # If the name ends with the suffix token, insert acq before it.
                        suffix_token = f"_{suffix}"
                        if name_no_ext.endswith(suffix_token):
                            new_name_no_ext = (
                                name_no_ext[: -len(suffix_token)]
                                + f"_acq-{new_acq_final}"
                                + suffix_token
                            )
                        else:
                            new_name_no_ext = name_no_ext + f"_acq-{new_acq_final}"
                    else:
                        new_name_no_ext = name_no_ext + f"_acq-{new_acq_final}"

                    new_base_name = new_name_no_ext + ext
                    new_nii_path = os.path.join(dir_name, new_base_name)

                # Ensure replacements for ObliquityFalse/True -> Plumb/Oblique
                new_nii_path = new_nii_path.replace("ObliquityFalse", "Plumb").replace(
                    "ObliquityTrue", "Oblique"
                )
                new_nii_path = clean_filename(new_nii_path)
                new_json_path = new_nii_path.replace(".nii.gz", ".json")

                new_bvec_path, new_bval_path = None, None
                if "dwi" in search_term and "epi" not in search_term:
                    new_bvec_path = new_nii_path.replace(".nii.gz", ".bvec")
                    new_bval_path = new_nii_path.replace(".nii.gz", ".bval")

                # Store rename mapping
                rename_log.append({"orig_name": nii_path, "rename_to": new_nii_path})

                ################################################################################
                # Check existence and do the renames
                ################################################################################

                if os.path.exists(nii_path):
                    print(f"Rename: {nii_path} -> {new_nii_path}")
                    if not dry_run:
                        subprocess.run(["git", "mv", nii_path, new_nii_path])
                else:
                    print(f"Not found: {nii_path}")

                if os.path.exists(json_path):
                    print(f"Rename: {json_path} -> {new_json_path}")
                    if not dry_run:
                        subprocess.run(["git", "mv", json_path, new_json_path])
                else:
                    print(f"Not found: {json_path}")

                if "dwi" in search_term and "epi" not in search_term:
                    if bvec_path and os.path.exists(bvec_path):
                        print(f"Rename: {bvec_path} -> {new_bvec_path}")
                        if not dry_run:
                            subprocess.run(["git", "mv", bvec_path, new_bvec_path])
                    else:
                        print(f"Not found: {bvec_path}")

                    if bval_path and os.path.exists(bval_path):
                        print(f"Rename: {bval_path} -> {new_bval_path}")
                        if not dry_run:
                            subprocess.run(["git", "mv", bval_path, new_bval_path])
                    else:
                        print(f"Not found: {bval_path}")

    # Save rename log
    df_rename_log = pd.DataFrame(rename_log)
    df_rename_log.to_csv(rename_log_file, sep="\t", index=False)

    print(f"\nRename log saved to {rename_log_file}")

    ################################################################################
    # Process deletion if delete_set_patterns and delete_log_file are specified
    ################################################################################

    if delete_set_patterns is not None and delete_log_file is not None:
        # Store deletion mappings
        delete_log = []
        # Process each delete pattern
        for pattern in delete_set_patterns:
            print(f"\nProcessing delete pattern: {pattern}")
            matching_entries = df_summary[
                df_summary["RenameEntitySet"].str.startswith(pattern, na=False)
            ]
            if matching_entries.empty:
                print(f"  No matches found for delete pattern: {pattern}")
                continue
            for _, row in matching_entries.iterrows():
                delete_set = row["RenameEntitySet"]
                key_param_group = df_summary.loc[
                    df_summary.RenameEntitySet == delete_set, "KeyParamGroup"
                ].tolist()
                files = df_files[df_files["KeyParamGroup"].isin(key_param_group)][
                    "FilePath"
                ]
                if files.empty:
                    print(f"  No files found for RenameEntitySet: {delete_set}")
                    continue
                for file in files:
                    nii_path = os.path.join(bids, file.lstrip("/"))
                    json_path = nii_path.replace(".nii.gz", ".json")

                    bvec_path, bval_path = None, None
                    if "dwi" in search_term and "epi" not in search_term:
                        bvec_path = nii_path.replace(".nii.gz", ".bvec")
                        bval_path = nii_path.replace(".nii.gz", ".bval")

                    # Delete the nii file
                    if os.path.exists(nii_path):
                        print(f"Delete: {nii_path}")
                        if not dry_run:
                            subprocess.run(["git", "rm", nii_path])
                        delete_log.append({"file_deleted": nii_path})
                    else:
                        print(f"Not found for deletion: {nii_path}")

                    # Delete the json file
                    if os.path.exists(json_path):
                        print(f"Delete: {json_path}")
                        if not dry_run:
                            subprocess.run(["git", "rm", json_path])
                        delete_log.append({"file_deleted": json_path})
                    else:
                        print(f"Not found for deletion: {json_path}")

                    if "dwi" in search_term and "epi" not in search_term:
                        if bvec_path and os.path.exists(bvec_path):
                            print(f"Delete: {bvec_path}")
                            if not dry_run:
                                subprocess.run(["git", "rm", bvec_path])
                            delete_log.append({"file_deleted": bvec_path})
                        else:
                            print(f"Not found for deletion: {bvec_path}")
                        if bval_path and os.path.exists(bval_path):
                            print(f"Delete: {bval_path}")
                            if not dry_run:
                                subprocess.run(["git", "rm", bval_path])
                            delete_log.append({"file_deleted": bval_path})
                        else:
                            print(f"Not found for deletion: {bval_path}")

        # Save deletion log
        df_delete_log = pd.DataFrame(delete_log)
        df_delete_log.to_csv(delete_log_file, sep="\t", index=False)

        print(f"\nDelete log saved to {delete_log_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Rename and optionally delete files based on cubids summary/files TSVs."
    )
    parser.add_argument("bids", type=str, help="Path to the BIDS dataset (root)")
    parser.add_argument("summary_file", type=str, help="Path to the summary TSV file")
    parser.add_argument("files_file", type=str, help="Path to the files TSV file")
    parser.add_argument(
        "rename_log_file", type=str, help="Path to write the rename log TSV"
    )
    parser.add_argument(
        "search_term",
        type=str,
        help="Filter term for 'RenameEntitySet' (e.g., 'datatype-dwi' or 'datatype-func')",
    )
    parser.add_argument(
        "--delete-set-pattern",
        dest="delete_set_patterns",
        action="append",
        default=None,
        help="Pattern in RenameEntitySet to delete; may be provided multiple times",
    )
    parser.add_argument(
        "--delete-log-file",
        dest="delete_log_file",
        type=str,
        default=None,
        help="Path to write the deletion log TSV (required to perform deletions)",
    )
    parser.add_argument(
        "--acq-rename-map",
        dest="acq_rename_map_path",
        type=str,
        default=None,
        help="Path to JSON mapping for acquisition normalization (long -> short)",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Show planned operations without performing git moves/removals",
    )

    args = parser.parse_args()

    acq_rename_map = None
    if args.acq_rename_map_path:
        try:
            with open(args.acq_rename_map_path, "r") as f:
                acq_rename_map = json.load(f)
        except Exception as e:
            print(
                f"Warning: failed to load acq rename map '{args.acq_rename_map_path}': {e}"
            )

    post_cubids_processing(
        bids=args.bids,
        summary_file=args.summary_file,
        files_file=args.files_file,
        rename_log_file=args.rename_log_file,
        search_term=args.search_term,
        delete_set_patterns=args.delete_set_patterns,
        delete_log_file=args.delete_log_file,
        acq_rename_map=acq_rename_map,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("Dry run complete; no files modified.")
    else:
        print("Processing complete.")


if __name__ == "__main__":
    main()
