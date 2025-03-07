#!/usr/bin/env python3
"""
Script to find files with multiple runs in a TSV file.
Extracts rows where 'run' is contained in the FilePath column.
"""

import argparse
import pandas as pd
import os

def find_multi_runs(input_file, output_file):
    """
    Find rows in a TSV file where 'run' is contained in the FilePath column.

    Parameters:
    -----------
    input_file : str
        Path to the input TSV file
    output_file : str
        Path to the output TSV file where matching rows will be saved
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Read the TSV file
    print(f"Reading input file: {input_file}")
    df = pd.read_csv(input_file, sep='\t')

    # Get the last column (FilePath)
    file_path_col = df.columns[-1]

    # Filter rows where 'run' is in the FilePath
    run_files = df[df[file_path_col].str.contains('run', case=False, na=False)]

    # Save the filtered rows to a new TSV file
    print(f"Found {len(run_files)} files containing 'run' in the path")
    run_files.to_csv(output_file, sep='\t', index=False)
    print(f"Results saved to: {output_file}")

    return len(run_files)

def main():
    parser = argparse.ArgumentParser(description='Find files with multiple runs in a TSV file')
    parser.add_argument('input_file', help='Path to the input TSV file')
    parser.add_argument('output_file', help='Path to the output TSV file')

    args = parser.parse_args()

    count = find_multi_runs(args.input_file, args.output_file)
    print(f"Total files with 'run' in path: {count}")

if __name__ == '__main__':
    main()