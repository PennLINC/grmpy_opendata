import glob
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

project_path = '/cbica/projects/executive_function/'

################
# concatenating
################
# path to unzipped xcpd data
inpath_qc = project_path + 'EF_dataset/derivatives/xcpd_BABS_EF_full_project_outputs/xcpd/' #CUBIC project path - replace
# outpath to save concatentaed qc data
outpath = project_path + 'EF_dataset_figures/concatenated_data/' #CUBIC project path - replace

# get all filenames for qc data
fileNames_qc = sorted(glob.glob(inpath_qc + 'sub-*/ses-*/func/' +
                                'sub-*_ses-*_task-*_run-*' +
                                '_motion.tsv'))

# get subject IDs based on filenames
subjList_qc = [fileNames_qc[s].split('/')[-1].split('_')[0]
               for s in range(len(fileNames_qc))]

# check filenames to define number of columns in the concatenated dataframe
# this is useful in case filenames are of different length
check_filename = [len(fileNames_qc[iSubj].split('/')[-1].split('_'))
                  for iSubj in range(len(subjList_qc))]
unique_namelength = np.unique(np.array(check_filename))
maxidx = np.where(np.array(check_filename) == unique_namelength.max())[0][0]

# generate empty main df for qc
# first get column names based on filenames
split_name = fileNames_qc[maxidx].split('/')[-1].split('_')
col_names_max = [split_title.split('-')[0] for split_title in split_name[:-1]]
# then get column names from the actual qc file
subj_qc = pd.read_csv(fileNames_qc[maxidx], delimiter='\t')
# finally generate main df for qc
df_main_qc = pd.DataFrame(columns=list(col_names_max) + list(subj_qc.columns))

# fill in the main qc df
for iSubj in range(len(subjList_qc)):
    # load each subject file
    subj_qc = pd.read_csv(fileNames_qc[iSubj], delimiter='\t')
    # Calculate the median across rows (each subj file has multiple rows)
    median_series = subj_qc.median(axis=0)
    # Convert the median Series to a dataframe with one row + reset index
    subj_qc_median = pd.DataFrame(median_series).T
    subj_qc_median = subj_qc_median.reset_index(drop=True)

    # get column values from filenames and make a temporary dataframe
    split_name = fileNames_qc[iSubj].split('/')[-1].split('_')
    col_names = [split_title.split('-')[0]
                 for split_title in split_name[:-1]]
    df_temp = pd.DataFrame(columns=col_names)
    col_vals = [split_title.split('-')[1]
                for split_title in split_name[:-1]]
    df_temp.loc[0] = col_vals

    # first combine temp dataframe with info from filenames with qc info
    df_subj_qc = pd.concat([df_temp, subj_qc_median], axis=1)

    # then add subj-level full qc info to the empty df_main_qc generated above
    df_main_qc = pd.concat([df_main_qc, df_subj_qc], ignore_index=True)

df_main_qc.to_csv(outpath + 'concat_xcpd_qc_median.csv',
                  index=False)

################
# plotting
################
# plot the median FD distribution
plt.ion()
# sns.histplot(df_main_qc['framewise_displacement'], kde=True, bins=20)
sns.displot(df_main_qc['framewise_displacement'], kde=True, bins=20)
plt.title('Median FD distribution')
plt.xlabel('Median FD')
plt.ylabel('Density')
plt.tight_layout()
plt.savefig(outpath + 'concat_xcpd_qc_histogram_median.png',
            bbox_inches='tight', dpi=300,
            transparent=True)
plt.close()
