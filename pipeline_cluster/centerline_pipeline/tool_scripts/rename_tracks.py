#!/usr/bin/env python3
"""
Renames the outputs of the Simple Worm Cropper to match the pipeline convention.
Specifically, it renames:
- `*_track_N.tif` -> `track.tif`
- `*_track_N.txt` -> `track.txt`
- `*_metadata.json` -> `track_metadata.json`

Usage:
    python rename_tracks.py <target_directory>
"""

import os
import sys
import glob

def rename_tracks_in_dir(target_dir):
    print(f"Checking directory: {target_dir}")
    # We look for all *_track_* directories inside the dataset directories
    # The structure is Dataset / Condition / *_track_N
    for condition_dir in glob.glob(os.path.join(target_dir, "*")):
        if os.path.isdir(condition_dir):
            for track_dir in glob.glob(os.path.join(condition_dir, "*_track_*")):
                if os.path.isdir(track_dir):
                    # Rename .tif
                    for f in glob.glob(os.path.join(track_dir, "*_track_*.tif")):
                        new_f = os.path.join(track_dir, "track.tif")
                        print(f"Renaming {f} -> {new_f}")
                        os.rename(f, new_f)
                        
                    # Rename .txt
                    for f in glob.glob(os.path.join(track_dir, "*_track_*.txt")):
                        new_f = os.path.join(track_dir, "track.txt")
                        print(f"Renaming {f} -> {new_f}")
                        os.rename(f, new_f)
                        
                    # Rename metadata
                    for f in glob.glob(os.path.join(track_dir, "*_metadata.json")):
                        new_f = os.path.join(track_dir, "track_metadata.json")
                        print(f"Renaming {f} -> {new_f}")
                        os.rename(f, new_f)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rename_tracks.py <target_directory>")
        sys.exit(1)
        
    target = sys.argv[1]
    rename_tracks_in_dir(target)
    print("Done renaming files!")
