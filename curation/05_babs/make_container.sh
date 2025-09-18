#!/bin/bash

# Prompt user for input values
read -p "Enter application name (e.g., fmriprep): " app
read -p "Enter version (e.g., 24.1.1): " version
read -p "Enter version with dashes (e.g., 24-1-1): " version_dash
read -p "Enter host (e.g., nipreps): " host

# Define paths
apptainer_path=/cbica/projects/grmpy/data/BABS/apptainer
apptainer_ds_path=/cbica/projects/grmpy/data/BABS/apptainer-datasets

# Build the container
echo "Building ${app} container version ${version}..."
singularity build \
    ${apptainer_path}/${app}-${version}.sif \
    docker://${host}/${app}:${version}

# Create DataLad dataset
echo "Creating DataLad dataset for ${app}..."

# If app contains an underscore, replace it with a dash (datalad only allows alphanumeric characters and dashes)
if [[ ${app} == *"_"* ]]; then
    app_dash=${app//_/-}
else
    app_dash=${app}
fi

datalad create -D "Create ${app}-${version} DataLad dataset" ${apptainer_ds_path}/${app_dash}-${version_dash}-ds
cd ${apptainer_ds_path}/${app_dash}-${version_dash}-ds
datalad containers-add \
    --url ${apptainer_path}/${app}-${version}.sif \
    ${app_dash}-${version_dash}