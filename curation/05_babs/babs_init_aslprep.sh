project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/aslprep-25-1-0-ds \
     --container-name aslprep-25-1-0 \
     --container-config ${project_root}/code/curation/05_babs/aslprep-25-1-0.yaml \
     --processing-level subject \
     --queue slurm \
     "${project_root}/data/BABS/derivatives/aslprep"