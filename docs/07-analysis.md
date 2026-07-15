---
title: "Analysis"
layout: default
nav_order: 8
---

# Analysis

## ASL
CBF maps were generated using [`plot_asl_cbf_maps.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/plot_asl_cbf_maps.py).

## fMRI

ALFF and ReHo were generated using [`plot_alff_reho.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/plot_alff_reho.py).

Atlasses were generated using [`plot_atlases.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/plot_atlases.py).

Correlation matrices were generated using [`plot_corrmats.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/plot_corrmats.py).

### GLM

The fracback GLM was run using the [`run_fracback_glm_first_level.slurm`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/task_glm/run_fracback_glm_first_level.slurm) script which runs the [`run_fracback_glm_first_level.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/task_glm/run_fracback_glm_first_level.py) script for each subject and model type.

These runs didn't complete:

fracback_15153658_10.err -> '106071' not found in fmriprep (has no T1w -- expected)

The remaining failed runs had this error:
```
File "/gpfs/fs001/cbica/projects/grmpy/micromamba/envs/nilearn/lib/python3.12/json/decoder.py", line 356, in raw_decode
    raise JSONDecodeError("Expecting value", s, err.value) from None
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

This is apparently a known issue where two processes are trying to write to the same file. The solution is to re-submit. This was done using the [`rerun_frackback_glm_first_level.slurm`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/task_glm/rerun_frackback_glm_first_level.slurm) script.

Second-level GLM was run using the [`run_fracback_second_level.slurm`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/task_glm/run_fracback_second_level.slurm) script which runs the [`run_fracback_second_level.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/task_glm/run_fracback_second_level.py) script for each model type and contrast.

Group figures were generated using [`create_group_figure.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/task_glm/create_group_figure.py).

## QSI

QSI Recon scalar maps were generated using [`plot_qsi_scalar_maps.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/plot_qsi_scalar_maps.py).

Bundles were plotted using [`plot_afq_bundles.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/analysis/plot_afq_bundles.py).
