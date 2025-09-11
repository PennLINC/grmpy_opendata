for subdir in sub-*; do
  anat_dir="$subdir/ses-1/anat"
  if [ -d "$anat_dir" ]; then
    count=$(find "$anat_dir" -maxdepth 1 -name '*angio.json' 2>/dev/null | wc -l)
    echo "$subdir: $count"
  fi
done
