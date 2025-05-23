#!/bin/bash
#SBATCH --job-name=aslprep
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -o /cbica/projects/grmpy/aslprep_test/logs/slurm-%j.out
#SBATCH -e /cbica/projects/grmpy/aslprep_test/logs/slurm-%j.err

# Check if subject ID is provided
if [ -z "$1" ]; then
    echo "Error: Subject ID not provided"
    echo "Usage: sbatch run_aslprep.sh <subject_id> <asl_type>"
    exit 1
fi

# Check if ASL type is provided
if [ -z "$2" ]; then
    echo "Error: ASL type not provided (must be 'label' or 'control')"
    echo "Usage: sbatch run_aslprep.sh <subject_id> <asl_type>"
    exit 1
fi

# Validate ASL type
if [ "$2" != "label" ] && [ "$2" != "control" ]; then
    echo "Error: ASL type must be 'label' or 'control'"
    echo "Usage: sbatch run_aslprep.sh <subject_id> <asl_type>"
    exit 1
fi

# Set subject ID and ASL type
subid=$1
asl_type=$2

# Run the singularity command
singularity run \
    -B "/cbica/projects/grmpy/aslprep_test" \
    -B "/cbica/projects/grmpy/templateflow":"/SGLR/TEMPLATEFLOW_HOME" \
    --env "TEMPLATEFLOW_HOME=/SGLR/TEMPLATEFLOW_HOME" \
    -B "/cbica/software/external/freesurfer/centos7/5.3.0/license.txt":"/SGLR/FREESURFER_HOME/license.txt" \
    --containall \
    --writable-tmpfs \
    /cbica/projects/grmpy/aslprep_test/aslprep-unstable.simg \
        "/cbica/projects/grmpy/aslprep_test/${asl_type}_first" \
        "/cbica/projects/grmpy/aslprep_test/${asl_type}_first_outputs" \
        participant \
        -w "/cbica/projects/grmpy/aslprep_test/wkdir" \
        --n_cpus ${SLURM_CPUS_PER_TASK} \
        --omp-nthreads ${SLURM_CPUS_PER_TASK} \
        --stop-on-first-crash \
        --fs-license-file /SGLR/FREESURFER_HOME/license.txt \
        --skip-bids-validation \
        --output-spaces MNI152NLin6Asym:res-2 \
        -v -v \
        --level full \
        --scorescrub \
        --basil \
        --fs-no-reconall \
        --fs-subjects-dir /cbica/projects/grmpy/aslprep_test/freesurfer/fmriprep_anat/ \
        --participant-label "${subid}"