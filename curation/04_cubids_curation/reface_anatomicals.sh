#!/usr/bin/env bash

bids_root="$1"

# Count T1w/T2w files to determine array size
file_count=$(find "${bids_root}"/sub-* -type f \
  \( -name "*_T1w.nii.gz" -o -name "*_T2w.nii.gz" \) \
  | grep -v "rec-defaced" | wc -l)

# Subtract 1 for zero-based array indexing
max_array=$((file_count - 1))

if [ $max_array -lt 0 ]; then
  echo "No files found to process. Exiting."
  exit 1
fi

echo "Found $file_count files to process. Setting array size to 0-$max_array."

# Submit the job with the calculated array size
sbatch --array=0-$max_array <<'SBATCH_SCRIPT'
#!/usr/bin/env bash
#SBATCH --job-name=reface
#SBATCH --output=/cbica/projects/grmpy/code/curation/04_cubids_curation/logs/reface/reface_%A_%a.out
#SBATCH --error=/cbica/projects/grmpy/code/curation/04_cubids_curation/logs/reface/reface_%A_%a.err
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

set -eux

# Load AFNI (for T1w refacing)
module add afni/2022_05_03

# Get the BIDS directory from the parent script
bids_root="${1}"

old_anat_archive_dir="${bids_root}/sourcedata/original_anatomicals"
mkdir -p "${old_anat_archive_dir}"

# 1) Gather T1w/T2w files (both), then sort - excluding already defaced files
mapfile -t anat_files < <(find "${bids_root}"/sub-* -type f \
  \( -name "*_T1w.nii.gz" -o -name "*_T2w.nii.gz" \) \
  | grep -v "rec-defaced" \
  | sort)

num_files="${#anat_files[@]}"
echo "Found ${num_files} T1w/T2w files to process."

# 2) Select the file for this array index
ANAT="${anat_files[$SLURM_ARRAY_TASK_ID]}"

ANAT_DIR="$(dirname "$ANAT")"
ANAT_BASENAME="$(basename "$ANAT")"

# Move to the directory containing the file
cd "$ANAT_DIR"

# 3) Build the defaced filename: Insert "_rec-defaced" before T1w or T2w
DEFACED_BASENAME="$(echo "$ANAT_BASENAME" | sed 's/\(_T[12]w\)\.nii\.gz$/_rec-defaced\1.nii.gz/')"

echo "SLURM_ARRAY_TASK_ID:   $SLURM_ARRAY_TASK_ID"
echo "Anatomical directory:  $ANAT_DIR"
echo "Anatomical file:       $ANAT_BASENAME"
echo "Defaced file:          $DEFACED_BASENAME"

# 4) Decide which defacing tool to use
if [[ "$ANAT_BASENAME" == *"_T1w.nii.gz" ]]; then
  echo "Using @afni_refacer_run (AFNI) for T1w"
  @afni_refacer_run \
    -input "$ANAT_BASENAME" \
    -mode_reface_plus \
    -prefix "$DEFACED_BASENAME"

elif [[ "$ANAT_BASENAME" == *"_T2w.nii.gz" ]]; then
  echo "Using pydeface for T2w"
  /gpfs/fs001/cbica/projects/grmpy/micromamba/envs/babs/bin/pydeface --outfile "$DEFACED_BASENAME" "$ANAT_BASENAME"

fi

# 5) Use git rm instead of moving the original NIfTI
git rm "${ANAT_BASENAME}"

# 6) Handle the JSON sidecar (if it exists)
JSON_BASENAME="${ANAT_BASENAME%.nii.gz}.json"
if [ -f "$JSON_BASENAME" ]; then
  DEFACED_JSON_BASENAME="$(echo "$JSON_BASENAME" | sed 's/\(_T[12]w\)\.json$/_rec-defaced\1.json/')"

  echo "JSON sidecar found:   $JSON_BASENAME"
  echo "Renaming to:          $DEFACED_JSON_BASENAME"

  # Copy the content to the new filename
  cp "${JSON_BASENAME}" "$DEFACED_JSON_BASENAME"

  # Remove the original JSON with git
  git rm "${JSON_BASENAME}"
fi

# 7) Clean up only if T1w (AFNI refacer leaves extra files)
if [[ "$ANAT_BASENAME" == *"_T1w.nii.gz" ]]; then
  rm -f *rec-defaced*face_plus*
  rm -rf *rec-defaced*_QC/
fi

echo "Done processing $ANAT_BASENAME"
SBATCH_SCRIPT

echo "Job submitted with BIDS directory: $bids_root"

