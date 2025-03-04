# edit the dirs/file names as needed to search

# look for cases where there is a standard scan and a run-01/02 (edit for which one) scan
for subdir in sub-*; do
  anat_dir="$subdir/ses-1/func"
  if [ -d "$anat_dir" ]; then
    has_run01=$(find "$anat_dir" -maxdepth 1 -name '*_ses-1_run-02_task-face_acq-singleband_bold.json' | wc -l)
    has_standard=$(find "$anat_dir" -maxdepth 1 -name '*_ses-1_task-face_acq-singleband_bold.json' | wc -l)

    if [[ "$has_run01" -gt 0 && "$has_standard" -gt 0 ]]; then
      echo "Found both in: $subdir"
    fi
  fi
done

# look for cases where there is a run-02 but no run-01
# for subdir in sub-*; do
#   anat_dir="$subdir/ses-1/func"
#   if [ -d "$anat_dir" ]; then
#     has_run01=$(find "$anat_dir" -maxdepth 1 -name '*_ses-1_run-01_task-face_acq-singleband_bold.json' | wc -l)
#     has_run02=$(find "$anat_dir" -maxdepth 1 -name '*_ses-1_run-02_task-face_acq-singleband_bold.json' | wc -l)

#     if [[ "$has_run02" -gt 0 && "$has_run01" -eq 0 ]]; then
#       echo "Found run-02 but NO run-01 in: $subdir"
#     fi
#   fi
# done

