---
title: Data Narrative
layout: page
nav_order: 2
---

# Table of Contents

1. [Getting data from flywheel](#01-getting-data-from-flywheel)
2. [Converting to bids](#02-converting-to-bids)
3. [Creating timing files](#03-creating-timing-files)
4. [CuBIDS](#04-cubids)
   - [Removing metadata fields](#removing-metadata-fields)
   - [Checking into datalad and initial validation](#checking-into-datalad-and-initial-validation)
   - [CuBIDS group and apply](#cubids-group-and-apply)
5. [BABS](#05-babs)
   - [MRIQC](#mriqc)
   - [fMRIPrep: Anatomical Only](#fmriprep-anatomical-only)
   - [QSIPREP](#qsiprep)
   - [ASLPrep](#aslprep)
   - [fMRIPrep: Functional Only](#fmriprep-functional-only)
   - [Freesurfer Post](#freesurfer-post)
   - [QSirecon](#qsirecon)
   - [XCP-D](#xcp-d)
6. [QC](#06-qc)
   - [XCP-D QC](#xcp-d-qc)
     - [Motion Assessment](#motion-assessment)
     - [Parcel Coverage Analysis](#parcel-coverage-analysis)
   - [QSI QC](#qsi-qc)
     - [QSIPrep Quality Metrics](#qsiprep-quality-metrics)
     - [DSI Studio Bundle Analysis](#dsi-studio-bundle-analysis)
   - [ASLPrep QC](#aslprep-qc)
   - [FreeSurfer-Post QC](#freesurfer-post-qc)
   - [T1w QC manual ratings](#t1w-qc-manual-ratings)
7. [Analysis](#post-processing)
8. [Phenotypic Data](#phenotypic-data)
9. [Helpful hints](#helpful-hints)

# 01: Getting data from flywheel

The data download process is handled by our [`download_dcms.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/01_download_dcms/download_dcms.sh) script, which uses the Flywheel CLI to sync DICOM files.

This command syncs DICOM files from our Flywheel project to our local storage.

Here's the key part of the script:
```bash
/cbica/projects/grmpy/linux_amd64/fw sync -m --include dicom \
fw://bbl/GRMPY_822831 \
/cbica/projects/grmpy/sourcedata/
```

# 02: Converting to bids

After downloading DICOM files via Flywheel, the [`dcm2bids_submit.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/02_dcm2bids/dcm2bids_submit.sh) script converts these files (located in `cbica/projects/grmpy/source_data`) into the BIDS format (bids outputs in `cbica/projects/grmpy/data/bids`).
It selects a subject based on the SLURM array task ID, finds all session directories with DICOM data for that subject, and then processes each session with the `dcm2bids` tool, ensuring that the converted data is properly organized in the BIDS directory.

Two subjects (`95257` and `20120`) had multiple sessions. For `95257`, the first visit's scans were stopped due to technical difficulties with the O2 detector that day.
On the second visit, the scan was completed, however, lmscribe stopped working and all fMRI sequences had to be completed straight on rather than adjusted. For `20120`, the first visit was completed with an earring.
The participant came back for a second session with a plastic holder in their ear. In both cases, we kept the second session and deleted the first (performed below in the initial CuBIDS stages).

# 03: Creating timing files

Timing files were created manually for the nback task following the [`create_fracback_events.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/03_create_events/create_fracback_events.py) script.

Timing files still need to be created for FACES.

# 04: CuBIDS

CuBIDS was installed in the micromamba environment `cubids` from source code.
VERSION: v1.2.1.dev5+g0be1b9a26

The git hashes referenced in this section refer to the datalad commit hashes and can be retrieved by running `git log --oneline` in the datalad dataset.

## Removing metadata fields
The following metadata fields were present in the bids data:
```
1-Localizer
10-restingBOLD_mb6_1200
11-bbl1_restbold1_124mb
12-ASL_3DSpiral_OnlineRecon
13-ASL_3DSpiral_OnlineRecon
14-ASL_3DSpiral_OnlineRecon
15-DTI_MultiShell_117dir
16-DTI_MultiShell_117dir
17-DTI_MultiShell_topup_ref
18-bbl1_fracback1_231mb
2-MPRAGE_TI1100_ipat2
3-T2_sagittal_SPACE
4-TOF_3D_multi-slab_R2
5-TOF_3D_multi-slab_R2
6-TOF_3D_multi-slab_R2
7-TOF_3D_multi-slab_R2
8-B0map
9-B0map
Acknowledgments
AcquisitionMatrixPE
AcquisitionNumber
AcquisitionTime
ArterialSpinLabelingType
Authors
B0FieldIdentifier
B0FieldSource
BIDSVersion
BandwidthPerPixelPhaseEncode
BaseResolution
BidsGuess
BodyPartExamined
CoilCombinationMethod
CoilString
ConsistencyInfo
ConversionSoftware
ConversionSoftwareVersion
DatasetDOI
Dcm2bidsVersion
DerivedVendorReportedEchoSpacing
DeviceSerialNumber
DiffusionScheme
DwellTime
EchoNumber
EchoTime
EchoTime1
EchoTime2
EchoTrainLength
EffectiveEchoSpacing
FlipAngle
FrameTimesStart
Funding
HowToAcknowledge
ImageComments
ImageOrientationPatientDICOM
ImageOrientationText
ImageType
ImagingFrequency
InPlanePhaseEncodingDirectionDICOM
InstitutionAddress
InstitutionName
InstitutionalDepartmentName
IntendedFor
InversionTime
License
M0Type
MRAcquisitionType
MagneticFieldStrength
Manufacturer
ManufacturersModelName
MatrixCoilMode
Modality
MultibandAccelerationFactor
Name
NonlinearGradientCorrection
ParallelReductionFactorInPlane
PartialFourier
PatientPosition
PercentPhaseFOV
PercentSampling
PhaseEncodingDirection
PhaseEncodingSteps
PhaseResolution
PixelBandwidth
ProcedureStepDescription
ProtocolName
PulseSequenceDetails
ReceiveCoilActiveElements
ReceiveCoilName
ReconMatrixPE
RefLinesPE
ReferencesAndLinks
RepetitionTime
RepetitionTimeExcitation
SAR
ScanOptions
ScanningSequence
SequenceName
SequenceVariant
SeriesDescription
SeriesNumber
ShimSetting
SliceThickness
SliceTiming
SoftwareVersions
SpacingBetweenSlices
SpoilingState
StationName
TaskName
TotalReadoutTime
TxRefAmp
VariableFlipAngleFlag
WipMemBlock
acq_time
age
filename
group
operator
randstr
sex
```

The strange fields at the top were in a hidden `.heudiconv` folder and removed.
`acq_time` was in a scans.tsv and was deleted.
`operator` was removed for PHI reasons.
`AcquisitionTime` was rounded to the nearest hour using the [`round_AcquisitionTime.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/round_AcquisitionTime.py) script.

Here are the new set of metadata fields that will be checked into datalad:

```
Acknowledgments
AcquisitionMatrixPE
AcquisitionNumber
AcquisitionTime
ArterialSpinLabelingType
Authors
B0FieldIdentifier
B0FieldSource
BIDSVersion
BandwidthPerPixelPhaseEncode
BaseResolution
BidsGuess
BodyPartExamined
CoilCombinationMethod
CoilString
ConsistencyInfo
ConversionSoftware
ConversionSoftwareVersion
DatasetDOI
Dcm2bidsVersion
DerivedVendorReportedEchoSpacing
DeviceSerialNumber
DiffusionScheme
DwellTime
EchoNumber
EchoTime
EchoTime1
EchoTime2
EchoTrainLength
EffectiveEchoSpacing
FlipAngle
FrameTimesStart
Funding
HowToAcknowledge
ImageComments
ImageOrientationPatientDICOM
ImageOrientationText
ImageType
ImagingFrequency
InPlanePhaseEncodingDirectionDICOM
InstitutionAddress
InstitutionName
InstitutionalDepartmentName
IntendedFor
InversionTime
License
M0Type
MRAcquisitionType
MagneticFieldStrength
Manufacturer
ManufacturersModelName
MatrixCoilMode
Modality
MultibandAccelerationFactor
Name
NonlinearGradientCorrection
ParallelReductionFactorInPlane
PartialFourier
PatientPosition
PercentPhaseFOV
PercentSampling
PhaseEncodingDirection
PhaseEncodingSteps
PhaseResolution
PixelBandwidth
ProcedureStepDescription
ProtocolName
PulseSequenceDetails
ReceiveCoilActiveElements
ReceiveCoilName
ReconMatrixPE
RefLinesPE
ReferencesAndLinks
RepetitionTime
RepetitionTimeExcitation
SAR
ScanOptions
ScanningSequence
SequenceName
SequenceVariant
SeriesDescription
SeriesNumber
ShimSetting
SliceThickness
SliceTiming
SoftwareVersions
SpacingBetweenSlices
SpoilingState
StationName
TaskName
TotalReadoutTime
TxRefAmp
VariableFlipAngleFlag
WipMemBlock
age
group
sex
```
NOTE:
`age`, `sex`, and `group` are in a (for now) empty `participants.json` and `Name` is the dataset name in `dataset_description.json`.

## Checking into datalad and initial validation

The bids data in `/cbica/projects/grmpy/data/bids` was checked into a datalad dataset at `cbica/projects/grmpy/data/bids_datalad` (`2e6a541`) and nifti info was added into the json sidecars (`297f150`) using CuBIDS.

The fmap sidecar `IntendedFor` fields were known to have an issue and updated to use relative paths instead of full BIDS uris, using the [`fix_intendedfor.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/fix_intendedfor.py) script (`ee2ce91`).

A participants.tsv was initialized using [`initialize_participants_tsv.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/initialize_participants_tsv.py) (`c2dba55`).

The pre-existing ASL data was removed (e.g. `git rm sub-*/ses-*/perf/*`) (`1404c9b`).

The perfusion data from the aslprep project (`/cbica/projects/aslprep/2022_adebimpe/IRRdata/curation/BIDS/`) was copied over to grmpy and then copied into the `bids_datalad` dataset with [`copy_perfusion_data.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/copy_perfusion_data.py) (`80e737db`).

The two before-mentioned subjects with a second session had both sessions initially checked into datalad. Those have now had their first sessions removed and the second sessions renamed to ses-1. The fmap intendefor paths were also updated. This was all done using [`fix_sessions.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/fix_sessions.py) (`023ba76d`).

Bids is not compatable with minIP images. Those were added to a `.bidsignore` (`echo "*/ses*/anat/*minIP*" >> .bidsignore`) (`e3374d60`).

T1w images were refaced and T2w images were defaced with [`reface_anatomicals.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/reface_anatomicals.sh) (`a43502af`).

`cubids validate v0` was run to check for validation errors. Many errors were for missing sidecar info in perfusion jsons, a `PARTICIPANT_ID_MISMATCH` error for the `participants.tsv`, and one non-4D BOLD sequence.

NOTE: bids validation will return many WARNINGS and often fewer ERRORS. This is expected. It can be helpful to filter the validation.tsv file to only show errors and address those first. Warnings can often be ignored but you should check with a modality expert that none of the missing sidecar info is critical.

`cubids purge bids_datalad/ ~/code/curation/04_cubids_curation/remove_non4d_bold.txt --use-datalad` was run to remove the [`non4d bold sequence`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/remove_non4d_bold.txt) (`e816aeb7` & `2486e875`).

Perf metadata was updated with [`update_perf_metadata.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/update_perf_metadata.py) (`f3f99b07`).

## CuBIDS group and apply

`cubids group v0` was run to begin looking at variants. There is a current issue with CuBIDS where M0 scans are mislabeled during `cubids apply`. To avoid this, the M0 scans were renamed manually with the [`cubids_group_rename.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/cubids_group_rename.py) script (`c649a45e`).

`cubids group v1` was run to get new groupings and tsvs.

Groupings were [`analyzed`](https://www.notion.so/go-through-cubids-groupings-1ac2e9b4cd19806887cad86b63739b47?pvs=4).

Several anatomical images were multi-run. In order to determine which runs to drop, the [`find_multiruns.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/find_multiruns.py) script was used to find the runs.

Jupyterlab was then used on cubic to inspect the data.

In a terminal on the cubic project user:
```bash
micromamba activate cubids
micromamba install jupyterlab # if not already installed
jupyter lab --no-browser --port=8888
```

Then, in a new terminal:
```bash
ssh -L localhost:8888:localhost:8888 singlest@cubic-sattertt
```

Then, in the browser, go to `http://localhost:8888` and open the `inspect_multiruns.ipynb` file.
You will need to enter the token provided on the first terminal after the `[jupyterlab]` prompt.

It was determined that the first run of each anatomical scan should be dropped. The first run of all fmaps were also dropped.

The above drops and others listed in the groupings analysis above were performed by entering a `0` in the `merge into` column of the `v2_edited_summary.tsv` file and running [`cubids apply v2`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/cubids_apply_v2.sh) (`3770a47d`, `d7c3d0c7`, `e7e12920`, & `c6c521be`).

The `cubids apply` run did not apply the rename entity sets to the fmap files (see [`v2_summary.tsv`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/v2/v2_summary.tsv)).  This is a known issue with [`CuBIDS`](https://github.com/PennLINC/CuBIDS/issues/425) and the files will have to be renamed manually.

The fmap files were renamed with the [`cubids_group_rename.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/cubids_group_rename.py) script (`89ab9ef1`).

The run-02 angio/minIP for sub-87538 was removed manually (`6b0d5213`). This subject had three runs of angio/minIP. The first run was removed during `cubids apply v2`. The run-03 was kept. Run entities from all scans were removed with the [`remove_run_and_fix_intendedfor.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/remove_run_and_fix_intendedfor.py) script (`a49f9e71`).

The last volume of the odd no. vol asl scans was removed and all aslcontext files were updated with the [`fix_asl_odd_volumes.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/fix_asl_odd_volumes.py) script (`63f0b87e`). NOTE: For nibable to access the niftis, first run `datalad unlock sub-*/ses-1/perf/*` in the datalad dataset before running the script.

`cubids group v3` was run to get groupings and tsvs. This revealed a few anat and fmap scans that previously held the run entity and now need variant renamings. This was done with the [`cubids_group_rename.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/cubids_group_rename.py) script (`fed752dc`) rather than a full `cubids apply` run.

`cubids group v4` was run to get groupings and tsvs. Here it was realized that the m0 scans still inherited the ASL variant names during cubids apply v2. The m0 scans were reverted to their original names using [`rename_m0_scans.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/rename_m0_scans.py) (`42a17c3b`).

Two M0 scan jsons became corrupted during a later step. `get reset --hard` was run to revert to the above commit and the jsons were copied back in from the aslprep project (`93ae96f5`). The metadata on these two jsons was updated with the [`update_perf_metadata.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/update_perf_metadata.py) script (`93ae96f5`). The intendedfor fields for these two jsons were updated to use the correct variant names (`67a98ddf`).

 Finally, all M0 scans and jsons were given the appropriate variant names using the [`cubids_group_rename.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/cubids_group_rename.py) script with the v0 summary and file tsvs (`551d9014`).

`cubids group v5` was run to check groupings. Groupings look good!

`cubids validate v5` was run to check for validation errors. No errors were found!

After discussion with Manuel Taso and review of the dicoms, it was determined that the ASL scans had two background suppression pulses (1.5s label / 1.5s PLD). The [`set_background_suppression_true.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/set_background_suppression_true.py) script was used to set the `BackgroundSuppression` field to true (`533f4d6a`).

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


# 06: QC

datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/fmriprep_anat/output_ria#~data /cbica/projects/grmpy/data/ephemerals/fmriprep_anat
datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/fmriprep_func/output_ria#~data /cbica/projects/grmpy/data/ephemerals/fmriprep_func
datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/qsiprep/output_ria#~data /cbica/projects/grmpy/data/ephemerals/qsiprep
datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/qsirecon/output_ria#~data /cbica/projects/grmpy/data/ephemerals/qsirecon
datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/aslprep/output_ria#~data /cbica/projects/grmpy/data/ephemerals/aslprep
datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/freesurfer-post/output_ria#~data /cbica/projects/grmpy/data/ephemerals/freesurfer-post
datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/xcp-d/output_ria#~data /cbica/projects/grmpy/data/ephemerals/xcp-d
datalad clone --reckless ephemeral ria+file:///cbica/projects/grmpy/data/BABS/derivatives/mriqc/output_ria#~data /cbica/projects/grmpy/data/ephemerals/mriqc


unzip to `/cbica/projects/grmpy/data/derivatives/xcp-d`

```
screen

cd /cbica/projects/grmpy/data/ephemerals/xcp-d

# Grab all matching files into an array
files=(sub-*.zip)

# Iterate over them
for f in "${files[@]}"; do
    unzip -n "$f" -d /cbica/projects/grmpy/data/derivatives
done
```

for fmriprep_func - a reduced set of files was unzipped:

```
for f in "${files[@]}"; do
    unzip -n "$f" -d /cbica/projects/grmpy/data/derivatives -x $(cat /cbica/projects/grmpy/code/curation/06_QC/scripts/exclude.txt)
done
```

for aslprep - we can ignore the ses-1/perf/*_desc-preproc_asl.* files since the timeseries are useless

```
for f in "${files[@]}"; do
    unzip -n "$f" -d /cbica/projects/grmpy/data/derivatives -x aslprep/sub-*/ses-1/perf/*_desc-preproc_asl.*
done
```

check that fmriprep in apply mode will work with this reduced set:

```
#!/bin/bash
#SBATCH --job-name=fmriprep_apply
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=20gb
#SBATCH --time=48:00:00
# Outputs ----------------------------------
#SBATCH --output=/cbica/projects/grmpy/data/fmriprep_apply_test/fmriprep_apply.out
#SBATCH --error=/cbica/projects/grmpy/data/fmriprep_apply_test/fmriprep_apply.err
# ------------------------------------------

apptainer run \
    --cleanenv \
    -B /cbica/projects/grmpy/data/bids_datalad:/data \ #bind path to your input BIDS data
    -B /cbica/projects/grmpy/data/derivatives:/deriv \ #bind path to your input fmriprepdata
    -B /cbica/projects/grmpy/data/fmriprep_apply_test:/out \ #bind path to your output directory
    -B /cbica/comp_space/grmpy/apply_test:/work \ #bind path to your compute space
    -B /cbica/projects/grmpy/data/fmriprep_apply_test/license.txt:/license.txt \ #bind path to your freesurfer license file
    /cbica/projects/grmpy/data/BABS/apptainer/fmriprep-25.1.4.sif \ #path to your apptainer image
    /data \ #path to your input BIDS data
    /out/fmriprep-apply-25.1.4 \ #path to your output directory
    participant \ #processing level
    -w /work \ #working directory
    --stop-on-first-crash \
    --fs-license-file /license.txt \
    --output-spaces func T1w MNI152NLin6Asym:res-2 \
    --force bbr \
    --skip-bids-validation \
    -vv \
    --cifti-output 91k \
    --n_cpus 4 \
    --mem-mb 70000 \
    --fs-subjects-dir /deriv/fmriprep_anat/sourcedata/freesurfer \ #path to your freesurfer results
    --participant-label sub-106802 \ #participant label
    --derivatives minimal=/deriv/fmriprep_func \ #path to your minimal fmriprep results
    --fs-no-resume
```

It works! TODO: add this to the README for the fmriprep repo.

## XCP-D QC

```bash
xcpd_median_fd.py:66: FutureWarning: The behavior of DataFrame concatenation with empty or all-NA entries is deprecated. In a future version, this will no longer exclude empty or all-NA columns when determining the result dtypes. To retain the old behavior, exclude the relevant entries before the concat operation.
  df_main_qc = pd.concat([df_main_qc, df_subj_qc], ignore_index=True)
```

Median FD and parcel coverage were analyzed with the [`01_xcpd_qc.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/06_QC/scripts/01_xcpd_qc.py) script. The script generated several QC metrics and visualizations to assess data quality:

### Motion Assessment

![Median FD Histogram](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/xcpd_qc_histogram_median_fd.png)

The histogram of median framewise displacement (FD) shows the distribution of head motion across all subjects. The majority of subjects exhibited low motion, with most median FD values falling below 0.2mm, indicating generally good motion control during scanning.

### Parcel Coverage Analysis

The Schaefer 1000 parcels + 56 subcortical regions (4S1056) atlas was used to assess brain coverage. Two main visualizations were generated to examine the coverage:

![Row Sum Barplot](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/xcpd_4S1056Parcels_coverage_row_sum_barplot.png)

A barplot showing the temporal coverage (number of valid timepoints) for each subject, allowing identification of subjects with notably poor coverage.

![Column Sum Barplot](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/xcpd_4S1056Parcels_coverage_col_sum_barplot.png)

A barplot showing the number of subjects with valid data for each parcel, helping identify any systematically problematic brain regions across the cohort.

## QSI QC

Quality control metrics for diffusion MRI data were analyzed using the [`02_qsi_qc.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/06_QC/scripts/02_qsi_qc.py) script. The analysis covered both QSIPrep preprocessing quality metrics and QSIRecon tractography results.

### QSIPrep Quality Metrics

![Mean FD Histogram](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/qsiprep_fd_histogram.png)

The distribution of mean framewise displacement (FD) across subjects shows the extent of head motion during diffusion scans. Lower values indicate better motion control during scanning.

![Neighborhood Correlation Histogram](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/qsiprep_neighborhood_corr_histogram.png)

The neighborhood correlation metric assesses the quality of the diffusion signal by measuring the similarity between adjacent voxels. Higher correlation values suggest better data quality with less noise.

![FD vs Neighborhood Correlation](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/qsiprep_scatter_meanfd_vs_neighborcorr.png)

This scatter plot explores the relationship between head motion (FD) and data quality (neighborhood correlation). A negative correlation would suggest that increased head motion leads to decreased data quality.

### DSI Studio Bundle Analysis

![Bundle Volume Distribution](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/qsirecon_DSIStudio_bundle_volume_histogram.png)

The total bundle volume distribution shows the variation in white matter tract volumes across subjects. This helps identify subjects with unusually large or small total tract volumes.

![Missing Bundle Distribution](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/qsirecon_DSIStudio_missing_bundle_column_distribution.png)

This histogram shows how many subjects are missing each white matter bundle. A high number of missing bundles could indicate problems with tract reconstruction or anatomical variability.

![Bundle Outlier Distribution](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/qsirecon_DSIStudio_row_bundle_outlier_distribution.png)

The distribution of outlier bundles per subject helps identify subjects with unusual tract volumes. Outliers are defined as bundle volumes more than 3 standard deviations from the mean or missing values.

### ASLPrep QC

Quality control metrics for ASL data were analyzed using the [`03_aslprep_qc.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/06_QC/scripts/03_aslprep_qc.py) script. The script focuses on the Quality Evaluation Index (QEI) for cerebral blood flow (CBF) measurements.

![QEI Distribution](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/aslprep_qei_cbf_histogram.png)

The QEI distribution shows the quality of CBF measurements across subjects. Higher QEI values indicate better quality ASL data with more reliable CBF quantification. The QEI takes into account factors such as temporal signal-to-noise ratio, motion artifacts, and ASL signal intensity.

### FreeSurfer-Post QC

Surface reconstruction quality was assessed using the [`04_freesurfer-post_qc.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/06_QC/scripts/04_freesurfer-post_qc.py) script. The analysis focuses on the Euler characteristic, a topological measure that indicates the quality of surface reconstruction.

![Left Hemisphere Euler](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/freesurfer-post_LH_euler_qc_histogram.png)

The left hemisphere Euler characteristic distribution shows the quality of surface reconstruction across subjects. A higher (less negative) Euler number indicates a simpler topology with fewer topological defects.

![Right Hemisphere Euler](https://raw.githubusercontent.com/PennLINC/grmpy_opendata/main/curation/06_QC/data/freesurfer-post_RH_euler_qc_histogram.png)

Similarly, the right hemisphere Euler characteristic distribution provides insight into the quality of surface reconstruction for the right hemisphere. The distributions for both hemispheres should be roughly similar, with any large asymmetries potentially indicating reconstruction issues.

### T1w QC manual ratings

The T1w QC manual ratings were generated using the [`06_generate_T1_rating_html.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/06_QC/scripts/06_generate_T1_rating_html.py) script. The script generates a HTML page with a simple UI to rate each view per (sub, ses).

```bash
python /cbica/projects/grmpy/code/curation/06_QC/scripts/06_generate_T1_rating_html.py \
  --root /cbica/projects/grmpy/data/T1_QC/slices \
  --out /cbica/projects/grmpy/code/curation/06_QC/scripts/07_T1_QC_ratings.html \
  --portable \
  --allow-missing
```

The HTML page ([07_T1_QC_ratings.html](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/06_QC/scripts/07_T1_QC_ratings.html)) allows for easy viewing and rating of the T1w images. The ratings are exported to a CSV file.

# Analysis


# Phenotypic Data

Phenotypic data was collected and previously uploaded to the GRMPY flywheel project. The phenotypic data for each participant is contained in the `/cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS/<sub-id>/` under a `<sub-id>.flywheel.json` file.

First, the available phenotypes were summarized using the [`01_summarize_available_phenotypes.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/01_summarize_available_phenotypes.py) script.

```bash
python /cbica/projects/grmpy/code/phenotype/01_summarize_available_phenotypes.py \
  --subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
  --output /cbica/projects/grmpy/code/phenotype/data/available_phenotypes.tsv
```

Then, the phenotypes were extracted using the [`02_extract_info_subfield.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/02_extract_info_subfield.py) script. This script allows for the exclusion of specific fields to avoid including sensitive information. Below are the commands used, along with exclusions for each phenotype.

```bash
python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield self_report_summary --output phenotype/data/self_report_summary.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield demographics \
--output phenotype/data/demographics.tsv \
--exclude intakeby,study_coordinator

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield CNB_raw \
--output phenotype/data/CNB_raw.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield Diagnosis \
--output phenotype/data/Diagnosis.tsv \
--exclude CONSENSUSBY,INTERVIEWER,ENTBY,DODIAGNOSIS

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield Proband_GOASSESS \
--output phenotype/data/Proband_GOASSESS.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield tanner_substance_spq \
--output phenotype/data/tanner_substance_spq.tsv \
--exclude redcapid,bbl_assessor,bbl_protocol,bbl_location

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield prime_screen \
--output phenotype/data/prime_screen.tsv \
--exclude redcapid,assessor,protocol

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield biss_madrs \
--output phenotype/data/biss_madrs.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield n_back_scores \
--output phenotype/data/n_back_scores.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield imaging_prescan_scales \
--output phenotype/data/imaging_prescan_scales.tsv \
--exclude redcapid,bbl_assessor,bbl_location

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield imaging_postscan_scales \
--output phenotype/data/imaging_postscan_scales.tsv \
--exclude redcapid,bbl_assessor,bbl_location

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield self_report_itemwise \
--output phenotype/data/self_report_itemwise.tsv \
--exclude redcapid,bbl_assessor

```

## Self-report scoring

The self-report itemwise data was split into separate files using the [`03_separate_self_reports.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/03_separate_self_reports.py) script.

als
map-sr - no summary scores in the self_report_summary.tsv, calculated following the logic in GRMPY_selfReportScoringCode_v4.R
swan-child
swan-collateral - missing?
aces
scared
scared-collateral - missing?
rpaq
ari - ari_7 isn't used in scoring?
ari-collateral - missing?
bdi
bisbas
grit
hcl - only uses hcl6_3 questions for scoring
bss
phys_anhed - scored as rpasShort
soc_anhed - scored as rsasShort
eswan_dmdd
psqi
best

TODO: split up self-reports into separate files; find out what additional fields to exclude; split up pre/post scan scales into separate files;

TODO: look into / include these filters prior to the splitting
```
grumpy<-grumpy[ which(grumpy$bbl_protocol %in% "GRMPY") , ] #removes subjects not listed as GRMPY protcol
grumpy<-grumpy[ which(grumpy$statetrait_vcode %in% "V" | grumpy$statetrait_vcode %in% "U" | grumpy$statetrait_vcode %in% "F") , ] #removes data not listed as "U" unproctored valid or "V" valid data or "F" for flagged
grumpy <- grumpy[ which(grumpy$admin_proband %in% "p"),]
grumpy[grumpy ==-9999] <- NA #replaces -9999 with NAs
```

# helpful hints

Use `git log --oneline` in your datalad project directory to get the commit history of your dataset.

If you ever need to reset a datalad project (or any git project) to a previous commit, you can do so with the following command (from the datalad project directory):
```bash
git reset --hard <commit_hash>
```

If you need to remove specific files from a datalad dataset, you can do so with the following command (from the dataladproject directory):
```bash
git rm <file_path> # can be a glob pattern, i.e. `git rm sub-*/ses-*/anat/*T1w*` to remove all T1w images and their jsons
```

If you ever need to delete a datalad dataset, you can do so with the following command (from the directory containing the dataset):
```bash
datalad drop -r <dataset_name>
rm -rf <dataset_name>
```
or:
```bash
chmod -R u+w <dataset_name>
rm -rf <dataset_name>
```

Check the amount of disk space left on your project user:
`df -h /cbica/projects/grmpy`

Check how much space a folder takes up:
`du -sh <folder_path>`

TODO: ephemeral clones
