#!/bin/bash
#SBATCH --job-name=nback_firstlevel
#SBATCH --output=/cbica/projects/grmpy/analysis/task_glm/first-level/logs/fracback_%A_%a.out
#SBATCH --error=/cbica/projects/grmpy/analysis/task_glm/first-level/logs/fracback_%A_%a.err
#SBATCH --array=0-9          # 10 subjects
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
102041
103679
104235
104785
105168
105176
105767
105860
105979
106039
)

SUB_ID=${SUBJECT_LIST[$SLURM_ARRAY_TASK_ID]}

echo "Running first-level GLM for subject: $SUB_ID"
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"

# --------------------------
# RUN FIRST-LEVEL SCRIPT
# --------------------------

python /cbica/projects/grmpy/code/analysis/task_glm/run_fracback_glm_first_level.py $SUB_ID

