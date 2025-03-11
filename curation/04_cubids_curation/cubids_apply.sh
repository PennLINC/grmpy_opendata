#!/bin/bash
#SBATCH --job-name=cubids_apply
#SBATCH --output=/cbica/projects/grmpy/code/curation/04_cubids_curation/v7/cubids_apply_%A.out
#SBATCH --error=/cbica/projects/grmpy/code/curation/04_cubids_curation/v7/cubids_apply_%A.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=48:00:00        # Adjust time as needed
#SBATCH --mem=64G

# Add mamba environment executables to path ### CHECK v# in all paths below and in our/err outpaths!!!
source /cbica/projects/grmpy/.bash_profile
PATH=$PATH:/cbica/projects/grmpy/miniforge3/envs/cubids/bin/
PATH=$PATH:/cbica/projects/grmpy/miniforge3/condabin/
PATH=$PATH:/cbica/projects/grmpy/data/bids_datalad/
PATH=$PATH:/cbica/projects/grmpy/code/curation/04_cubids_curation/v7/
mamba activate cubids

# Run CuBIDS apply
cd /cbica/projects/grmpy/data/bids_datalad/
/cbica/projects/grmpy/miniforge3/envs/cubids/bin/cubids apply /cbica/projects/grmpy/data/bids_datalad /cbica/projects/grmpy/code/curation/04_cubids_curation/v6/v6_summary.tsv /cbica/projects/grmpy/code/curation/04_cubids_curation/v6/v6_files.tsv /cbica/projects/grmpy/code/curation/04_cubids_curation/v7/v7 --use-datalad
