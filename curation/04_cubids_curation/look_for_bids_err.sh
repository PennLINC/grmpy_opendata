for subdir in sub-*; do
  anat_dir="$subdir/ses-1/anat"
  if [ -d "$anat_dir" ]; then
    has_run01=$(find "$anat_dir" -maxdepth 1 -name '*_ses-1_run-01_angio.json' | wc -l)
    has_standard=$(find "$anat_dir" -maxdepth 1 -name '*_ses-1_angio.json' | wc -l)

    if [[ "$has_run01" -gt 0 && "$has_standard" -gt 0 ]]; then
      echo "Found both in: $subdir"
    fi
  fi
done
