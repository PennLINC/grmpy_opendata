---
title: "Phenotypic Data"
layout: default
nav_order: 9
---

# Phenotypic Data

Phenotypic data was collected and previously uploaded to the GRMPY flywheel project. The phenotypic data for each participant is contained in the `/cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS/<sub-id>/` under a `<sub-id>.flywheel.json` file.

First, the available phenotypes were summarized using the [`01_summarize_available_phenotypes.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/01_summarize_available_phenotypes.py) script.

```bash
python /cbica/projects/grmpy/code/phenotype/01_summarize_available_phenotypes.py \
  --subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
  --output /cbica/projects/grmpy/code/phenotype/data/available_phenotypes.tsv
```

Then, the phenotypes were extracted using the [`02_extract_info_subfield.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/02_extract_info_subfield.py) script. This script allows for the exclusion of specific fields to avoid including sensitive information. Below are the commands used, along with exclusions for each phenotype.

```bash
python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield self_report_summary --output phenotype/data/self_report_summary.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield demographics \
--output phenotype/data/demographics.tsv \
--exclude intakeby,study_coordinator

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield CNB_raw \
--output phenotype/data/CNB_raw.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield Diagnosis \
--output phenotype/data/Diagnosis.tsv \
--exclude CONSENSUSBY,INTERVIEWER,ENTBY,DODIAGNOSIS

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield Proband_GOASSESS \
--output phenotype/data/Proband_GOASSESS.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield tanner_substance_spq \
--output phenotype/data/tanner_substance_spq.tsv \
--exclude redcapid,bbl_assessor,bbl_protocol,bbl_location

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield prime_screen \
--output phenotype/data/prime_screen.tsv \
--exclude redcapid,assessor,protocol

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield biss_madrs \
--output phenotype/data/biss_madrs.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield n_back_scores \
--output phenotype/data/n_back_scores.tsv

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield imaging_prescan_scales \
--output phenotype/data/imaging_prescan_scales.tsv \
--exclude redcapid,bbl_assessor,bbl_location

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield imaging_postscan_scales \
--output phenotype/data/imaging_postscan_scales.tsv \
--exclude redcapid,bbl_assessor,bbl_location

python phenotype/02_extract_info_subfield.py \
--subjects-root /cbica/projects/grmpy/sourcedata/GRMPY_822831/SUBJECTS \
--info-subfield self_report_itemwise \
--output phenotype/data/self_report_itemwise.tsv \
--exclude redcapid,bbl_assessor

```

## Scoring

The self-report itemwise data was split into separate files using the [`03_separate_self_reports.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/03_separate_self_reports.py) script. Imaging scales were split into separate files using the [`04_separate_imaging_scales.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/04_separate_imaging_scales.py) script. Self-report and imaging scales were then scored using the [`05_score_self_reports.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/05_score_self_reports.py) script. Developmental scales were separated and scored using the [`06_separate_dev_scales.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/06_separate_dev_scales.py) script. Axis data was extracted and scored using the [`07_process_axis.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/07_process_axis.py) script. These data were later merged into the participants.tsv file (see CUBIDS curation for more details). The CNB data was processed using the [`08_process_cnb.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/08_process_cnb.py) script. Prime data was scored using the [`09_process_prime.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/09_process_prime.py) script.

On July 8, 2026 files to be released were coppied to the phenotype/data/final/ folder. These files were copied into the phenotype folder in the raw openneuro dataset.


aces - completed + verified. JSON complete.

als - completed - i have just an average score, EF also has a sum. JSON complete.

ari - completed + verified. JSON complete.

bdi - completed + verified. JSON complete.

best-ms - completed + verified against self_report_summary.tsv. Note this is a best modified satterthwaite version of best. JSON complete.

bisbas - completed + verified against self_report_summary.tsv. EF is a child version. JSON complete.

biss_madrs - completed + verified w/ Ted. biss item 43 in data dictionary is not present in the data - asks about "why you are coming for psychiatric treatment" when the individuals in the study are not doing so. JSON complete.

bss - completed + verified against self_report_summary.tsv. JSON complete.

eswan_dmdd - completed + verified. Note: input was changed to range from -3 to 3 to match EF/PAFIN. JSON complete.

grit - compelted + verified against self_report_summary.tsv. JSON complete.

hcl16 - completed + verified against self_report_summary.tsv. R code only uses hcl6_3 questions for scoring - that seems correct as these are actual questions from the larger hcl 32. However, these 16 questions differ from the ones used in Forty et al 2010, which was the only 16 question version identified in this systematic review of short form versions of the hcl32: https://pubmed.ncbi.nlm.nih.gov/31066059/. Not in EF. JSON complete.

mapssr - completed + verified. JSON complete.

phys_anhed - scored as rpasShort - EF has this, did sum and average, while here is only sum. completed. JSON complete.

soc_anhed - scored as rsasShort - EF has this, did sum and average, while here is only sum. completed. JSON complete.

prime_screen - scored using the [`09_process_prime.py`](https://github.com/PennLINC/grmpy_opendata/blob/main/phenotype/09_process_prime.py) script. JSON complete.

***Proband_GOASSESS - only has summary/flagged columns. TODO - ignore for now, look in flyhweel for study group related to irritability.

psqi - completed + verified. sub-110354 says they spend 6am to 5am in bed but only sleep for 8 hours resulting in a component 4 score of 3 by my logic, but its 2 in the self_report_summary.tsv which means the scorer must have assumed the ptp meant they went to bed at 6pm. Component 4 score and the global score were set to n/a for this subject. JSON complete.

rpaq - complete + verified against self_report_summary.tsv. not in EF. JSON complete.

scared - completed + verified against self_report_summary.tsv. not in EF. JSON complete.

stai_pre_imaging - completed + verified. JSON complete.

stai_post_imaging - completed + verified. JSON complete.

staxi2-ca - scored by summing based on https://www.annarbor.co.uk/index.php?main_page=index&cPath=419_322. Anger expression subscales were not scored due to lack of clarity on the scoring logic. JSON complete.

swan (ADHD) - EF has this. But only totals, while grmpy R code scored based on thresholds. ALSO EF items ranged from 0-7 and was changed to -3 to 3 for scoring (code from dan's lab). while here the answers are all binary (0 = quite a bit or very much. 1 = not at all or just a little). Original publications says responses should range from -3 to 3. Would need to confirm 1) if reverse coding is needed, 2) if the R code is correct based on the inputs (are the thresholds imposed based on binary inputs?). Unclear if swan_total1 and swan_total2 are needed at all -- was in the R code but not in the self_report_itemwise.tsv. DECISION: DO NOT RELEASE.

suq - no scoring needed. added validity column on substance_othr_040/050 - should be 0 b/c drugs are fake. JSON complete.

spq - scored onsite, scoring logic in dev data dictionary pdf. JSON complete.

tanner_boy - no scoring needed. JSON complete.

tanner_girl - no scoring needed. JSON complete.

wolf_post_imaging - no scoring needed. JSON complete.

Diagnosis - release a subset of columns highlighted by ted. axis.tsv is the output to release.
