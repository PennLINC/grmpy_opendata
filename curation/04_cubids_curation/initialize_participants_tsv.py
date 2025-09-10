import os


def generate_participants_tsv(bids_dir):
    """
    Search for all directories beginning with 'sub-' in the BIDS dataset directory
    and generate a 'participants.tsv' file listing these directories under the 'participant_id' column.

    Args:
        bids_dir (str): Path to the root of the BIDS dataset.
    """
    subjects = []

    # Loop over the items in the bids directory
    for item in sorted(os.listdir(bids_dir)):
        item_path = os.path.join(bids_dir, item)
        if os.path.isdir(item_path) and item.startswith("sub-"):
            subjects.append(item)

    # Define the output file path
    participants_path = os.path.join(bids_dir, "participants.tsv")

    # Write the participant IDs to the TSV file with a header
    with open(participants_path, "w") as f:
        f.write("participant_id\n")
        for subject in subjects:
            # Normalize to ensure exactly one 'sub-' prefix
            label = subject[4:] if subject.startswith("sub-") else subject
            f.write(f"sub-{label}\n")

    print(f"Created {participants_path} with {len(subjects)} subject(s).")


if __name__ == "__main__":
    bids_dir = input("Enter the path to your BIDS dataset directory: ")
    generate_participants_tsv(bids_dir)
