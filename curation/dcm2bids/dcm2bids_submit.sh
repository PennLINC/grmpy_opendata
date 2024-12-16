#!/bin/bash
#SBATCH --job-name=dcm2bids_conversion  # Job name
#SBATCH --array=0-1
#SBATCH --time=24:00:00                 # Maximum runtime
#SBATCH --cpus-per-task=4               # Number of CPUs per task
#SBATCH --mem=8G                        # Memory per job
#SBATCH --output=/cbica/projects/grmpy/code/curation/dcm2bids/logs/dcm2bids_%A_%a.out # Output log
#SBATCH --error=/cbica/projects/grmpy/code/curation/dcm2bids/logs/dcm2bids_%A_%a.err  # Error log

# Define paths
bids="/cbica/projects/grmpy/data/bids"

# Step 1: Get all subject IDs
subjects=($(ls -d /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS/* | xargs -n 1 basename))

# Step 2: Select the current subject based on the SLURM array task ID
subID=${subjects[${SLURM_ARRAY_TASK_ID}]}

# Step 3: Find all DICOM directories for all sessions of the current subject
mapfile -t session_dirs < <(find /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS/${subID}/SESSIONS/*/ACQUISITIONS -maxdepth 0 -type d)

# Step 4: Process each session
session_num=1  # Initialize session counter
for session_dir in "${session_dirs[@]}"; do

    echo "Processing session ${session_num} for subject ${subID} in directory ${session_dir}"  # For debugging

    ~/miniforge3/envs/dcmconv/bin/dcm2bids -p ${subID} \
        -s ${session_num} \
        -c /cbica/projects/grmpy/code/dcm2bids/config.json \
        -o ${bids} \
        -d ${session_dir} \
        --force_dcm2bids
        
    ((session_num++))
    
done
