---
title: "Prepare data for OpenNeuro and NeuroVault"
layout: default
nav_order: 10
---

# Prepare data for OpenNeuro and NeuroVault

## Raw BIDS data
First, the bids_datalad dataset must be updated following phenotype curation (see above).
Following phenotype curation, the participants.tsv was updated with the demographics from the [`build_participants_tmp.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/build_participants_tmp.py) script using the [`collide_participants_tmp.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/collide_participants_tmp.py) script (`dda40dae`).

The task timing file `task-fracback_acq-singleband_events.tsv` was removed from the bids_datalad dataset as this has been deprecated and replaced with the individual events.tsv files (`ec68f693`).

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
cp /cbica/projects/grmpy/code/openneuro/bids/dataset_description.json .
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
screen -S upload-bids
bash /cbica/projects/grmpy/code/openneuro/bids/upload-bids.sh
```

The upload succeeded and the dataset is now available at [**ds008579**](https://openneuro.org/datasets/ds008579).

TODO:
after upload - add protocol PDF to code/.


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

This upload took ~1 week on CUBIC using the 5.3.0 CLI.

There are 39 corrupted files in the openneuro dataset, so will try re-uploading with the patched version of the 5.4.0 CLI:

```bash
screen -S upload-aslprep
micromamba activate openneuro
bash /cbica/projects/grmpy/code/openneuro/aslprep/upload-aslprep.sh
```

## QSIRecon Derivatives

ASLPrep is taking so long and CUBIC will be shutdown for upgrades soon.
Going to try out PARCC.

QSIRecon was rsynced to PARCC (from a screen session):

```bash
rsync -avzh --partial --append-verify --info=progress2 /cbica/projects/grmpy/data/derivatives/qsirecon sps253@login.betty.parcc.upenn.edu:/ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives | tee log.txt
```


Now, on PARCC. Micromamba env was created following the above steps.


```bash
micromamba activate openneuro
cp /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/* .
```

Bidsignore:

```
*.html
log/
sub-*/log
logs/
figures/
*_xfm.*
*.surf.gii
*_boldref.nii.gz
*_bold.func.gii
*_mixing.tsv
*_timeseries.tsv
*space-ACPC*
```

```bash
export OPENNEURO_LOG=DEBUG
openneuro upload --affirmDefaced . | tee /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/qsirecon/upload$(date +%Y%m%d_%H%M).log
```

This initially failed on PARCC: every file reported `could not be added, check if this
file is accessible and not a broken symlink`, despite the tree containing no symlinks.
The cause was three separate OpenNeuro CLI bugs, all now fixed upstream.

| Bug | Issue | Fix |
|---|---|---|
| `setup`/`clone` messages dropped before the git worker finished loading, leaving `context` undefined | [#4040](https://github.com/OpenNeuroOrg/openneuro/issues/4040) | [#4035](https://github.com/OpenNeuroOrg/openneuro/pull/4035), released in CLI 5.4.0 |
| The underlying error was swallowed and misreported as a broken symlink | — | [#4042](https://github.com/OpenNeuroOrg/openneuro/pull/4042) |
| git-annex branch committed once per annex key (quadratic; the upload hung for 32h) | [#4047](https://github.com/OpenNeuroOrg/openneuro/issues/4047) | [#4048](https://github.com/OpenNeuroOrg/openneuro/pull/4048) |

Uploaded with CLI 5.4.0 plus the #4048 patch, deployed at
`/ceph/projects/sattertt/pennlinc-parcc/grmpy/openneuro-cli-patched`.

Scripts in [`openneuro/qsirecon/parcc/`](../openneuro/qsirecon/parcc/):

- [`upload-reroutestdout.sbatch`](../openneuro/qsirecon/parcc/upload-reroutestdout.sbatch) — the upload job
- [`upload-resume.sbatch`](../openneuro/qsirecon/parcc/upload-resume.sbatch) — resume run; reuses the accession so
  already-stored keys are skipped, and preserves `.git` so a failed push can be retried
- [`pushmain.sbatch`](../openneuro/qsirecon/parcc/pushmain.sbatch) — recovery helper

Two problems remain unsolved and needed manual work:

- Deno aborts with `WouldBlock: Resource temporarily unavailable (os error 11)` under high
  log volume, even writing to a regular file on CephFS. Keep `OPENNEURO_LOG` low, or expect
  to restart the job.
- The CLI's final `git push` of `main` times out on a large tree (the timeout comes from
  Deno's node-http shim and is not configurable). Push it with system git from the
  preserved `.git` — see `pushmain.sbatch`.

Result: [**ds008547**](https://openneuro.org/datasets/ds008547) — 65,560 files, 226 GB.


## fMRIPrep Anatomical Derivatives

```bash
cd /ceph/projects/sattertt/pennlinc-parcc/grmpy/data/derivatives/fmriprep_anat
cp /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/fmriprep_anat/* .
```

Bidsignore:
```
*.html
log
logs
figures
*_xfm.*
*.surf.gii
*_boldref.*
*_bold.func.gii
*_mixing.tsv
*_timeseries.*
*T2starmap*
*_fieldmap.*
*space-*
*.shape.gii
*mask.nii.gz
*mask.json
*mask.label.gii
```

Validate before submitting the upload sbatch:

```bash
micromamba activate openneuro
deno run -A jsr:@bids/validator .
sbatch /ceph/projects/sattertt/pennlinc-parcc/grmpy/code/openneuro/fmriprep_anat/parcc/upload.sbatch
```

## fMRIPrep Functional Derivatives

```bash
cd /cbica/projects/grmpy/data/derivatives/fmriprep_func
cp /cbica/projects/grmpy/code/openneuro/fmriprep_func/* .
```

Bidsignore:
```
*.html
log
logs
figures
*_xfm.*
*.surf.gii
*_boldref.*
*_bold.func.gii
*_mixing.tsv
*_timeseries.*
*T2starmap*
*_fieldmap.*
*space-*
*.shape.gii
*mask.nii.gz
*mask.json
*mask.label.gii
```

Validate before submitting the upload script:

```bash
screen -S upload-fmriprep-func
micromamba activate openneuro
deno run -A jsr:@bids/validator .
bash /cbica/projects/grmpy/code/openneuro/fmriprep_func/upload-fmriprep-func.sh
```

Upload succeeded and the dataset is now available at [**ds008590**](https://openneuro.org/datasets/ds008590).


## XCPD Derivatives

```bash
cd /cbica/projects/grmpy/data/derivatives/xcpd
cp /cbica/projects/grmpy/code/openneuro/xcpd/* .
```


Create a .bidsignore file and add the following:
```
*_qc.*
*_design.*
*_motion.*
atlases
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
```

Validate before submitting the upload script:

```bash
screen -S upload-xcpd
micromamba activate openneuro
deno run -A jsr:@bids/validator .
bash /cbica/projects/grmpy/code/openneuro/xcpd/upload-xcpd.sh
```
