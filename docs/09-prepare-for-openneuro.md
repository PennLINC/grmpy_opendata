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
script /cbica/projects/grmpy/code/openneuro/qsiprep/upload$(date +%Y%m%d_%H%M).log
deno run -A jsr:@openneuro/cli upload --affirmDefaced /cbica/projects/grmpy/data/derivatives/qsiprep
```

upload failed. Try again using the empty dataset:
```bash
script /cbica/projects/grmpy/code/openneuro/qsiprep/upload$(date +%Y%m%d_%H%M).log
deno run -A jsr:@openneuro/cli upload --dataset ds008238 /cbica/projects/grmpy/data/derivatives/qsiprep
```

Same error. Try downloading the dataset to comp_space and uploading from there.
First download the `git-annex-remote-openneuro` file:
```bash
cd ~
curl https://raw.githubusercontent.com/OpenNeuroOrg/openneuro/refs/heads/master/bin/git-annex-remote-openneuro -o git-annex-remote-openneuro
chmod +x git-annex-remote-openneuro
mv ~/git-annex-remote-openneuro /cbica/projects/grmpy/.local/bin/
```

Then upload the dataset:
```bash
cd /cbica/comp_space/grmpy
openneuro download ds008238 qsiprep
cd qsiprep
git config annex.private true
git annex init
cp -r /cbica/projects/grmpy/data/derivatives/qsiprep .
# the bidsignore file is missing. Add it.
cp /cbica/projects/grmpy/data/derivatives/qsiprep/.bidsignore .
git annex add -J8 .
git commit -m 'Added files'
git annex initremote openneuro type=external externaltype=openneuro encryption=none url=https://openneuro.org/git/1/ds008238
git annex copy --to=openneuro -J8
git push origin main git-annex
```

Failed on last step with authentication error. try:
```bash
git config --global credential.https://openneuro.org.useHttpPath true
git config --global credential.https://openneuro.org.helper "/gpfs/fs001/cbica/projects/grmpy/micromamba/envs/openneuro/bin/deno -A jsr:@openneuro/cli git-credential"
git push origin main git-annex
```
output:
```
error: Uncaught (in promise) BrokenPipe: Broken pipe (os error 32)
    at Object.print (ext:core/01_core.js:672:28)
    at Console.<anonymous> (ext:runtime/98_global_scope_shared.js:135:46)
    at console.log (ext:deno_console/01_console.js:3139:20)
    at console.log (file:///gpfs/fs001/cbica/projects/grmpy/.cache/deno/npm/registry.npmjs.org/@sentry/deno/8.55.2/index.mjs:9632:20)
    at Command.showHelp (https://jsr.io/@effigies/cliffy-command/1.0.0-dev.8/command.ts:2341:13)
    at commandLine (https://jsr.io/@openneuro/cli/5.3.0/src/options.ts:50:22)
    at eventLoopTick (ext:core/01_core.js:177:7)
    at async main (https://jsr.io/@openneuro/cli/5.3.0/mod.ts:21:5)
    at async https://jsr.io/@openneuro/cli/5.3.0/mod.ts:26:1
Enumerating objects: 15614, done.
Counting objects: 100% (15614/15614), done.
Delta compression using up to 40 threads
Compressing objects: 100% (13976/13976), done.
error: RPC failed; HTTP 500 curl 22 The requested URL returned error: 500
send-pack: unexpected disconnect while reading sideband packet
Writing objects: 100% (15610/15610), 10.89 MiB | 395.00 KiB/s, done.
Total 15610 (delta 866), reused 0 (delta 0), pack-reused 0
fatal: the remote end hung up unexpectedly
Everything up-to-date
```

With some other help from opus, confirmed that the dataset is corrupted on the openneuro side.

Will try one more attempt. First copy over just a few things to a new comp_space dir and upload as a new dataset:
```bash
cd /cbica/comp_space/grmpy
chmod -R u+w qsiprep/
rm -rf qsiprep
mkdir qsiprep && cd qsiprep
# copy over dataset_description.json, README.md, and .bidsignore from qsiprep dataset and one subject dir
screen
micromamba activate openneuro
deno run -A jsr:@openneuro/cli upload --affirmDefaced /cbica/comp_space/grmpy/qsiprep/.
```

This upload was successful. Will now try to upload the entire dataset.
First will try copying into this dataset and uploading from there.
If that doesn't work, will try downloading the dataset from openneuro to comp_space and uploading from there via git annex.

```bash
cp -r /cbica/projects/grmpy/data/derivatives/qsiprep/. .
deno run -A jsr:@openneuro/cli upload --dataset ds008291 /cbica/comp_space/grmpy/qsiprep/.
```
