#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=48:00:00
#SBATCH --output=/cbica/projects/grmpy/data/bids/code/download_dcms/logs/download_dcms-%A.out
#SBATCH --error=/cbica/projects/grmpy/data/bids/code/download_dcms/logs/download_dcms-%A.err

unset LD_LIBRARY_PATH
/cbica/projects/grmpy/glibc-2.34/lib/ld-linux-x86-64.so.2 /cbica/projects/grmpy/linux_amd64/fw sync -m --include dicom fw://bbl/GRMPY_822831 /cbica/projects/grmpy/data/bids/sourcedata/
