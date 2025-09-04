#!/bin/bash -l
#SBATCH --job-name=cubids_apply
#SBATCH --output=/cbica/projects/grmpy/code/curation/04_cubids_curation/v3/cubids_apply_%A.out
#SBATCH --error=/cbica/projects/grmpy/code/curation/04_cubids_curation/v3/cubids_apply_%A.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=48:00:00        # Adjust time as needed
#SBATCH --mem=64G

# Add mamba environment executables to path ### CHECK v# in all paths below and in our/err outpaths!!!
source /cbica/projects/grmpy/.bash_profile
# PATH=$PATH:/cbica/projects/grmpy/miniforge3/envs/cubids/bin/
# PATH=$PATH:/cbica/projects/grmpy/miniforge3/condabin/
PATH=$PATH:/cbica/projects/grmpy/data/bids_datalad/
PATH=$PATH:/cbica/projects/grmpy/code/curation/04_cubids_curation/v3/

micromamba activate cubids
echo "hello world 2"

# Run CuBIDS apply
cd /cbica/projects/grmpy/data/bids_datalad/
cubids apply /cbica/projects/grmpy/data/bids_datalad /cbica/projects/grmpy/code/curation/04_cubids_curation/v2/v2_edited_summary.tsv /cbica/projects/grmpy/code/curation/04_cubids_curation/v2/v2_files.tsv /cbica/projects/grmpy/code/curation/04_cubids_curation/v3/v3 --use-datalad
