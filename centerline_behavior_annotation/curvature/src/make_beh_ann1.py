import os
import pandas as pd
import numpy as np
import argparse
import sys

def categorize_value(x):
    """Categorize the value into 1, 0, or -1."""
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

def modify_csv(beh_ann1_path, project_folder, output_file):
    threshold = 50

    # Read the CSV file using pandas, assuming no header
    df = pd.read_csv(beh_ann1_path, header=None)

    # Ensure initial values are 1, 0, or -1
    df[1] = df[1].apply(categorize_value)

    # Perform the rolling mean operation
    df[1] = df[1].rolling(window=50, min_periods=1).mean()

    # Categorize the rolling mean results into 1, 0, or -1
    df[1] = df[1].apply(categorize_value)

    # Apply the majority filtering from the first script
    for i in range(1, len(df)):  # Start from 1 to skip the header row
        window = df[1].iloc[max(i - threshold, 1):min(i + threshold, len(df))]
        majority = window.mode()[0]
        if len(window[window == df[1].iloc[i]]) < threshold:
            df[1].iloc[i] = majority

    # Write the modified dataframe to a new CSV file
    df.to_csv(output_file, header=False, index=False)
    print(f"Modified CSV saved at: {output_file}")

def main(arg_list=None):

    parser = argparse.ArgumentParser(description='Modify behavior annotation CSV file')
    parser.add_argument('--input_path', help='Input CSV file path', required=True)
    parser.add_argument('--input_file',  help='Input CSV file path', required=True)
    parser.add_argument('--output_file', help='Input CSV file path', required=True)

    args = parser.parse_args(arg_list)

    input_file = args.input_file
    output_file = args.output_file

    main_folder = args.input_path

    project_folder = main_folder

    beh_ann1_path = input_file

    modify_csv(beh_ann1_path, project_folder, output_file)


if __name__ == '__main__':

    main(sys.argv[1:])

