---
title: Data Narrative
layout: page
nav_order: 2
---

# Getting data from flywheel

The data download process is handled by our [`download_dcms.sh`](../curation/01_download_dcms/download_dcms.sh) script, which uses the Flywheel CLI to sync DICOM files.

This command syncs DICOM files from our Flywheel project to our local storage.

Here's the key part of the script:
```bash
/cbica/projects/grmpy/linux_amd64/fw sync -m --include dicom \
fw://bbl/GRMPY_822831 \
/cbica/projects/grmpy/sourcedata/
```

# Converting to bids
