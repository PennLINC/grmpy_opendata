import os
import json
import re

def remove_bids_uri_from_intendedfor(bids_dir):
    """
    Remove BIDS URI (matching 'bids::sub-{id}/') from 'IntendedFor' fields in JSON files under the 'fmap' directory.
    
    Args:
    bids_dir (str): Path to the BIDS dataset directory.
    """
    bids_uri_pattern = re.compile(r'bids::sub-[^/]+/')

    for root, dirs, files in os.walk(bids_dir):
        if 'fmap' in root:
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    
                    if 'IntendedFor' in data:
                        intended_for = data['IntendedFor']
                        if isinstance(intended_for, list):
                            updated_intended_for = [
                                bids_uri_pattern.sub('', path) for path in intended_for
                            ]
                            data['IntendedFor'] = updated_intended_for
                        elif isinstance(intended_for, str):
                            data['IntendedFor'] = bids_uri_pattern.sub('', intended_for)
                        
                        with open(json_path, 'w') as f:
                            json.dump(data, f, indent=4)
                        print(f"Updated {json_path}")

if __name__ == "__main__":
    bids_dir = input("Enter the path to your BIDS dataset directory: ")
    remove_bids_uri_from_intendedfor(bids_dir)
