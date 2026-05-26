#!/bin/bash
#SBATCH --job-name=nback_secondlevel_thresholded
#SBATCH --output=/cbica/projects/grmpy/data/derivatives/logs/fracback_secondlevel_%j.out
#SBATCH --error=/cbica/projects/grmpy/data/derivatives/logs/fracback_secondlevel_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G

eval "$(micromamba shell hook --shell bash)"
micromamba activate nilearn

python /cbica/projects/grmpy/code/analysis/task_glm/run_fracback_second_level_thresholded.py
