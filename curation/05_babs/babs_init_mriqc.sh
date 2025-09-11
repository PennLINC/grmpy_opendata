project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/derivatives
export TEMPLATEFLOW_HOME=${PWD}/templateflow_home
mkdir -p ${TEMPLATEFLOW_HOME}
babs init \
     --container-ds ${project_root}/data/BABS/apptainer-datasets/mriqc-25-0-0rc0-ds \
     --container-name mriqc-25-0-0rc0 \
     --container-config ${project_root}/code/curation/05_babs/mriqc-25-0-0rc0.yaml \
     --processing-level subject \
     --queue slurm \
     "${project_root}/data/BABS/derivatives/mriqc"