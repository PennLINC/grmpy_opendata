project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/freesurfer-post-0-1-2-ds \
     --container-name freesurfer-post-0-1-2 \
     --container-config ${project_root}/code/curation/05_babs/freesurfer-post-0-1-2.yaml \
     --processing-level subject \
     --queue slurm \
     "${project_root}/data/BABS/derivatives/freesurfer-post"