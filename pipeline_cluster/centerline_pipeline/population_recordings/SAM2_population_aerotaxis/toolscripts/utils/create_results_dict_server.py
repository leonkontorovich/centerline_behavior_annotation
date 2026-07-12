#!/usr/bin/env python3
"""
Combine per-crop temporal_features.csv files into ONE flat, tidy table
for downstream analysis in Pandas / Seaborn or R.

Usage (run from the dataset folder):
    python /path/to/create_results_dict_server.py .              # -> parquet (default)
    python /path/to/create_results_dict_server.py . --format csv
    python /path/to/create_results_dict_server.py . --format pkl

Output (in the dataset folder):
    aerotaxis_results.{parquet,csv,pkl}

Columns:
    Condition, Recording, Crop_ID, Frame, Time_Seconds, O2_State,
    Forward_Velocity, Reversal_Active, Turn_Active

The `Condition` / `Recording` columns are recovered from the folder structure
    <condition>/<recording>/<crop>/output/temporal_features.csv
so each condition (e.g. genotype or paradigm) remains a simple groupby key --
no MultiIndex, no custom dict to unpickle.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

TARGET = "temporal_features.csv"


def collect(source_path: Path) -> pd.DataFrame:
    frames = []
    csv_files = sorted(source_path.rglob(f"*/output/{TARGET}"))
    for csv in tqdm(csv_files, desc="Reading"):
        try:
            df = pd.read_csv(csv)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] skipping {csv}: {e}", file=sys.stderr)
            continue
        # provenance from folder structure: <condition>/<recording>/<crop>/output/...
        crop_dir = csv.parents[1]
        recording_dir = crop_dir.parent
        condition_dir = recording_dir.parent
        df.insert(0, "Recording", recording_dir.name)
        df.insert(0, "Condition", condition_dir.name)
        frames.append(df)

    if not frames:
        raise SystemExit(f"No {TARGET} files found under {source_path}")
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", default=".", help="dataset folder (default: cwd)")
    ap.add_argument("--format", choices=["parquet", "csv", "pkl"], default="parquet")
    args = ap.parse_args()

    src = Path(args.source).resolve()
    out = src / f"aerotaxis_results.{args.format}"

    print(f"Source folder: {src}")
    print(f"Output file:   {out}\n")

    tidy = collect(src)

    if args.format == "parquet":
        tidy.to_parquet(out, index=False)
    elif args.format == "csv":
        tidy.to_csv(out, index=False)
    else:
        tidy.to_pickle(out)

    print(f"\nWrote {len(tidy):,} rows x {tidy.shape[1]} cols -> {out}")
    print("\nRows per Condition x O2_State:")
    print(tidy.groupby(["Condition", "O2_State"]).size())
