#!/bin/bash
#SBATCH --job-name=cubids_apply
#SBATCH --output=cubids_apply_%A.out
#SBATCH --error=cubids_apply_%A.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=48:00:00        # Adjust time as needed
#SBATCH --mem=64G

# Add mamba environment executables to path
source /cbica/projects/grmpy/.bash_profile
PATH=$PATH:/cbica/projects/grmpy/miniforge3/envs/cubids/bin/
PATH=$PATH:/cbica/projects/grmpy/miniforge3/condabin/
PATH=$PATH:/cbica/projects/grmpy/data/bids_datalad/
PATH=$PATH:/cbica/projects/grmpy/data/bids_datalad/code/CuBIDS/
mamba activate cubids

# Run CuBIDS apply
cd /cbica/projects/grmpy/data/bids_datalad/code/CuBIDS/
/cbica/projects/grmpy/miniforge3/envs/cubids/bin/cubids apply /cbica/projects/grmpy/data/bids_datalad /cbica/projects/grmpy/data/bids_datalad/code/CuBIDS/v1_summary.tsv /cbica/projects/grmpy/data/bids_datalad/code/CuBIDS/v1_files.tsv v2 --use-datalad
