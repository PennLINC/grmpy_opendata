---
title: "02: Converting to bids"
layout: default
nav_order: 3
---

# 02: Converting to bids

After downloading DICOM files via Flywheel, the [`dcm2bids_submit.sh`](https://github.com/PennLINC/grmpy_opendata/blob/main/curation/02_dcm2bids/dcm2bids_submit.sh) script converts these files (located in `cbica/projects/grmpy/source_data`) into the BIDS format (bids outputs in `cbica/projects/grmpy/data/bids`).
It selects a subject based on the SLURM array task ID, finds all session directories with DICOM data for that subject, and then processes each session with the `dcm2bids` tool, ensuring that the converted data is properly organized in the BIDS directory.

Two subjects (`95257` and `20120`) had multiple sessions. For `95257`, the first visit's scans were stopped due to technical difficulties with the O2 detector that day.
On the second visit, the scan was completed, however, lmscribe stopped working and all fMRI sequences had to be completed straight on rather than adjusted. For `20120`, the first visit was completed with an earring.
The participant came back for a second session with a plastic holder in their ear. In both cases, we kept the second session and deleted the first (performed below in the initial CuBIDS stages).
