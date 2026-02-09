#!/usr/bin/env python3
"""
Create results_dict.pkl from chemotaxis CSV files.

Usage (run from dataset folder):
    python /path/to/create_results_dict_server.py .

Output: results_dict.pkl in the dataset folder
"""

import os
import sys
import pickle
from pathlib import Path
from tqdm import tqdm
import pandas as pd

NAN_THRESHOLD_PERCENT = 40


def process_chemotaxis_files(source_path: str, target_filename: str = "chemotaxis_params.csv",
                             nan_threshold_percent: int = 40) -> dict:
    """
    Process chemotaxis CSV files from folder structure and combine them.
    """
    source_path = Path(source_path)
    results_dict = {}

    subfolders = [sf for sf in source_path.iterdir() if sf.is_dir()]

    print(f"Processing {len(subfolders)} recording folders...")

    for subfolder in tqdm(subfolders, desc="Processing"):
        for subsubfolder in subfolder.iterdir():
            if not subsubfolder.is_dir():
                continue

            subsubfolder_dfs = []

            for subsubsubfolder in subsubfolder.iterdir():
                if not subsubsubfolder.is_dir():
                    continue

                output_folder = subsubsubfolder / "output"
                target_file = output_folder / target_filename

                if target_file.exists():
                    try:
                        df = pd.read_csv(target_file, header=[0, 1], index_col=0)
                        df[('trackID', 'trackID')] = subsubsubfolder.name

                        spline_k_df = df.loc[:, df.columns.get_level_values(0) == 'Spline_K']

                        if spline_k_df.isna().any(axis=1).mean() * 100 < nan_threshold_percent:
                            subsubfolder_dfs.append(df)

                    except Exception as e:
                        print(f"Error reading {target_file}: {e}")

            if subsubfolder_dfs:
                combined_df = pd.concat(subsubfolder_dfs, axis=0)
                results_dict[subsubfolder.name] = combined_df

    return results_dict


if __name__ == "__main__":
    # Get source folder from command line argument (default: current directory)
    if len(sys.argv) > 1:
        source_folder = Path(sys.argv[1]).resolve()
    else:
        source_folder = Path.cwd()

    # Output file in the same folder
    output_file = source_folder / "results_dict.pkl"

    print(f"Source folder: {source_folder}")
    print(f"Output file:   {output_file}")
    print()

    results_dict = process_chemotaxis_files(source_folder, nan_threshold_percent=NAN_THRESHOLD_PERCENT)

    print(f"\nLoaded {len(results_dict)} recordings:")
    total_rows = 0
    for key, df in results_dict.items():
        print(f"  {key}: {len(df)} rows")
        total_rows += len(df)
    print(f"\nTotal: {total_rows} rows")

    print(f"\nSaving to {output_file}...")
    with open(output_file, 'wb') as f:
        pickle.dump(results_dict, f)

    size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"Done! File size: {size_mb:.1f} MB")
