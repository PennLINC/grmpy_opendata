---
title: "05: BABS"
layout: default
nav_order: 6
---

# 05: BABS

`BABS` was installed in the micromamba environment `babs` from source code.
VERSION: v0.5.3.dev4+geca256596

The general process for setting up BABS is described in the [BABS documentation](https://github.com/PennLINC/BABS).
Here, I will describe the specifc workflow that was used for grmpy:

In the `/cbica/projects/grmpy/data/BABS/` directory, three directories were made: `apptainer`, `apptainer-datasets`, and `derivatives`.
The `apptainer` directory was used to store the apptainer containers.
The `apptainer-datasets` directory was used to store the datalad datasets for the apptainer containers.
The `derivatives` directory will store the BABS projects.

To set up the apptainer containers, the [`make_container.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/make_container.sh) script was used, passing argmuments for the most recent stable version of each app that was on DockerHub at the time.

## MRIQC

VERSION: 25.0.0rc0

The MRIQC BABS project was set up with the [`babs_init_mriqc.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_mriqc.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

grep -L "SUCCESS" /gpfs/fs001/cbica/projects/grmpy/data/BABS/derivatives/mriqc/analysis/logs/*

11114170_213 - sub-95116 - nan value error
11114170_6 - sub-105168 - nan value error
11114170_202 - sub-93517 - time limit - this one completed successfully on second run
11114170_203 - sub-93549 - nan value error
11114170_172 - sub-88209 - Input inhomogeneity-corrected data seem empty. This is probably related to the nan error.

227 out of 231 subjects completed successfully.

`babs merge` was run to merge the output results branches.

## fMRIPrep: Anatomical Only

VERSION: 25.1.4

The fMRIPrep container was set up with the [`babs_init_fmriprepanat.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_fmriprepanat.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

One job failed:
11116678_13 - sub-106071 - no T1w image

230 out of 231 subjects completed successfully.

`babs merge` was run to merge the output results branches.

## QSIPREP

VERSION: 1.0.1

The QSIPREP container was set up with the [`babs_init_qsiprep.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_qsiprep.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

grep -L "SUCCESS" /gpfs/fs001/cbica/projects/grmpy/data/BABS/derivatives/qsiprep/analysis/logs/*

e11120649_13 - sub-106071 - no T1w image

`grep -L "SUCCESS" *e* | xargs grep -l "No dwi images found" | xargs grep -oE "sub-[0-9]+" | sort -u`
all others - no dwi images
qsi.e11120649_11:sub-105979
qsi.e11120649_136:sub-82051
qsi.e11120649_137:sub-82063
qsi.e11120649_138:sub-82492
qsi.e11120649_139:sub-82790
qsi.e11120649_140:sub-83010
qsi.e11120649_144:sub-83999
qsi.e11120649_145:sub-84103
qsi.e11120649_149:sub-84973
qsi.e11120649_151:sub-85173
qsi.e11120649_154:sub-85853
qsi.e11120649_155:sub-86287
qsi.e11120649_156:sub-86350
qsi.e11120649_157:sub-86444
qsi.e11120649_160:sub-86924
qsi.e11120649_162:sub-87135
qsi.e11120649_165:sub-87457
qsi.e11120649_166:sub-87538
qsi.e11120649_170:sub-87804
qsi.e11120649_171:sub-87990
qsi.e11120649_172:sub-88209
qsi.e11120649_178:sub-88773
qsi.e11120649_197:sub-93169
qsi.e11120649_205:sub-93734
qsi.e11120649_207:sub-93856
qsi.e11120649_222:sub-98394
qsi.e11120649_226:sub-98831
qsi.e11120649_231:sub-99964
qsi.e11120649_23:sub-110168
qsi.e11120649_27:sub-112061
qsi.e11120649_28:sub-112126
qsi.e11120649_2:sub-103679
qsi.e11120649_32:sub-113111
qsi.e11120649_34:sub-114713
qsi.e11120649_37:sub-114990
qsi.e11120649_39:sub-116019
qsi.e11120649_40:sub-116051
qsi.e11120649_41:sub-116210
qsi.e11120649_43:sub-116360
qsi.e11120649_44:sub-117226
qsi.e11120649_46:sub-118393
qsi.e11120649_49:sub-119302
qsi.e11120649_50:sub-119791
qsi.e11120649_55:sub-121085
qsi.e11120649_57:sub-121476
qsi.e11120649_62:sub-122916
qsi.e11120649_65:sub-125554
qsi.e11120649_69:sub-126903
qsi.e11120649_75:sub-127542
qsi.e11120649_79:sub-129354
qsi.e11120649_84:sub-129926
qsi.e11120649_86:sub-130211
qsi.e11120649_89:sub-130896
qsi.e11120649_96:sub-139272

176 out of 231 subjects completed successfully.

`babs merge` was run to merge the output results branches.

## ASLPrep

VERSION: 25.1.0

The ASLPrep container was set up with the [`babs_init_aslprep.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_aslprep.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

There's some weird issue with aslprep where the job exits for an unknown error _after_ aslprep has completed. We modified the `participant_job.sh` script (in the `analysis/code` directory of the BABS project) to not exit during the `datalad run` command by placing `set +e` before the `datalad run` command and `set -e` after the `datalad run` command (to turn it back on). This file was datalad saved in the babs project `analysis` directory (`2cd72cc`) and `babs sync-code` was run from the babs project directory to sync the change across branches.

```
230 job(s) have been submitted; 0 job(s) haven't been submitted.

Among submitted jobs,
214 job(s) successfully finished;
0 job(s) are pending;
0 job(s) are running;
0 job(s) failed.
```

There were only 214 subjects that had asl timeseries, so this is done.

`babs merge` was run to merge the output results branches.
`babs merge` failed! There are no results in any of the output results branches!
This is likely some ASLPrep bug. Will need to debug.

This babs project was burned and re-initialized after changing the job compute space to `/cbica/comp_space/grmpy/` in the `aslprep-25-0-0.yaml` file.
There jobs were submitted: `babs submit --select sub-99949 sub-99964 sub-90021`.

Identified a bug that hopefully is now fixed. Will re-run the jobs.

The project was re-initialized and submitted after aslprep was updated to 25.1.0.

190 finished successfully.

3 subjects timed out (twice):
11275422_22 - sub-125535
11275422_5 - sub-105860
11275422_6 - sub-105979

18 subjects failed due to lack of M0 scans:
`grep -l "Background-suppressed control volumes cannot be used for calibration" *e11422* | xargs grep -oE "sub-[0-9]+" | sort -u`
asl.e11275422_11:sub-109735
asl.e11275422_12:sub-112028
asl.e11275422_16:sub-116360
asl.e11275422_1:sub-104059
asl.e11275422_20:sub-122528
asl.e11275422_23:sub-126389
asl.e11275422_25:sub-130687
asl.e11275422_28:sub-133220
asl.e11275422_29:sub-19977
asl.e11275422_2:sub-104785
asl.e11275422_31:sub-20197
asl.e11275422_32:sub-20322
asl.e11275422_36:sub-20888
asl.e11275422_39:sub-81725
asl.e11275422_42:sub-83372
asl.e11275422_49:sub-90021
asl.e11275422_4:sub-105176
asl.e11275422_9:sub-106802

16 subjects had no ASL data:
`grep -l "No ASL images found for participant" *e11275422* | xargs grep -oE "sub-[0-9]+" | sort -u`
asl.e11275422_13:sub-113111
asl.e11275422_15:sub-116210
asl.e11275422_17:sub-118393
asl.e11275422_18:sub-118990
asl.e11275422_19:sub-121476
asl.e11275422_24:sub-129354
asl.e11275422_26:sub-130896
asl.e11275422_30:sub-20120
asl.e11275422_35:sub-20809
asl.e11275422_40:sub-82063
asl.e11275422_44:sub-85369
asl.e11275422_45:sub-86287
asl.e11275422_47:sub-87457
asl.e11275422_51:sub-90683
asl.e11275422_52:sub-93274
asl.e11275422_54:sub-95257

1 subject had M0 file not found error:
asl.e11275422_34: sub-20699
NOTE: this subject had their M0 scan purged from the dataset due to abnormal VoxelDim3 size. The ASL scan should have its variant updated to reflect this.

1 subject failed due to lack of good voxels:
asl.e11275422_37: sub-20974

1 subject failed due to file not found error:
asl.e11275422_38: sub-80688

`babs merge` was run to merge the output results branches.

TODO: Remove perf dirs from subjects with no M0 scans (including sub-20699 and sub-20809 which had M0 scans purged)

## fMRIPrep: Functional Only

VERSION: 25.1.4

The fMRIPrep container was set up with the [`babs_init_fmriprepfunc.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_fmriprepfunc.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

```
There are in total of 230 jobs to complete.

230 job(s) have been submitted; 0 job(s) haven't been submitted.

Among submitted jobs,
230 job(s) successfully finished;
All jobs are completed!
```

`babs merge` was run to merge the output results branches.

## Freesurfer Post

VERSION: 0.1.2

The Freesurfer Post container was set up with the [`babs_init_freesurferpost.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_freesurferpost.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

```
230 job(s) have been submitted; 0 job(s) haven't been submitted.

Among submitted jobs,
230 job(s) successfully finished;
All jobs are completed!
```

`babs merge` was run to merge the output results branches.

## QSirecon


VERSION: 1.1.1

The QSirecon container was set up with the [`babs_init_qsirecon.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_qsirecon.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

```
176 job(s) have been submitted; 0 job(s) haven't been submitted.

Among submitted jobs,
176 job(s) successfully finished;
All jobs are completed!
```

`babs merge` was run to merge the output results branches.

## XCP-D

VERSION: 0.12.0

The XCP-D container was set up with the [`babs_init_xcpd.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_xcpd.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.

```
230 job(s) have been submitted; 0 job(s) haven't been submitted.

Among submitted jobs,
230 job(s) successfully finished;
All jobs are completed!
```

`babs merge` was run to merge the output results branches.

TODO: update the yamls on the babs-cubic-yaml repo; seff_array each project to get a sense of resource usage
