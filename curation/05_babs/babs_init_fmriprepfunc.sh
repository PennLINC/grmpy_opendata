project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/fmriprep-25-1-4-ds \
     --container-name fmriprep-25-1-4 \
     --container-config ${project_root}/code/curation/05_babs/fmriprep-25-1-4_func.yaml \
     --processing-level subject \
     --queue slurm \
     "${project_root}/data/BABS/derivatives/fmriprep_func"