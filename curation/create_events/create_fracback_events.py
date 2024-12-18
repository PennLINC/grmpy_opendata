import pandas as pd
from glob import glob

# Parameters
input_files = ["0back.txt", "1back.txt", "2back.txt", "instr.txt"]
output_file = "task-fracback_acq-singleband_events.tsv"

# Function to merge consecutive blocks
def merge_blocks(df, trial_type):
    df = df.sort_values("onset").reset_index(drop=True)
    blocks = []
    current_block = {"onset": df.loc[0, "onset"], "duration": df.loc[0, "duration"]}
    for i in range(1, len(df)):
        if df.loc[i, "onset"] == current_block["onset"] + current_block["duration"]:
            current_block["duration"] += df.loc[i, "duration"]
        else:
            blocks.append(current_block)
            current_block = {"onset": df.loc[i, "onset"], "duration": df.loc[i, "duration"]}
    blocks.append(current_block)
    return pd.DataFrame(blocks).assign(trial_type=trial_type)

# Process all files and combine them
all_events = []
for file in input_files:
    trial_type = file.split(".")[0]  # Extract trial type from file name
    df = pd.read_csv(file, sep="\t", header=None, names=["onset", "duration", "ignore"])
    merged_df = merge_blocks(df, trial_type)
    all_events.append(merged_df)

# Combine all trial types and save to a BIDS-compatible file
events = pd.concat(all_events).sort_values("onset").reset_index(drop=True)
events.to_csv(output_file, sep="\t", index=False)

print(f"Events file created: {output_file}")