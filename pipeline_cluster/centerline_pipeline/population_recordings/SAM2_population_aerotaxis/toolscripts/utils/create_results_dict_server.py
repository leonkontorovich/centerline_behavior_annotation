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
    Condition, Genotype, Recording, Plate, Crop_ID, Frame, Time_Seconds,
    O2_State, Cycle_Index, Time_In_Phase_s, Forward_Velocity, Reversal_Active,
    Turn_Active, Reversal_Onset, Bend_Frequency, Bend_Amplitude, Occluded,
    X_mm, Y_mm, fps
(Cycle_Index/Time_In_Phase_s enable habituation analysis across pulses; X_mm/Y_mm
are the arena position for analysis-time displacement QC; `fps` is the true
per-recording frame rate so the analysis never assumes 10 fps. All are absent for
tables built by older pipeline versions — downstream code tolerates that.)

`Occluded` (1 = animal lost/occluded on that frame, from the SWC crop ledger)
is a per-frame quality flag: filter `Occluded == 0` before computing behaviour
rates, since occluded frames carry blank-crop-derived values. Absent for data
cropped by older SWC versions (then it is 0 everywhere).

The provenance columns are recovered from the folder structure
    <condition>/<recording>/<crop>/output/temporal_features.csv

`setup_aerotaxis_dataset.py` wraps each recording in its own `<recording>_new`
folder, so on disk the layout is `<recording>_new/<recording>/<crop>/...`. When
that per-recording wrapper is detected (the parent is just `<recording>_new`),
there is no genuine grouping folder, so `Condition` falls back to the parsed
`Genotype` -- giving you N2 vs rde vs nprrde as a plain groupby key exactly as
if the data had been laid out `<genotype>/<recording>/<crop>/...`. If you DO use
a real condition folder, its name (minus any trailing `_new`) is kept verbatim.

`Genotype` / `Plate` are parsed from the recording name with `--genotype-regex`
(default matches SWC names like `2026-06-20_11-00-53_N2_A` -> genotype `N2`,
plate `A`). If the name does not match, `Genotype` falls back to the full
recording name and `Plate` is blank, so nothing is ever silently dropped.
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

import json
import numpy as np

TARGET = "temporal_features.csv"

# Canonical allele mappings for known short tags
DEFAULT_GENOTYPE_MAP = {
    "N2": "N2",
    "rde": "rde-4(db2038)",
    "npr": "npr-1(ad609)",
    "rdenpr": "rde-4(db2039); npr-1(ad609)",
    "nprrde": "rde-4(db2039); npr-1(ad609)",
    "mut": "mut-16(pk710)",
}

# SWC recordings are named "<date>_<time>_<genotype>_<plate>", e.g.
# "2026-06-20_11-00-53_N2_A". Group 1 = genotype (may contain underscores, e.g.
# "npr_rde"); optional group 2 = plate/replicate token. Override with
# --genotype-regex (must expose named groups `genotype` and, optionally, `plate`).
DEFAULT_NAME_RE = (
    r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_(?P<genotype>.+?)"
    r"(?:_(?P<plate>[A-Za-z0-9]+))?$"
)


def _strip_new(name: str) -> str:
    """Drop the trailing '_new' wrapper that setup_aerotaxis_dataset.py adds."""
    return name[:-4] if name.endswith("_new") else name


def parse_recording_name(recording: str, name_re: "re.Pattern", genotype_map: dict = None):
    """Return (genotype, plate) parsed from a recording folder name.

    Falls back to (full name, '') when the name does not match, so an
    unexpected naming scheme never silently discards data.

    Stray whitespace is normalised before matching. Hand-typed recording names
    pick up spaces ("2026-06-17_11-51-38_N2_ B"), and the plate group is
    [A-Za-z0-9]+, so "_ B" fails to match as a plate. The name then falls back
    wholesale to Genotype="N2_ B" with an empty Plate -- and since Condition
    defaults to Genotype, that recording silently becomes its OWN condition
    group, split from the N2 it belongs to. Nothing errors; the stats are just
    quietly wrong. Collapsing internal whitespace first makes "N2_ B" parse
    identically to "N2_B".
    """
    recording = re.sub(r"\s+", "", recording)
    m = name_re.match(recording)
    if not m:
        raw_g, plate = recording, ""
    else:
        gd = m.groupdict()
        raw_g = gd.get("genotype") or recording
        plate = gd.get("plate") or ""

    if genotype_map and raw_g in genotype_map:
        genotype = genotype_map[raw_g]
    else:
        genotype = raw_g
    return genotype, plate


def _find_csv_files(source_path: Path) -> list[Path]:
    """Find all temporal_features.csv files efficiently."""
    csv_files = []
    try:
        subdirs = [p for p in source_path.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name != "log"]
        for p in subdirs:
            if (p / "output" / TARGET).is_file():
                csv_files.append(p / "output" / TARGET)
                continue
            inner_dirs = [q for q in p.iterdir() if q.is_dir() and not q.name.startswith(".") and q.name not in ("log", "report")]
            for q in inner_dirs:
                if (q / "output" / TARGET).is_file():
                    csv_files.append(q / "output" / TARGET)
                else:
                    for r in q.iterdir():
                        if r.is_dir() and not r.name.startswith(".") and (r / "output" / TARGET).is_file():
                            csv_files.append(r / "output" / TARGET)
    except Exception:
        csv_files = []

    if not csv_files:
        csv_files = list(source_path.rglob(f"*/output/{TARGET}"))
    return sorted(csv_files)


def collect(source_path: Path, name_re: "re.Pattern", genotype_map: dict = None) -> pd.DataFrame:
    frames = []
    csv_files = _find_csv_files(source_path)
    for csv in tqdm(csv_files, desc="Reading"):
        try:
            df = pd.read_csv(csv)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] skipping {csv}: {e}", file=sys.stderr)
            continue
        # provenance from folder structure: <condition>/<recording>/<crop>/output/...
        crop_dir = csv.parents[1]
        recording = _strip_new(crop_dir.parent.name)
        condition_raw = _strip_new(crop_dir.parents[1].name)
        genotype, plate = parse_recording_name(recording, name_re, genotype_map=genotype_map)
        
        # Derive date once in pipeline from recording name (leading YYYY-MM-DD)
        date_m = re.match(r"^(\d{4}-\d{2}-\d{2})", re.sub(r"\s+", "", recording))
        date = date_m.group(1) if date_m else ""

        # If the parent folder is just the per-recording "_new" wrapper (so it
        # collapses to the recording itself), there is no real condition folder;
        # group by genotype instead. Otherwise keep the genuine condition name.
        is_wrapper = re.sub(r"\s+", "", condition_raw) == re.sub(r"\s+", "", recording)
        condition = genotype if is_wrapper else condition_raw
        df.insert(0, "Date", date)
        df.insert(0, "Plate", plate)
        df.insert(0, "Recording", recording)
        df.insert(0, "Genotype", genotype)
        df.insert(0, "Condition", condition)
        frames.append(df)

    if not frames:
        raise SystemExit(f"No {TARGET} files found under {source_path}")
    tidy = pd.concat(frames, ignore_index=True)

    # Freeze declared estimand windows (§7): 7 % p_start - 30 -> p_start, 21 % p_end - 10 -> p_end
    # Protocol: 10 pulses, pulse i (0..9): p_start = 240 + i*90, p_end = 270 + i*90
    pulse_starts = [240 + i * 90 for i in range(10)]
    pulse_ends = [270 + i * 90 for i in range(10)]
    in_win_7 = np.zeros(len(tidy), dtype=bool)
    in_win_21 = np.zeros(len(tidy), dtype=bool)
    for ps, pe in zip(pulse_starts, pulse_ends):
        in_win_7 |= (tidy["Time_Seconds"] >= ps - 30.0) & (tidy["Time_Seconds"] < ps)
        in_win_21 |= (tidy["Time_Seconds"] >= pe - 10.0) & (tidy["Time_Seconds"] < pe)
    tidy["in_declared_window"] = in_win_7 | in_win_21

    # Biological QC flags from rde4_dossier.md §3.7 / Stats_3.py
    # Evaluated on declared windows across the 10-pulse protocol
    b_df = tidy[in_win_7]
    pk_df = tidy[in_win_21]
    b_mean = b_df.groupby(["Recording", "Crop_ID"])["Forward_Velocity"].apply(lambda x: np.nanmean(np.abs(x))) * 1000.0
    pk_mean = pk_df.groupby(["Recording", "Crop_ID"])["Forward_Velocity"].apply(lambda x: np.nanmean(np.abs(x))) * 1000.0

    vb_tracks = set(b_mean[(b_mean >= 0) & (b_mean <= 250)].index)
    vp_tracks = set(pk_mean[(pk_mean >= 0) & (pk_mean <= 350)].index)
    common = b_mean.index.intersection(pk_mean.index)
    delta_mean = pk_mean.loc[common] - b_mean.loc[common]
    vd_tracks = set(delta_mean[(delta_mean >= -150) & (delta_mean <= 350)].index)

    track_idx = pd.MultiIndex.from_arrays([tidy["Recording"], tidy["Crop_ID"]])
    tidy["valid_baseline"] = track_idx.isin(vb_tracks)
    tidy["valid_peak"] = track_idx.isin(vp_tracks)
    tidy["valid_delta"] = track_idx.isin(vd_tracks)

    return tidy


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?", default=".", help="dataset folder (default: cwd)")
    ap.add_argument("--format", choices=["parquet", "csv", "pkl"], default="parquet")
    ap.add_argument("--output", "-o", default=None,
                    help="custom output file path (default: aerotaxis_results.<format> in source folder)")
    ap.add_argument("--genotype-regex", default=DEFAULT_NAME_RE,
                    help="regex with named group `genotype` (and optional `plate`) "
                         "applied to each recording folder name "
                         "(default matches SWC `<date>_<time>_<genotype>_<plate>`)")
    ap.add_argument("--genotype-map", default="default",
                    help="mapping from raw parsed genotype tag to canonical allele label "
                         "(JSON string, JSON filepath, 'default', or 'none' to disable)")
    args = ap.parse_args()

    try:
        name_re = re.compile(args.genotype_regex)
    except re.error as e:
        raise SystemExit(f"Invalid --genotype-regex: {e}")

    gmap = None
    if args.genotype_map and args.genotype_map.lower() != "none":
        if args.genotype_map.lower() == "default":
            gmap = DEFAULT_GENOTYPE_MAP
        elif Path(args.genotype_map).is_file():
            with open(args.genotype_map) as f:
                gmap = json.load(f)
        else:
            try:
                gmap = json.loads(args.genotype_map)
            except json.JSONDecodeError as e:
                raise SystemExit(f"Invalid --genotype-map JSON: {e}")

    src = Path(args.source).resolve()
    if args.output:
        out = Path(args.output).resolve()
    else:
        out = src / f"aerotaxis_results.{args.format}"

    print(f"Source folder: {src}")
    print(f"Output file:   {out}")
    if gmap:
        print(f"Genotype map:  {gmap}\n")
    else:
        print("Genotype map:  (disabled)\n")

    tidy = collect(src, name_re, genotype_map=gmap)

    if args.format == "parquet":
        tidy.to_parquet(out, index=False)
    elif args.format == "csv":
        tidy.to_csv(out, index=False)
    else:
        tidy.to_pickle(out)

    print(f"\nWrote {len(tidy):,} rows x {tidy.shape[1]} cols -> {out}")
    print("\nRows per Condition x O2_State:")
    print(tidy.groupby(["Condition", "O2_State"]).size())
