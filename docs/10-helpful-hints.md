---
title: "Helpful hints"
layout: default
nav_order: 11
---

# Helpful hints

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
datalad drop -d <dataset_name>
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
