project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/xcp-d-0-12-0-ds \
     --container-name xcp-d-0-12-0 \
     --container-config ${project_root}/code/curation/05_babs/xcp-d-0-12-0.yaml \
     --processing-level subject \
     --queue slurm \
     "${project_root}/data/BABS/derivatives/xcp-d"