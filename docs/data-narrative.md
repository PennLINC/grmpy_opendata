---
title: Data Narrative
layout: page
nav_order: 2
---

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

`cubids group v4` was run to get groupings and tsvs. Here it was realized that the m0 scans still inherited the ASL variant names during cubids apply v2. The m0 scans were reverted to their original names using [`rename_m0_scans.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/rename_m0_scans.py) (`42a17c3b`) and then they were given the appropriate variant names using the [`cubids_group_rename.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/cubids_group_rename.py) script with the v0 summary and file tsvs (`9893b75e`).

`cubids validate v4` was run to check for validation errors and revealed that the `IntendedFor` fields were not updated for the M0 jsons after fixing the odd volume asl scan variants. This was done manually (no hash - datalad save did not provide one. CUBIC briefly crashed right before this, maybe something to do with that).

`cubids group v5` was run to check groupings. Groupings look good!

`cubids validate v5` was run to check for validation errors. No errors were found!

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

## fMRIPrep: Anatomical Only

VERSION: 25.1.4

The fMRIPrep container was set up with the [`babs_init_fmriprepanat.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/05_babs/babs_init_fmriprepanat.sh) script.

`babs check-setup` revealed all systems go.
`babs submit` was run to submit the jobs.


TODO: update the yamls on the babs-cubic-yaml repo