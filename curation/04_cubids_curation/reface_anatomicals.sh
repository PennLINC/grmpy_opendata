#!/usr/bin/env bash
#SBATCH --job-name=reface
#SBATCH --output=/cbica/projects/grmpy/code/curation/04_cubids_curation/logs/reface/reface_%A_%a.out
#SBATCH --error=/cbica/projects/grmpy/code/curation/04_cubids_curation/logs/reface/reface_%A_%a.err
#SBATCH --array=0-481           # <-- Adjust to (# of T1w+T2w files) - 1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G

set -eux

# Load AFNI (for T1w refacing)
module add afni/2022_05_03

bids_root="/cbica/projects/grmpy/data/bids"
old_anat_archive_dir="${bids_root}/sourcedata/original_anatomicals"
mkdir -p "${old_anat_archive_dir}"

# 1) Gather T1w/T2w files (both), then sort
mapfile -t anat_files < <(find "${bids_root}"/sub-* -type f \
  \( -name "*_T1w.nii.gz" -o -name "*_T2w.nii.gz" \) \
  | sort)

num_files="${#anat_files[@]}"
echo "Found ${num_files} T1w/T2w files (including possibly already-defaced)."

# 2) Select the file for this array index
ANAT="${anat_files[$SLURM_ARRAY_TASK_ID]}"

ANAT_DIR="$(dirname "$ANAT")"
ANAT_BASENAME="$(basename "$ANAT")"

# Move to the directory containing the file
cd "$ANAT_DIR"

# 3) Skip if already has 'rec-defaced' in the name
if [[ "$ANAT_BASENAME" == *"rec-defaced"* ]]; then
  echo "Skipping $ANAT_BASENAME (already rec-defaced)."
  exit 0
fi

# 4) Build the defaced filename: Insert "_rec-defaced" before T1w or T2w
DEFACED_BASENAME="$(echo "$ANAT_BASENAME" | sed 's/\(_T[12]w\)\.nii\.gz$/_rec-defaced\1.nii.gz/')"

echo "SLURM_ARRAY_TASK_ID:   $SLURM_ARRAY_TASK_ID"
echo "Anatomical directory:  $ANAT_DIR"
echo "Anatomical file:       $ANAT_BASENAME"
echo "Defaced file:          $DEFACED_BASENAME"

# 5) Decide which defacing tool to use
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

# 6) Move original NIfTI to the archive
mv "${ANAT_BASENAME}" "${old_anat_archive_dir}/"

# 7) Handle the JSON sidecar (if it exists)
JSON_BASENAME="${ANAT_BASENAME%.nii.gz}.json"
if [ -f "$JSON_BASENAME" ]; then
  cp "${JSON_BASENAME}" "${old_anat_archive_dir}/"
  DEFACED_JSON_BASENAME="$(echo "$JSON_BASENAME" | sed 's/\(_T[12]w\)\.json$/_rec-defaced\1.json/')"

  echo "JSON sidecar found:   $JSON_BASENAME"
  echo "Copying to archive:   -> ${old_anat_archive_dir}/"
  echo "Renaming local JSON:  $JSON_BASENAME -> $DEFACED_JSON_BASENAME"

  mv "${JSON_BASENAME}" "$DEFACED_JSON_BASENAME"
fi

# 8) Clean up only if T1w (AFNI refacer leaves extra files)
if [[ "$ANAT_BASENAME" == *"_T1w.nii.gz" ]]; then
  rm -f *rec-defaced*face_plus*
  rm -rf *rec-defaced*_QC/
fi

echo "Done processing $ANAT_BASENAME"

