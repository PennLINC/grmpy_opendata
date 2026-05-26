#!/bin/bash -l
#SBATCH --job-name=nback_firstlevel
#SBATCH --output=/cbica/projects/grmpy/data/derivatives/logs/fracback_%A_%a.out
#SBATCH --error=/cbica/projects/grmpy/data/derivatives/logs/fracback_%A_%a.err
#SBATCH --array=0         # 10 subjects that failed first run
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

SUBJECT_LIST=(
    # 20941
    # 84103
    84761 # failed second run as well -- resubmit
    # 85083
    # 86924
    # 115800
    # 116051
    # 117226
    # 20699
    # 20809
)

SUB_ID=${SUBJECT_LIST[$SLURM_ARRAY_TASK_ID]}

echo "Running first-level GLM for subject: $SUB_ID"
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"

# --------------------------
# RUN FIRST-LEVEL SCRIPT
# --------------------------

python /cbica/projects/grmpy/code/analysis/task_glm/run_fracback_glm_first_level.py $SUB_ID

