#!/usr/bin/env bash

set -euo pipefail

# replace_anatomicals_with_originals.sh
# Safely delete existing T1w/T2w images and sidecars in a BIDS dataset and copy
# originals from a flat sourcedata/original_anatomicals directory into matching
# sub-*/ses-*/anat directories.
#
# Defaults to DRY-RUN. Use --execute to actually perform changes.
# Produces a TSV report of planned or executed actions.

print_usage() {
  cat <<EOF
Usage: $(basename "$0") --bids-dir /path/to/BIDS [--source-dir /path/to/BIDS/sourcedata/original_anatomicals] [--report /path/to/report.tsv] [--execute]

Options:
  --bids-dir DIR        Path to BIDS dataset root (required)
  --source-dir DIR      Path to flat originals (default: BIDS_DIR/sourcedata/original_anatomicals)
  --report FILE         Path to TSV report (default: BIDS_DIR/logs/replace_anatomicals_YYYYmmdd_HHMMSS.tsv)
  --execute             Perform actions (default: dry-run)
  -h, --help            Show this help and exit

Behavior:
  1) Deletes existing T1w/T2w NIfTI and JSON files in sub-*/ses-*/anat.
  2) Copies originals from SOURCE_DIR (flat) into matching sub-*/ses-*/anat.
  3) In dry-run, only reports planned DELETE/COPY actions.

Safety:
  - Requires --execute to actually delete/copy files.
  - Skips files without both subject and session entities in filename.
  - Creates missing anat directories on execute.
EOF
}

timestamp() { date '+%Y%m%d_%H%M%S'; }

is_dry_run=1
bids_dir=""
source_dir=""
report_path=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bids-dir)
      bids_dir="$2"; shift 2 ;;
    --source-dir)
      source_dir="$2"; shift 2 ;;
    --report)
      report_path="$2"; shift 2 ;;
    --execute)
      is_dry_run=0; shift ;;
    -h|--help)
      print_usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2
      print_usage
      exit 2 ;;
  esac
done

if [[ -z "${bids_dir}" ]]; then
  echo "Error: --bids-dir is required" >&2
  print_usage
  exit 2
fi

if [[ ! -d "${bids_dir}" ]]; then
  echo "Error: BIDS directory not found: ${bids_dir}" >&2
  exit 1
fi

if [[ -z "${source_dir}" ]]; then
  source_dir="${bids_dir}/sourcedata/original_anatomicals"
fi

if [[ ! -d "${source_dir}" ]]; then
  echo "Error: source directory not found: ${source_dir}" >&2
  exit 1
fi

logs_dir="${bids_dir}/logs"
mkdir -p "${logs_dir}"

if [[ -z "${report_path}" ]]; then
  report_path="${logs_dir}/replace_anatomicals_$(timestamp).tsv"
fi

echo -e "action\tmodality\tsubject\tsession\tsource_path\tdest_path" > "${report_path}"

note_dryrun() {
  if [[ ${is_dry_run} -eq 1 ]]; then
    echo "[DRY-RUN] $*"
  else
    echo "$*"
  fi
}

report() {
  # args: action modality subject session source dest
  echo -e "$1\t$2\t$3\t$4\t$5\t$6" >> "${report_path}"
}

delete_targets() {
  # Find existing T1w/T2w files in anat directories and schedule deletion
  # This will match .nii.gz, .nii, and .json
  while IFS= read -r -d '' file; do
    fname="$(basename "$file")"
    modality=""
    if [[ "$fname" == *_T1w.* ]]; then modality="T1w"; fi
    if [[ "$fname" == *_T2w.* ]]; then modality="T2w"; fi
    # Extract subject and session from path
    # Expected path: .../sub-XXX/ses-YYY/anat/filename
    sub="$(echo "$file" | sed -n 's#.*/\(sub-[^/]*\)/.*#\1#p')"
    ses="$(echo "$file" | sed -n 's#.*/\(ses-[^/]*\)/anat/.*#\1#p')"
    dest_path="$file"
    report "DELETE" "$modality" "$sub" "$ses" "$dest_path" ""
    if [[ ${is_dry_run} -eq 0 ]]; then
      rm -f -- "$file"
    fi
  done < <(find "${bids_dir}" -type d -name anat -prune -print0 | while IFS= read -r -d '' anatdir; do
              find "$anatdir" -type f \( -name '*_T1w.nii.gz' -o -name '*_T1w.nii' -o -name '*_T1w.json' -o \
                                           -name '*_T2w.nii.gz' -o -name '*_T2w.nii' -o -name '*_T2w.json' \) -print0
            done)
}

copy_sources() {
  # Iterate over source files for T1w/T2w, group by base stem without extension
  # We will consider .nii.gz/.nii and .json sidecar
  shopt -s nullglob
  # Collect unique basenames (without extension) for modalities
  declare -A seen
  while IFS= read -r -d '' src; do
    base="${src##*/}"
    # normalize to remove .nii.gz or .nii or .json
    stem="$base"
    stem="${stem%.nii.gz}"
    stem="${stem%.nii}"
    stem="${stem%.json}"
    # Only consider stems that include _T1w or _T2w
    if [[ "$stem" != *"_T1w" && "$stem" != *"_T2w" ]]; then
      continue
    fi
    if [[ -n "${seen[$stem]:-}" ]]; then
      continue
    fi
    seen[$stem]=1

    modality=""
    if [[ "$stem" == *"_T1w" ]]; then modality="T1w"; fi
    if [[ "$stem" == *"_T2w" ]]; then modality="T2w"; fi

    # Extract subject and session from stem (e.g., sub-XXX[_...]_ses-YYY[_...]_T1w)
    subj_token="$(echo "$stem" | grep -o 'sub-[^_]*')"
    sess_token="$(echo "$stem" | grep -o 'ses-[^_]*')"

    if [[ -z "$subj_token" || -z "$sess_token" ]]; then
      note_dryrun "Skipping (cannot determine subject/session): ${src}"
      report "SKIP" "$modality" "$subj_token" "$sess_token" "$src" ""
      continue
    fi

    dest_dir="${bids_dir}/${subj_token}/${sess_token}/anat"
    nii_src=""
    if [[ -f "${source_dir}/${stem}.nii.gz" ]]; then
      nii_src="${source_dir}/${stem}.nii.gz"
    elif [[ -f "${source_dir}/${stem}.nii" ]]; then
      nii_src="${source_dir}/${stem}.nii"
    fi
    json_src=""
    if [[ -f "${source_dir}/${stem}.json" ]]; then
      json_src="${source_dir}/${stem}.json"
    fi

    # Copy NIfTI if present
    if [[ -n "$nii_src" ]]; then
      dest_nii="${dest_dir}/$(basename "$nii_src")"
      report "COPY" "$modality" "$subj_token" "$sess_token" "$nii_src" "$dest_nii"
      if [[ ${is_dry_run} -eq 0 ]]; then
        mkdir -p "$dest_dir"
        cp -p "$nii_src" "$dest_nii"
      fi
    else
      note_dryrun "Warning: Missing NIfTI for stem ${stem} in ${source_dir}"
      report "MISSING" "$modality" "$subj_token" "$sess_token" "${source_dir}/${stem}.nii[.gz]" ""
    fi

    # Copy JSON if present
    if [[ -n "$json_src" ]]; then
      dest_json="${dest_dir}/$(basename "$json_src")"
      report "COPY" "$modality" "$subj_token" "$sess_token" "$json_src" "$dest_json"
      if [[ ${is_dry_run} -eq 0 ]]; then
        mkdir -p "$dest_dir"
        cp -p "$json_src" "$dest_json"
      fi
    else
      # Not all datasets have JSONs for these; warn but continue
      note_dryrun "Notice: No JSON for stem ${stem} in ${source_dir}"
      report "INFO" "$modality" "$subj_token" "$sess_token" "(no json)" ""
    fi
  done < <(find "${source_dir}" -maxdepth 1 -type f \( -name 'sub-*_T1w.nii.gz' -o -name 'sub-*_T1w.nii' -o -name 'sub-*_T1w.json' -o -name 'sub-*_T2w.nii.gz' -o -name 'sub-*_T2w.nii' -o -name 'sub-*_T2w.json' \) -print0)
}

mode_label="DRY-RUN"
if [[ ${is_dry_run} -eq 0 ]]; then
  mode_label="EXECUTE"
fi

echo "Mode: ${mode_label}"
echo "BIDS_DIR: ${bids_dir}"
echo "SOURCE_DIR: ${source_dir}"
echo "Report: ${report_path}"

echo "Step 1/2: Deleting existing T1w/T2w from anat directories (${mode_label})"
delete_targets
echo "Step 2/2: Copying originals into matching anat directories (${mode_label})"
copy_sources

echo "Done. Report written to: ${report_path}"


