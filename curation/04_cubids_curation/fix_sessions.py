import os
import shutil
import json

def fix_sessions(subject_dir):
    """
    Performs two operations for a given subject directory:

    1. Removes the 'ses-1' directory and renames the 'ses-2' directory (and its contained
       file and directory names that reference "ses-2") to 'ses-1'.

    2. Recursively searches for JSON files within any 'fmap' directory under the subject and
       updates the 'IntendedFor' field by replacing occurrences of 'ses-2' with 'ses-1'.

    Args:
        subject_dir (str): Path to the subject directory (e.g., /path/to/bids/sub-XX)
    """
    ses1_path = os.path.join(subject_dir, 'ses-1')
    ses2_path = os.path.join(subject_dir, 'ses-2')

    # Delete ses-1 directory if it exists
    if os.path.exists(ses1_path):
        print(f"Deleting existing directory: {ses1_path}")
        shutil.rmtree(ses1_path)
    else:
        print(f"No 'ses-1' directory exists at {ses1_path}.")

    # Check that the ses-2 directory exists before proceeding
    if not os.path.exists(ses2_path):
        print(f"No 'ses-2' directory found at {ses2_path}. Exiting operation.")
        return

    # Rename ses-2 directory to ses-1
    new_ses1_path = ses1_path  # we want it renamed to 'ses-1'
    print(f"Renaming {ses2_path} to {new_ses1_path}")
    os.rename(ses2_path, new_ses1_path)

    # Recursively update filenames names that include 'ses-2'
    for root, dirs, files in os.walk(new_ses1_path, topdown=False):
        # Update filenames
        for filename in files:
            if 'ses-2' in filename:
                old_filepath = os.path.join(root, filename)
                new_filename = filename.replace('ses-2', 'ses-1')
                new_filepath = os.path.join(root, new_filename)
                print(f"Renaming file: {old_filepath} -> {new_filepath}")
                os.rename(old_filepath, new_filepath)

    # Now, update the fmap JSON files to reflect the session renaming in the 'IntendedFor' field.
    # We search under the subject directory for any JSON in paths that include 'fmap'
    for root, dirs, files in os.walk(subject_dir):
        if 'fmap' in root:
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r') as f:
                            data = json.load(f)
                    except Exception as e:
                        print(f"Unable to open {json_path}: {e}")
                        continue

                    # Update the IntendedFor field if it exists by replacing 'ses-2' with 'ses-1'
                    if 'IntendedFor' in data:
                        intended_for = data['IntendedFor']
                        if isinstance(intended_for, list):
                            updated_intended_for = [
                                item.replace('ses-2', 'ses-1') for item in intended_for
                            ]
                            data['IntendedFor'] = updated_intended_for
                        elif isinstance(intended_for, str):
                            data['IntendedFor'] = intended_for.replace('ses-2', 'ses-1')

                        with open(json_path, 'w') as f:
                            json.dump(data, f, sort_keys=True, indent=4)
                        print(f"Updated {json_path}")

    print("Session conversion complete.")

if __name__ == "__main__":
    subject_dir = input("Enter the path to the subject directory (e.g., /path/to/bids/sub-XX): ").strip()
    if not os.path.isdir(subject_dir):
        print(f"Error: The directory '{subject_dir}' does not exist or is not a valid directory.")
    else:
        fix_sessions(subject_dir)