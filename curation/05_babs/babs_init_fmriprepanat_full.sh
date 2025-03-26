project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     ${PWD}/fmriprepANAT \
     --datasets BIDS=${project_root}/data/bids_datalad/ \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/fmriprep-24-1-1-ds \
     --container-name fmriprep-24-1-1 \
     --container-config ${project_root}/code/curation/05_babs/fmriprep-24-1-1_anatonly.yaml \
     --processing-level subject \
     --queue slurm