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
The participant came back for a second session with a plastic holder in their ear. In both cases, we kept the second session and deleted the first.

# 03: Creating timing files

Timing files were created manually for the nback task following the [`create_fracback_events.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/03_create_events/create_fracback_events.py) script.

Timing files still need to be created for FACES.

# 04: CuBIDS

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

The bids data in `/cbica/projects/grmpy/data/bids` was checked into a datalad dataset at `cbica/projects/grmpy/data/bids_datalad` and nifti info was added into the json sidecars using CuBIDS.

`cubids validate v0` was run.

The fmap sidecar `IntendedFor` fields were known to have an issue and updated to use relative paths instead of full BIDS uris, using the [`fix_intendedfor.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/fix_intendedfor.py) script.

`cubids validate v1` was then run and this did not decrease the amount of validation errors/warnings.

A number of the warnings are due to bids not being compatable with minIP images. Will add those to `.bidsignore`.
Many others are for missing sidecare info in perfusion jsons.

A participants.tsv was initialized using [`generate_participants_tsv.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/generate_participants_tsv.py).

It is also noted that the two before-mentioned subjects with a second session actually had both sessions checked into datalad. Those have now had their first sessions removed and the second sessions renamed to ses-1. The fmap intendefor pather were also updated. This was all done using [`fix_sessions.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/fix_sessions.py).

After these changes `v2` validation reveals that remaining errors are missing sidecar info for perfusion scans and one non-4D BOLD sequence.

`cubids purge bids_datalad/ ~/code/curation/04_cubids_curation/remove_non4d_bold.txt --use-datalad` was run to remove the [`non4d bold sequence`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/04_cubids_curation/remove_non4d_bold.txt).
