#!/bin/bash -l
#SBATCH --job-name=nback_firstlevel
#SBATCH --output=/cbica/projects/grmpy/data/derivatives/logs/fracback_%A_%a.out
#SBATCH --error=/cbica/projects/grmpy/data/derivatives/logs/fracback_%A_%a.err
#SBATCH --array=0-189         # 190 subjects after removing 5 who failed xcpd QC.
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G

# --------------------------
# LOAD ENVIRONMENT
# --------------------------

module purge
eval "$(micromamba shell hook --shell bash)"
micromamba activate nilearn

# --------------------------
# SUBJECT LIST (NO COMMAS)
# --------------------------

mapfile -t SUBJECT_LIST < /cbica/projects/grmpy/code/analysis/task_glm/subjects.txt # all subjects with event.tsv files sans 5 who failed QC.

SUB_ID=${SUBJECT_LIST[$SLURM_ARRAY_TASK_ID]}

echo "Running first-level GLM for subject: $SUB_ID"
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"

# --------------------------
# RUN FIRST-LEVEL SCRIPT
# --------------------------

python /cbica/projects/grmpy/code/analysis/task_glm/run_fracback_glm_first_level.py $SUB_ID

