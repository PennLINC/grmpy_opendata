project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/qsiprep-1-0-1-ds \
     --container-name qsiprep-1-0-1 \
     --container-config ${project_root}/code/curation/05_babs/qsiprep-1-0-1.yaml \
     --processing-level subject \
     --queue slurm \
     "${project_root}/data/BABS/derivatives/qsiprep"