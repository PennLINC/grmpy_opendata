#!/bin/bash
#SBATCH --job-name=nback_secondlevel
#SBATCH --output=/cbica/projects/grmpy/analysis/task_glm/second-level/logs/fracback_%j.out
#SBATCH --error=/cbica/projects/grmpy/analysis/task_glm/second-level/logs/fracback_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

eval "$(micromamba shell hook --shell bash)"
micromamba activate nilearn

python /cbica/projects/grmpy/code/analysis/task_glm/run_nback_second_level.py
