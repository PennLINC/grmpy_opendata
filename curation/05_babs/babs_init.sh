project_root=/cbica/projects/grmpy
cd ${project_root}/data/BABS/exemplars/derivatives
babs-init \
     --where_project ${PWD} \
     --project_name fmriprepANAT \
     --input BIDS ${project_root}/data/BABS/exemplars/BIDS \
     --container_ds ${project_root}/data/BABS/apptainer-datasets/fmriprep-24-1-1-ds \
     --container_name fmriprep-24-1-1 \
     --container_config_yaml_file ${project_root}/code/curation/05_babs/config_fmriprepANAT.yaml \
     --type_session single-ses \
     --type_system slurm