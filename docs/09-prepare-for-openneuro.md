---
title: "Prepare data for OpenNeuro and NeuroVault"
layout: default
nav_order: 10
---

# Prepare data for OpenNeuro and NeuroVault

## Raw BIDS data
First, the bids_datalad dataset must be updated following phenotype curation (see above).
Following phenotype curation, the participants.tsv was updated with the demographics from the [`build_participants_tmp.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/build_participants_tmp.py) script using the [`collide_participants_tmp.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/collide_participants_tmp.py) script (`86c16852`).

The task timing file `task-fracback_acq-singleband_events.tsv` was removed from the bids_datalad dataset as this has been deprecated and replaced with the individual events.tsv files (4fb4dafd).

`cp -RL data/bids_datalad/ /cbica/comp_space/grmpy/.`

From the new copied bids_datalad dataset:
```bash
mkdir derivatives
cp -r /cbica/projects/grmpy/data/derivatives/freesurfer-post/ derivatives/.
rsync -av --exclude='*errorts*' /cbica/projects/grmpy/data/derivatives/fracback-nortdur derivatives/.
rsync -av --exclude='*errorts*' /cbica/projects/grmpy/data/derivatives/fracback-rtdur derivatives/.
mdkir -p code/cubids
cp /cbica/projects/grmpy/code/curation/04_cubids_curation/v5/* code/cubids/.
mkdir phenotype
cp -r /cbica/projects/grmpy/code/phenotype/data/final/* phenotype/.
echo "GRMPY Raw data" > README.md
```

Now prepare the openeuro environment:
```bash
micromamba create -n openneuro
micromamba install -n openneuro -c conda-forge deno
micromamba activate openneuro
deno install -A --global jsr:@openneuro/cli -n openneuro
```

Now start a screen session and upload the dataset:
```bash
screen -S openneuro
micromamba activate openneuro
deno run -A jsr:@openneuro/cli login
# paste in API key when prompted. Select 'y' for error reporting.
openneuro upload --affirmDefaced /cbica/comp_space/grmpy/bids_datalad
```

TODO:
screen session. deno run
after upload - add protocol PDF to code/.

## fMRIPrep Anatomical Derivatives

```bash
cd /cbica/projects/grmpy/data/derivatives/fmriprep_anat
echo "GRMPY fMRIPrep Anatomical Derivatives" >> README.md
```
Add the following to the `.bidsignore` file:
```
log
figures
*space-*
*.shape.gii
```

Add some authors (not final list) to the `dataset_description.json` file:
```json
    "Authors": [
	    "S. Parker Singleton",
        "Brooke L. Sevchik",
        "Sage Rush",
        "Matt Cieslak",
        "Steven L. Meisler",
        "Taylor Salo",
        "Tien T. Tong",
        "Theodore D. Satterthwaite"
    ],
```

From a screen session:
`openneuro upload --affirmDefaced /cbica/projects/grmpy/data/derivatives/fmriprep_anat`

## QSIPrep Derivatives

```bash
cd /cbica/projects/grmpy/data/derivatives/qsiprep
cp /cbica/projects/grmpy/code/openneuro/qsiprep/* .
```

Use vim to clear the `.bidsignore` file and add the following:
```
*.html
logs
log
figures
*_xfm.*
*.surf.gii
*_dwiref.nii.gz
*_dwi.func.gii
*_desc-slice_qc.json
*.b_table.txt
*.b
*_dwimap.*
*_hmcOptimization.csv
*_qc.tsv
*_timeseries.tsv
*_rigid.mat
*.bvec
*.bval
*_dwi.nii.gz
*_dwi.json
*space-ACPC*
```

From a screen session:
```bash
micromamba activate openneuro
export OPENNEURO_LOG=DEBUG
openneuro upload --affirmDefaced . | tee /cbica/projects/grmpy/code/openneuro/qsiprep/upload$(date +%Y%m%d_%H%M).log
```

## ASLPrep Derivatives

```bash
cd /cbica/projects/grmpy/data/derivatives/aslprep
cp /cbica/projects/grmpy/code/openneuro/aslprep/* .
```

Use vim to clear the `.bidsignore` file and add the following:
```
atlases
*_asl.*
*_cbf.*
*.html
log
logs
figures
*_xfm.*
*_mixing.tsv
*_timeseries.tsv
*space-*
*atlas-*
*_mask.*
*_att.*
*_aslref.*
*.surf.gii
*.shape.gii
```

The dataset_description.json file needed some changes. See the [ASLPrep dataset_description.json](https://github.com/PennLINC/grmpy_opendata/blob/main/openneuro/aslprep/dataset_description.json) commit history for the changes.

From a screen session:
```bash
micromamba activate openneuro
export OPENNEURO_LOG=DEBUG
openneuro upload --affirmDefaced . | tee /cbica/projects/grmpy/code/openneuro/aslprep/upload$(date +%Y%m%d_%H%M).log
```
