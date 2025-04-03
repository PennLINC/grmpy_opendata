project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     ${PWD}/fmriprep \
     --datasets BIDS=${project_root}/data/bids_datalad/ fmriprep_anat=${project_root}/derivatives/fmriprep_anat \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/fmriprep-25-0-0-ds \
     --container-name fmriprep-25-0-0 \
     --container-config ${project_root}/code/curation/05_babs/fmriprep-25-0-0_ingressed-fs.yaml \
     --processing-level subject \
     --queue slurm