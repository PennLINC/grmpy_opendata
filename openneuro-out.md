	[33m[WARNING] README_FILE_SMALL The recommended file '/README' is very small.
Please consider expanding it with additional information about the dataset.[39m
		/README
		/README.md

[36m	Please visit https://neurostars.org/search?q=README_FILE_SMALL for existing conversations about this issue.[39m

	[33m[WARNING] UNKNOWN_BIDS_VERSION The BIDSVersion field of 'dataset_description.json' does not match a known release.
The BIDS Schema used for validation may be out of date.[39m
		/dataset_description.json

[36m	Please visit https://neurostars.org/search?q=UNKNOWN_BIDS_VERSION for existing conversations about this issue.[39m

	[33m[WARNING] JSON_KEY_RECOMMENDED A JSON file is missing a key listed as recommended.[39m
		[33mGeneratedBy[39m
		/dataset_description.json - Field description: Used to specify provenance of the dataset.

		[33mSourceDatasets[39m
		/dataset_description.json - Field description: Used to specify the locations and relevant attributes of all source datasets.
Valid keys in each object include [36m"URL"[39m, [36m"DOI"[39m (see
[34mURI[39m ([90mhttps://bids-specification.readthedocs.io/en/stable/common-principles.md#uniform-resource-indicator[39m)), and
[36m"Version"[39m with
[34mstring[39m ([90mhttps://www.w3schools.com/js/js_json_datatypes.asp[39m)
values.

[36m	Please visit https://neurostars.org/search?q=JSON_KEY_RECOMMENDED for existing conversations about this issue.[39m

	[33m[WARNING] SIDECAR_KEY_RECOMMENDED A data file's JSON sidecar is missing a key listed as recommended.[39m
		[33mPulseSequenceType[39m
		/sub-114935/ses-1/fmap/sub-114935_ses-1_magnitude2.nii.gz - Field description: A general description of the pulse sequence used for the scan.
		/sub-114935/ses-1/fmap/sub-114935_ses-1_acq-multiband_dir-PA_epi.nii.gz - Field description: A general description of the pulse sequence used for the scan.

		2839 more files with the same issue

		[33mPartialFourierDirection[39m
		/sub-114935/ses-1/fmap/sub-114935_ses-1_magnitude2.nii.gz - Field description: The direction where only partial Fourier information was collected.
Corresponds to [34mDICOM Tag 0018, 9036[39m ([90mhttps://dicomlookup.com/dicomtags/(0018,9036)[39m) [36mPartial Fourier Direction[39m.
		/sub-114935/ses-1/fmap/sub-114935_ses-1_acq-multiband_dir-PA_epi.nii.gz - Field description: The direction where only partial Fourier information was collected.
Corresponds to [34mDICOM Tag 0018, 9036[39m ([90mhttps://dicomlookup.com/dicomtags/(0018,9036)[39m) [36mPartial Fourier Direction[39m.

		2839 more files with the same issue

		[33mDwellTime[39m
		/sub-114935/ses-1/fmap/sub-114935_ses-1_magnitude2.nii.gz - Field description: Actual dwell time (in seconds) of the receiver per point in the readout
direction, including any oversampling.
For Siemens, this corresponds to DICOM field 0019, 1018 (in ns).
This value is necessary for the optional readout distortion correction of
anatomicals in the HCP Pipelines.
It also usefully provides a handle on the readout bandwidth,
which isn't captured in the other metadata tags.
Not to be confused with [36m"EffectiveEchoSpacing"[39m, and the frequent mislabeling
of echo spacing (which is spacing in the phase encoding direction) as
"dwell time" (which is spacing in the readout direction).
		/sub-114935/ses-1/fmap/sub-114935_ses-1_acq-multiband_dir-PA_epi.nii.gz - Field description: Actual dwell time (in seconds) of the receiver per point in the readout
direction, including any oversampling.
For Siemens, this corresponds to DICOM field 0019, 1018 (in ns).
This value is necessary for the optional readout distortion correction of
anatomicals in the HCP Pipelines.
It also usefully provides a handle on the readout bandwidth,
which isn't captured in the other metadata tags.
Not to be confused with [36m"EffectiveEchoSpacing"[39m, and the frequent mislabeling
of echo spacing (which is spacing in the phase encoding direction) as
"dwell time" (which is spacing in the readout direction).

		2427 more files with the same issue

		[33mInstitutionalDepartmentName[39m
		/sub-114935/ses-1/fmap/sub-114935_ses-1_magnitude2.nii.gz - Field description: The department in the institution in charge of the equipment that produced
the measurements.
		/sub-114935/ses-1/fmap/sub-114935_ses-1_acq-multiband_dir-PA_epi.nii.gz - Field description: The department in the institution in charge of the equipment that produced
the measurements.

		2427 more files with the same issue

		[33mLabelingOrientation[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Orientation of the labeling plane ([36m(P)CASL[39m) or slab ([36mPASL[39m).
The direction cosines of a normal vector perpendicular to the ASL labeling
slab or plane with respect to the patient.
Corresponds to [34mDICOM Tag 0018, 9255[39m ([90mhttps://dicomlookup.com/dicomtags/(0018,9255)[39m) [36mASL Slab Orientation[39m.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Orientation of the labeling plane ([36m(P)CASL[39m) or slab ([36mPASL[39m).
The direction cosines of a normal vector perpendicular to the ASL labeling
slab or plane with respect to the patient.
Corresponds to [34mDICOM Tag 0018, 9255[39m ([90mhttps://dicomlookup.com/dicomtags/(0018,9255)[39m) [36mASL Slab Orientation[39m.

		212 more files with the same issue

		[33mLabelingDistance[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Distance from the center of the imaging slab to the center of the labeling
plane ([36m(P)CASL[39m) or the leading edge of the labeling slab ([36mPASL[39m),
in millimeters.
If the labeling is performed inferior to the isocenter,
this number should be negative.
Based on DICOM macro C.8.13.5.14.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Distance from the center of the imaging slab to the center of the labeling
plane ([36m(P)CASL[39m) or the leading edge of the labeling slab ([36mPASL[39m),
in millimeters.
If the labeling is performed inferior to the isocenter,
this number should be negative.
Based on DICOM macro C.8.13.5.14.

		212 more files with the same issue

		[33mLabelingLocationDescription[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Description of the location of the labeling plane ([36m"CASL"[39m or [36m"PCASL"[39m) or
the labeling slab ([36m"PASL"[39m) that cannot be captured by fields
[36mLabelingOrientation[39m or [36mLabelingDistance[39m.
May include a link to a deidentified screenshot of the planning of the
labeling slab/plane with respect to the imaging slab or slices
[36m*_asllabeling.*[39m.
Based on DICOM macro C.8.13.5.14.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Description of the location of the labeling plane ([36m"CASL"[39m or [36m"PCASL"[39m) or
the labeling slab ([36m"PASL"[39m) that cannot be captured by fields
[36mLabelingOrientation[39m or [36mLabelingDistance[39m.
May include a link to a deidentified screenshot of the planning of the
labeling slab/plane with respect to the imaging slab or slices
[36m*_asllabeling.*[39m.
Based on DICOM macro C.8.13.5.14.

		212 more files with the same issue

		[33mBackgroundSuppressionNumberPulses[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The number of background suppression pulses used.
Note that this excludes any effect of background suppression pulses applied
before the labeling.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The number of background suppression pulses used.
Note that this excludes any effect of background suppression pulses applied
before the labeling.

		212 more files with the same issue

		[33mBackgroundSuppressionPulseTime[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Array of numbers containing timing, in seconds,
of the background suppression pulses with respect to the start of the
labeling.
In case of multi-PLD with different background suppression pulse times,
only the pulse time of the first PLD should be defined.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Array of numbers containing timing, in seconds,
of the background suppression pulses with respect to the start of the
labeling.
In case of multi-PLD with different background suppression pulse times,
only the pulse time of the first PLD should be defined.

		212 more files with the same issue

		[33mLabelingPulseAverageGradient[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The average labeling gradient, in milliteslas per meter.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The average labeling gradient, in milliteslas per meter.

		212 more files with the same issue

		[33mLabelingPulseMaximumGradient[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The maximum amplitude of the gradient switched on during the application of
the labeling RF pulse(s), in milliteslas per meter.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The maximum amplitude of the gradient switched on during the application of
the labeling RF pulse(s), in milliteslas per meter.

		212 more files with the same issue

		[33mLabelingPulseAverageB1[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The average B1-field strength of the RF labeling pulses, in microteslas.
As an alternative, [36m"LabelingPulseFlipAngle"[39m can be provided.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The average B1-field strength of the RF labeling pulses, in microteslas.
As an alternative, [36m"LabelingPulseFlipAngle"[39m can be provided.

		212 more files with the same issue

		[33mLabelingPulseDuration[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Duration of the individual labeling pulses, in milliseconds.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Duration of the individual labeling pulses, in milliseconds.

		212 more files with the same issue

		[33mLabelingPulseFlipAngle[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The flip angle of a single labeling pulse, in degrees,
which can be given as an alternative to [36m"LabelingPulseAverageB1"[39m.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The flip angle of a single labeling pulse, in degrees,
which can be given as an alternative to [36m"LabelingPulseAverageB1"[39m.

		212 more files with the same issue

		[33mLabelingPulseInterval[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Delay between the peaks of the individual labeling pulses, in milliseconds.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Delay between the peaks of the individual labeling pulses, in milliseconds.

		212 more files with the same issue

		[33mPCASLType[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The type of gradient pulses used in the [36mcontrol[39m condition.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The type of gradient pulses used in the [36mcontrol[39m condition.

		212 more files with the same issue

		[33mMatrixCoilMode[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: (If used)
A method for reducing the number of independent channels by combining in
analog the signals from multiple coil elements.
There are typically different default modes when using un-accelerated or
accelerated (for example, [36m"GRAPPA"[39m, [36m"SENSE"[39m) imaging.
		/sub-114935/ses-1/perf/sub-114935_ses-1_m0scan.nii.gz - Field description: (If used)
A method for reducing the number of independent channels by combining in
analog the signals from multiple coil elements.
There are typically different default modes when using un-accelerated or
accelerated (for example, [36m"GRAPPA"[39m, [36m"SENSE"[39m) imaging.

		407 more files with the same issue

		[33mCoilCombinationMethod[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Almost all fMRI studies using phased-array coils use root-sum-of-squares
(rSOS) combination, but other methods exist.
The image reconstruction is changed by the coil combination method
(as for the matrix coil mode above),
so anything non-standard should be reported.
		/sub-114935/ses-1/perf/sub-114935_ses-1_m0scan.nii.gz - Field description: Almost all fMRI studies using phased-array coils use root-sum-of-squares
(rSOS) combination, but other methods exist.
The image reconstruction is changed by the coil combination method
(as for the matrix coil mode above),
so anything non-standard should be reported.

		407 more files with the same issue

		[33mNonlinearGradientCorrection[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: Boolean stating if the image saved has been corrected for gradient
nonlinearities by the scanner sequence.
		/sub-114935/ses-1/perf/sub-114935_ses-1_m0scan.nii.gz - Field description: Boolean stating if the image saved has been corrected for gradient
nonlinearities by the scanner sequence.

		407 more files with the same issue

		[33mPhaseEncodingDirection[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The letters [36mi[39m, [36mj[39m, [36mk[39m correspond to the first, second and third axis of
the data in the NIFTI file.
The polarity of the phase encoding is assumed to go from zero index to
maximum index unless [36m-[39m sign is present
(then the order is reversed - starting from the highest index instead of
zero).
[36mPhaseEncodingDirection[39m is defined as the direction along which phase is was
modulated which may result in visible distortions.
Note that this is not the same as the DICOM term
[36mInPlanePhaseEncodingDirection[39m which can have [36mROW[39m or [36mCOL[39m values.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: The letters [36mi[39m, [36mj[39m, [36mk[39m correspond to the first, second and third axis of
the data in the NIFTI file.
The polarity of the phase encoding is assumed to go from zero index to
maximum index unless [36m-[39m sign is present
(then the order is reversed - starting from the highest index instead of
zero).
[36mPhaseEncodingDirection[39m is defined as the direction along which phase is was
modulated which may result in visible distortions.
Note that this is not the same as the DICOM term
[36mInPlanePhaseEncodingDirection[39m which can have [36mROW[39m or [36mCOL[39m values.

		212 more files with the same issue

		[33mTotalReadoutTime[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: This is actually the "effective" total readout time,
defined as the readout duration, specified in seconds,
that would have generated data with the given level of distortion.
It is NOT the actual, physical duration of the readout train.
If [36m"EffectiveEchoSpacing"[39m has been properly computed,
it is just [36mEffectiveEchoSpacing * (ReconMatrixPE - 1)[39m.
		/sub-121050/ses-1/perf/sub-121050_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz - Field description: This is actually the "effective" total readout time,
defined as the readout duration, specified in seconds,
that would have generated data with the given level of distortion.
It is NOT the actual, physical duration of the readout train.
If [36m"EffectiveEchoSpacing"[39m has been properly computed,
it is just [36mEffectiveEchoSpacing * (ReconMatrixPE - 1)[39m.

		212 more files with the same issue

		[33mSpoilingType[39m
		/sub-114935/ses-1/anat/sub-114935_ses-1_rec-refaced_T1w.nii.gz - Field description: Specifies which spoiling method(s) are used by a spoiled sequence.
		/sub-114935/ses-1/anat/sub-114935_ses-1_rec-defaced_T2w.nii.gz - Field description: Specifies which spoiling method(s) are used by a spoiled sequence.

		459 more files with the same issue

		[33mInstructions[39m
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-multiband_bold.nii.gz - Field description: Text of the instructions given to participants before the recording.
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-singleband_bold.nii.gz - Field description: Text of the instructions given to participants before the recording.

		691 more files with the same issue

		[33mTaskDescription[39m
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-multiband_bold.nii.gz - Field description: Longer description of the task.
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-singleband_bold.nii.gz - Field description: Longer description of the task.

		691 more files with the same issue

		[33mCogAtlasID[39m
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-multiband_bold.nii.gz - Field description: [34mURI[39m ([90mhttps://bids-specification.readthedocs.io/en/stable/common-principles.md#uniform-resource-indicator[39m)
of the corresponding [34mCognitive Atlas[39m ([90mhttps://www.cognitiveatlas.org/[39m)
Task term.
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-singleband_bold.nii.gz - Field description: [34mURI[39m ([90mhttps://bids-specification.readthedocs.io/en/stable/common-principles.md#uniform-resource-indicator[39m)
of the corresponding [34mCognitive Atlas[39m ([90mhttps://www.cognitiveatlas.org/[39m)
Task term.

		691 more files with the same issue

		[33mCogPOID[39m
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-multiband_bold.nii.gz - Field description: [34mURI[39m ([90mhttps://bids-specification.readthedocs.io/en/stable/common-principles.md#uniform-resource-indicator[39m)
of the corresponding [34mCogPO[39m ([90mhttp://www.cogpo.org/[39m) term.
		/sub-114935/ses-1/func/sub-114935_ses-1_task-rest_acq-singleband_bold.nii.gz - Field description: [34mURI[39m ([90mhttps://bids-specification.readthedocs.io/en/stable/common-principles.md#uniform-resource-indicator[39m)
of the corresponding [34mCogPO[39m ([90mhttp://www.cogpo.org/[39m) term.

		691 more files with the same issue

		[33mStimulusPresentation[39m
		/sub-114935/ses-1/func/sub-114935_ses-1_task-fracback_acq-singleband_events.tsv - Field description: Object containing key-value pairs related to the software used to present
the stimuli during the experiment.
		/sub-121050/ses-1/func/sub-121050_ses-1_task-fracback_acq-singleband_events.tsv - Field description: Object containing key-value pairs related to the software used to present
the stimuli during the experiment.

		193 more files with the same issue

[36m	Please visit https://neurostars.org/search?q=SIDECAR_KEY_RECOMMENDED for existing conversations about this issue.[39m

	[33m[WARNING] MISSING_MAGNITUDE1_FILE 'phasediff.nii[.gz]' file does not have an associated 'magnitude1.nii[.gz]' file.[39m
		/sub-114935/ses-1/fmap/sub-114935_ses-1_phasediff.nii.gz
		/sub-83010/ses-1/fmap/sub-83010_ses-1_phasediff.nii.gz

		109 more files with the same issue

[36m	Please visit https://neurostars.org/search?q=MISSING_MAGNITUDE1_FILE for existing conversations about this issue.[39m

	[33m[WARNING] GZIP_HEADER_MTIME The gzip header contains a non-zero timestamp.
This may leak sensitive information or indicate a non-reproducible conversion process.[39m
		/sub-114935/ses-1/perf/sub-114935_ses-1_acq-VARIANTRepetitionTimeC0_asl.nii.gz
		/sub-114935/ses-1/perf/sub-114935_ses-1_m0scan.nii.gz

		405 more files with the same issue

[36m	Please visit https://neurostars.org/search?q=GZIP_HEADER_MTIME for existing conversations about this issue.[39m

	[33m[WARNING] GZIP_HEADER_FILENAME The gzip header contains a non-empty filename.
This may leak sensitive information or indicate a non-reproducible conversion process.[39m
		/sub-83010/ses-1/perf/sub-83010_ses-1_asl.nii.gz
		/sub-83010/ses-1/perf/sub-83010_ses-1_m0scan.nii.gz

		141 more files with the same issue

[36m	Please visit https://neurostars.org/search?q=GZIP_HEADER_FILENAME for existing conversations about this issue.[39m

	[33m[WARNING] EVENTS_TSV_MISSING Task scans should have a corresponding 'events.tsv' file.
If this is a resting state scan you can ignore this warning or rename the task to include the word "rest".[39m
		/sub-83010/ses-1/func/sub-83010_ses-1_task-face_acq-singleband_bold.nii.gz
		/sub-82051/ses-1/func/sub-82051_ses-1_task-face_acq-singleband_bold.nii.gz

		50 more files with the same issue

[36m	Please visit https://neurostars.org/search?q=EVENTS_TSV_MISSING for existing conversations about this issue.[39m

	[33m[WARNING] TSV_ADDITIONAL_COLUMNS_UNDEFINED A TSV file has extra columns which are not defined in its associated JSON sidecar[39m
		[33mmapsr_rawtot_sum[39m
		/phenotype/mapssr.tsv

		[33mmapsr_social_sum[39m
		/phenotype/mapssr.tsv

		[33mmapsr_recvoc_sum[39m
		/phenotype/mapssr.tsv

		[33mmapsr_motrelation_sum[39m
		/phenotype/mapssr.tsv

		[33mmapsr_engage_sum[39m
		/phenotype/mapssr.tsv

[36m	Please visit https://neurostars.org/search?q=TSV_ADDITIONAL_COLUMNS_UNDEFINED for existing conversations about this issue.[39m

	[31m[ERROR] MULTIPLE_README_FILES There are multiple '/README' files (with different extensions) in this BIDS
dataset. Only one '/README' file should exist.[39m
		/README
		/README.md

[36m	Please visit https://neurostars.org/search?q=MULTIPLE_README_FILES for existing conversations about this issue.[39m

	[31m[ERROR] TSV_VALUE_INCORRECT_TYPE A value in a column did not match the acceptable type for that column headers specified format.[39m
		[31mdx_BrderPD[39m
		/participants.tsv - '1.0'

		[31mdx_pscat[39m
		/participants.tsv - 'none'

		[31mdx_psychosis[39m
		/participants.tsv - 'pro'

		[31mpsqi_1[39m
		/phenotype/psqi.tsv - '300'

		[31mpsqi_3[39m
		/phenotype/psqi.tsv - '500'

		[31mwolf_post_1[39m
		/phenotype/wolf_post_imaging.tsv - ''

		[31mwolf_post_2[39m
		/phenotype/wolf_post_imaging.tsv - ''

		[31mwolf_post_3[39m
		/phenotype/wolf_post_imaging.tsv - ''

		[31msubstance_practice_age[39m
		/phenotype/suq.tsv - '1'

		[31msubstance_practice_fam___6[39m
		/phenotype/suq.tsv - '3'

		[31msubstance_tob_010[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_tob_020___3[39m
		/phenotype/suq.tsv - '2'

		[31msubstance_tob_030[39m
		/phenotype/suq.tsv - '6'

		[31msubstance_alc_010[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_alc_020[39m
		/phenotype/suq.tsv - '4'

		[31msubstance_alc_110[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_alc_120[39m
		/phenotype/suq.tsv - '6'

		[31msubstance_alc_140[39m
		/phenotype/suq.tsv - '2'

		[31msubstance_alc_150[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_alc_160[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_mar_010[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_010[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_020[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_030[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_040[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_050[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_060[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_070[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_072[39m
		/phenotype/suq.tsv - '2'

		[31msubstance_othr_080[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_090[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_100[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_101[39m
		/phenotype/suq.tsv - '2'

		[31msubstance_othr_110[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_120[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_130[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_140[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_150[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_160[39m
		/phenotype/suq.tsv - '0'

		[31msubstance_othr_170[39m
		/phenotype/suq.tsv - '0'

		[31mdrugs_opiates___0[39m
		/phenotype/suq.tsv - 'V'

		[31mbiss_31[39m
		/phenotype/biss_madrs.tsv - '9'

[36m	Please visit https://neurostars.org/search?q=TSV_VALUE_INCORRECT_TYPE for existing conversations about this issue.[39m


          [35mSummary:[39m                           [35mAvailable Tasks:[39m        [35mAvailable Modalities:[39m
          7087 Files, 171 GB                 Resting State           MRI                  
          231 - Subjects 1 - Sessions        Fractal N-Back                               
                                             Face                                         


Please correct validation errors before uploading.
