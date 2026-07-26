# Population Aerotaxis Pipeline — Protocol & Guide

Temporal (non-spatial) behavioural analysis for **global plate-level gas-shift**
assays (aerotaxis / O₂-sensing). Behaviour — speed, reversals, turns, body-bend
frequency — is locked to global gas shifts (a baseline O₂ level, then repeating
pulse/return cycles). There are **no gradients, no odor position, no chemotaxis
index**.

This pipeline shares all upstream tracking (SAM2 segmentation, DLC, centerline,
curvature, reversals, turns, Hilbert) with the chemotaxis pipeline and only
replaces the final analysis with a temporal one.

- **Reference cropper output** inspected while building this:
  `/Volumes/scratch/neurobiology/zimmer/LeonK/rde4_behavior/LeonL1/2026-06-20_11-00-53_N2_A`
  (SWC v1.1.0; 10 fps; 2.5 cm arena; 2048 px sensor; 187 tracks).

---

## Contents
1. [How the assay maps to the pipeline](#1-how-the-assay-maps-to-the-pipeline)
2. [The gas protocol (config)](#2-the-gas-protocol-config)
3. [One-time setup](#3-one-time-setup)
4. [Step-by-step run protocol](#4-step-by-step-run-protocol)
5. [Outputs & the tidy table](#5-outputs--the-tidy-table)
6. [Downstream analysis](#6-downstream-analysis)
7. [Monitoring, cleanup & single-crop debug](#7-monitoring-cleanup--single-crop-debug)
8. [Troubleshooting](#8-troubleshooting)
9. [Configuration reference](#9-configuration-reference)

---

## 1. How the assay maps to the pipeline

```
raw recording ──► SWC cropper ──► one folder per worm track
                                   (<...>_track_N.tif + <...>_track_N.txt position log)
        │
        ▼  (upstream, unchanged: SAM2 → DLC → centerline → curvature →
        │   reversals → turns → Hilbert body-bends)
        ▼
  aerotaxis_temporal_analysis  ──►  output/temporal_features.csv   (one per crop, tidy per-frame)
        │
        ▼
  create_results_dict_server.py ──►  aerotaxis_results.parquet     (one flat table for the whole dataset)
        │
        ▼
  aerotaxis_analysis.py / notebook ──► per-state summaries, gas-transition-triggered averages,
                                       reversal-reaction latency, per-crop viewer
```

**Key idea — one global clock.** Each crop is only a *segment* of the recording
and starts at a different time, but the gas protocol is global to the plate. The
SWC `track.txt` logs the **absolute** recording frame/time (`time_imputed_seconds`)
and the worm's **absolute arena position** (`X,Y` in px). The extractor uses that
as the authoritative clock, so every crop locks to the same protocol. `Forward_Velocity`
is derived from the arena `X,Y` trajectory (px→mm, signed by reversal state).

### Dataset folder structure (flat — no extra nesting)
```
Working_dir/
├── 2026-06-20_11-00-53_N2_A/         (condition / recording 1)
│   ├── parameters.yaml               (auto-parsed by the pipeline)
│   ├── tracks.json                   (SWC ledger)
│   ├── <...>_track_0/  ├── <...>_track_0.tif  └── <...>_track_0.txt
│   ├── <...>_track_1/  └── ...
│   └── ...                           (other SWC outputs: logs, report/, etc.)
├── 2026-06-20_12-10-05_gcy35_A/      (condition / recording 2)
└── ...
```
- Each recording folder needs a **unique identifier** in its name; downstream
  code uses the top-level folder as the `Condition` and the mid folder as the
  `Recording` grouping key.
- Multiple conditions per dataset are supported (e.g. a genotype panel).
- **Avoid spaces in recording names.** `..._N2_ B` is normalised away when
  parsing genotype/plate, but the space still travels into the `Recording`
  value and every path that quotes it. Name them `..._N2_B`.

### What the pipeline reads from the cropper (SWC contract)

Everything below comes from SWC output; the pipeline never re-derives it. If a
key is absent — older SWC build, hand-assembled dataset — the pipeline falls
back to `config.yaml` and says so on a `[swc] ... FALLBACK` line.

| SWC writes | Where | Pipeline uses it for |
|---|---|---|
| `<rec>_track_N.tif` | crop folder | → `track.tif` (step 2) — the frames |
| `<rec>_track_N.txt` | crop folder | → `track.txt` — absolute clock (`time_imputed_seconds`) and arena position (`X`,`Y`); the basis of all gas alignment |
| `<rec>_track_N_metadata.json` | crop folder | per-frame `is_missing_frame` → `Occluded`; `animal_clipped` → `Animal_Clipped` |
| `recording.fps` | `parameters.yaml` | the clock. SWC keeps the **configured** value here |
| `recording.fps_measured_from_metadata` | `parameters.yaml` | provenance only — the pipeline **warns** if it disagrees with `recording.fps` by >5 %, and (like SWC) does not override |
| `recording.pixel_size_mm`, `frame_height_px` | `parameters.yaml` | px→mm for velocity, and for converting `min_worm_length_mm` to pixels |
| `region_extraction.min/max_region_size` | `parameters.yaml` | `min/max_worm_area` for the turn/coil detector |

> **Older crops:** `pixel_size_mm` / `frame_height_px` were added by SWC's
> calibration-persistence change. Datasets cropped before it lack them, so
> px→mm falls back to `config.yaml` — verify that fallback equals your
> arena width ÷ frame width. Re-cropping with a current SWC build removes the
> guesswork.

---

## 2. The gas protocol (config)

The assay timing lives in `config.yaml` under `aerotaxis:` and is applied per
frame from the **absolute** recording time. You normally **don't edit it by
hand**: the setup script in [§4](#4-step-by-step-run-protocol) (step 3) writes
this block for you by parsing your Alicat `.txt` gas script. It reads the
standard **baseline → pulse → return** shape (line 1 = baseline, line 2 = pulse,
line 3 = return). For anything more elaborate — extra cycle phases, a
camera/gas start offset, or capping the number of cycles — edit the block
directly afterwards; no code change is needed and `O2_State` follows
automatically.

```yaml
aerotaxis:
  t0_offset_s: 0.0             # absolute recording time (s) at which the protocol starts
                               # (0 = protocol begins at recording t=0; earlier frames -> "pre_protocol")
  baseline_duration_s: 240     # Maps to the first line in your script (e.g. 240s of 7%)
  baseline_state: "7pct_O2"
  cycle:                       # One repeating unit; phases applied in order
    - {state: "21pct_O2", duration_s: 30}   # Maps to the 30s 21% pulse
    - {state: "7pct_O2",  duration_s: 60}   # Maps to the 60s 7% return
  n_cycles: null               # null = repeat to end of recording; or an int to cap
```

Default = **4-min 7 % O₂ baseline, then repeating 30 s 21 % pulse / 60 s 7 %
return**. For any other paradigm, change `baseline_*` and the `cycle` phase list;
the `O2_State` column follows automatically.

### 2.1 Critical Nuances for a Bullet-proof Analysis
To ensure your temporal alignment is flawless, beware of these common pitfalls:

1. **Camera Start vs. Gas Start Synchronization (`t0_offset_s`)**
   Your mass flow controller `.txt` script starts running the moment you execute it, but your camera recording might have started slightly earlier or later. 
   - If you started the camera 15 seconds *before* starting the gas script, you must set `t0_offset_s: 15.0`. 
   - If you do not account for this human delay, all your transition-triggered averages (e.g., speed spikes at gas shifts) will be shifted and blurry!
2. **Do NOT try to manually tune FPS, Pixel Size, or Worm Area in `config.yaml`**
   The Snakemake pipeline is built to automatically override `config.yaml` by extracting `fps`, `pixel_size_mm`, `min_worm_area`, and `max_worm_area` directly from the `parameters.yaml` file generated by the Simple Worm Cropper (SWC). If you want to change these values, tune them upstream in SWC before cropping, rather than editing `config.yaml`.

   **Check the `[swc]` lines at the top of every run log.** Each recording
   reports the value it resolved *and where it came from*:
   ```
   [swc] <recording>: fps = 10  (source: parameters.yaml)
   [swc] <recording>: factor_px_to_mm = 0.01221  (source: config.yaml fallback)  <-- FALLBACK, verify this fits your cropper output
   [swc] <recording>: min_worm_length_px = 32.8  (source: min_worm_length_mm x parameters.yaml)
   ```
   A `FALLBACK` line means SWC did **not** supply that key and a generic config
   number is standing in. That is often fine — but it is exactly how a value
   tuned for a different microscope reaches your data unnoticed, so confirm it
   matches this rig before trusting the run. Older SWC versions omit
   `pixel_size_mm` and `frame_height_px`, so `factor_px_to_mm` commonly falls
   back; verify it equals your arena width ÷ frame width.

3. **Worm-size thresholds are in millimetres, not pixels**
   `min_worm_length_mm` (default `0.4`) is converted to pixels per recording
   using that recording's px→mm calibration. Worm length in mm is biology and
   travels between rigs; worm length in *pixels* depends entirely on
   magnification and does not.

   This is a **junk floor** — it exists to reject debris and broken mask
   fragments, and sits far below a real adult (~0.8–1.1 mm). Raising it toward
   the median does not improve quality, it silently deletes frames. Selecting
   real worms is the analysis-time aliveness gate's job ([§6](#6-downstream-analysis)).

   > ⚠️ **This threshold has bitten before.** It was previously a hardcoded
   > pixel value (`min_worm_lenght: 83`) tuned where worms imaged at ~1.0 mm.
   > On a dataset whose worms imaged at ~60–70 px it blanked ~99 % of frames;
   > every crop collapsed to an empty curvature table and 4,190 of 4,576 crops
   > died in `annotate_reversals`. To check it against *your* worms before
   > committing a run, see [§4 step 4a](#4-step-by-step-run-protocol).
3. **Missing `track.txt` absolute positions**
   The pipeline relies on `track.txt` generated by SWC for absolute tracking and timestamps. If you ever see a warning in the logs about *`local clock ... ABSOLUTE gas alignment NOT guaranteed`*, it means the file is missing and temporal alignment will fail.

---

## 3. One-time setup

### 3.1. Conda Setup
Only needed the first time you use conda on the LISC login.
```bash
module load conda
echo 'module load conda' >> ~/.bashrc
conda config --append envs_dirs /lisc/data/scratch/neurobiology/zimmer/.conda/envs
conda env list      # confirm environments are visible
```

### 3.2. Clone Your Isolated Repository (CRITICAL)
Because the aerotaxis pipeline is still under active development on your personal branch, **do not run this code using the shared lab repository** (`/lisc/data/scratch/neurobiology/zimmer/autoscope/...`). That can cause merge conflicts and break other people's pipelines.

Instead, clone your fork directly into your personal scratch space (e.g. `LeonK`) and switch to the correct branch:
```bash
cd /lisc/data/scratch/neurobiology/zimmer/LeonK
git clone https://github.com/leonkontorovich/centerline_behavior_annotation.git
cd centerline_behavior_annotation
git checkout aerotaxis-temporal-pipeline
```
All commands in this guide assume your clone is located at `/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation`. If you clone it elsewhere, simply adjust the paths accordingly.
---

## 4. Step-by-step run protocol

> Run **every** command from within the working directory that contains your
> recording folders (`cd` there first; check with `pwd`).

**1. Go to the dataset and activate the environment**
```bash
cd "path/to/folder/of/cropped/recordings"
conda activate autoscope_behaviour_shared
```

**2. Rename the SWC files to the pipeline convention** (`*_track_N.tif` → `track.tif`)
```bash
python "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/tool_scripts/rename_tracks.py" "$PWD"
```

**3. Automate the folder structure and gas protocol configurations**
This single master script will create the necessary nested `*_new` folders, copy the entire pipeline into them, and automatically read your Alicat `.txt` gas script to perfectly populate every `config.yaml` file across the dataset.
```bash
python "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/tool_scripts/setup_aerotaxis_dataset.py" "$PWD" "PATH_TO_YOUR_GAS_SCRIPT.txt"
```
*(Replace `PATH_TO_YOUR_GAS_SCRIPT.txt` with the path to the Alicat `.txt` file you used for this specific experiment).*

*3a. Need to re-copy pipeline files only? (existing structure):*
```bash
bash "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/copy_aerotaxis_population_pipeline.sh"
```

**4. Double-check your config (optional).**
Open one `config.yaml` inside a `*_new/` folder and confirm the `aerotaxis:`
block matches your assay. Do **not** set `fps` or `factor_px_to_mm` here — they
are read per recording from SWC (see [§2.1](#21-critical-nuances-for-a-bullet-proof-analysis)
and [§9](#9-configuration-reference)).

**4a. Check the worm-size threshold against your actual worms.** Strongly
recommended on any new rig, objective, magnification, or worm stage — it takes
a couple of minutes and catches the one failure mode that can silently void an
entire multi-day run.
```bash
python "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/toolscripts/utils/calibrate_min_worm_length.py" . --per-recording 25
```
This measures your worms from the DLC keypoints and prints the length
distribution in px and mm, how many crops each candidate threshold would
discard, and a recommended `min_worm_length_mm`. It needs no GPU.

Run it **after** a first pass has produced DLC output (so the `*_filtered.h5`
files exist); on a brand-new dataset, run one recording through first. If the
recommendation differs materially from the `min_worm_length_mm` in your
`config.yaml`, update the config and re-copy it (step 3a) before launching the
full dataset.

**5. (Optional) Bubble filter — throughput only, NOT biological QC.**
> ⚠️ This step's **only** purpose is to stop **thousands** of junk bubble crops
> from flooding the cluster queue. It is **not** how you quality-control worms:
> the biological QC is the lenient, non-destructive **aliveness gate** applied at
> analysis time ([§6](#6-downstream-analysis)), which keeps slow *and* fast real
> worms and drops only inert objects — nothing is deleted on disk. So:
> **skip this step** unless a recording has ballooned to many hundreds/thousands
> of crops because the cropper jittered on bubbles. If your SWC `min/max` region
> sizes already keep crop counts reasonable (a few hundred per recording), you do
> not need it at all.

**How it works & its limits (read before `--delete`, it is irreversible):**
The filter deletes any track whose **absolute arena-position SD**
(`sqrt(SD(X)² + SD(Y)²)` from `track.txt`) is `≤ --threshold` **pixels**. Real
crawling worms sit far above the default 15 px (typically 50–500 px), and bubbles
sit near 0, so the default cleanly separates them **in well-behaved recordings**.
Two caveats:
> - **It is duration-blind.** SD is not normalised by track length, so a genuine
>   worm that was only tracked for a few seconds (near `min_track_duration`) can
>   have a small SD and be deleted alongside true bubbles. Inspect the borderline
>   band (SD ≈ 10–20 px) rather than trusting the cut blindly.
> - **High deletion % usually means a junky recording, not an over-harsh
>   threshold.** (In the reference dataset, one plate was ~77 % low-motion
>   detections — those really were stationary debris, median total path ~130 px.)
>   But confirm per recording.

Every run writes `Output_Bubble_Filter/{SD_Summary.csv, Clustering_Results.csv,
clustering_plot.html}` next to the crops — **open the plot / CSV and eyeball the
Stationary/Non-Stationary split before deleting.** Lower `--threshold` (e.g. 10)
if you see real short tracks in the cut.
```bash
# Dry-run (shows what would be deleted; writes the SD summary + plot to inspect):
python "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/toolscripts/bubble_filter/NTF_compact.py" --src . --threshold 15.0
# Then delete (irreversible — the track folders are rm -rf'd):
python "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/toolscripts/bubble_filter/NTF_compact.py" --src . --threshold 15.0 --delete
```

**6. Run the pipeline.** Keep total parallel jobs ≤ 200
(e.g. 20 recordings × 10 jobs).
```bash
bash "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/run_aerotaxis_population_pipeline.sh" --folders 20 --jobs 10 --finalize --pulse_state 21pct_O2
```
`--finalize` submits a **dependent** SLURM job that runs step 7 automatically
once every recording has finished (so you can launch and walk away); drop it if
you'd rather run step 7 by hand. *Local test run (one recording, no cluster):
from inside a `*_new/` folder run `bash RUNME_cluster.sh -c`.*

**7. Finalize the dataset** — combine every crop's table and run the standard
analysis in one step (skip if you used `--finalize` above):
```bash
bash "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/finalize_aerotaxis_dataset.sh" . --pulse_state 21pct_O2
```
This writes `aerotaxis_results.parquet` (the combined tidy table) in the dataset
folder and an `analysis/` folder with the summaries, figures, QC table and
statistics described in [§6](#6-downstream-analysis). To only build the table
(no analysis), run `create_results_dict_server.py . --format parquet` instead.

---

## 5. Outputs & the tidy table

**Per crop:** `output/temporal_features.csv` — one row per frame.
**Whole dataset:** `aerotaxis_results.{parquet,csv,pkl}` — all crops concatenated.

| Column | Meaning |
|---|---|
| `Condition` | grouping key — *added by create_results_dict*. With the `*_new`-per-recording layout this pipeline creates, it resolves to the parsed `Genotype` (so `groupby("Condition")` gives N2 vs rde vs nprrde). If you use a genuine condition folder, its name (minus any trailing `_new`) is kept. |
| `Genotype` | parsed from the recording name via `--genotype-regex` (default `<date>_<time>_<genotype>_<plate>`) — *added by create_results_dict*; falls back to the full recording name if it doesn't match |
| `Plate` | plate/replicate token from the recording name (e.g. `A`/`B`) — *added by create_results_dict*; blank if the name doesn't match |
| `Recording` | recording folder (unique per recording, `_new` stripped) — *added by create_results_dict* |
| `Crop_ID` | per-**track** id — one continuous trajectory fragment, **not** a guaranteed unique worm (see the crop-vs-animal note in [§6](#6-downstream-analysis)) |
| `Frame` | **absolute** recording frame (shared clock across crops) |
| `Time_Seconds` | **absolute** recording time (s) |
| `O2_State` | gas state at that time (`7pct_O2`, `21pct_O2`, `pre_protocol`, `post_protocol`) |
| `Cycle_Index` | 0-based pulse/return repeat number; `-1` for baseline/pre/post. Enables habituation analysis across successive pulses. |
| `Time_In_Phase_s` | seconds since the current gas phase began (0 at each phase onset) |
| `Forward_Velocity` | signed speed (mm/s); negative during reversals |
| `Reversal_Active` | 1 while reversing, else 0 |
| `Turn_Active` | 1 during a turn/coil, else 0 |
| `Reversal_Onset` | 1 on the frame a reversal begins (for reaction-latency analysis) |
| `Bend_Frequency` | body-bend frequency (Hz), median \|Hilbert inst. freq\| across segments |
| `Bend_Amplitude` | body-bend amplitude (curvature units), from Hilbert envelope |
| `Occluded` | 1 = animal lost/occluded on that frame (from the SWC crop ledger `<crop>_metadata.json`). Filter `Occluded == 0` before computing behaviour rates — occluded frames carry blank-crop-derived values. 0 everywhere for data cropped by older SWC versions. |
| `X_mm`, `Y_mm` | absolute arena position (mm), for analysis-time displacement QC (see [§6](#6-downstream-analysis)). Crop centroid in the track.txt fallback. |
| `fps` | the **true per-recording frame rate** (read from SWC `parameters.yaml`), embedded so downstream analysis converts frames↔seconds with the real rate instead of assuming 10 fps. Constant per crop; absent (→ analysis falls back to `--fps`) for tables from older pipeline versions. |

The core behaviour columns are the originally-specified schema; the rest are
enrichments computed from artifacts already in the pipeline (reversal onsets, the
Hilbert body-bend transform, the SWC per-frame occlusion mask, the gas-cycle
index, and the arena position for QC).

---

## 6. Downstream analysis

Everything is plain Pandas/Seaborn and lives in
`toolscripts/utils/aerotaxis_analysis.py` (import in a notebook, run as a CLI, or
feed the tidy CSVs to R).

**Aliveness QC — keep every real worm (slow OR fast), drop only inert junk (on by default).**
`load_results()` / the CLI apply a deliberately **lenient** gate before any
summary: a crop is kept if it was tracked for `≥ --min_track_seconds` (default
5 s) **and shows ANY sign of life** — it *moved* (integrated path `≥ --min_path_mm`
OR net displacement `≥ --min_displacement_mm`), *bent its body* (mean Hilbert
amplitude `≥ --min_bend_amplitude`), or *behaved* (`≥ --min_events` reversal/turn
onsets). Only crops flat on **all** of these — the definitive dead / bubble /
debris signature — are removed. This deliberately keeps a slow dwelling worm
(barely translocates but keeps bending) just like a fast roamer, so you capture
both extremes of real biology. It is **non-destructive** (filters the loaded
table, deletes nothing), **duration-aware**, and uses body-bend and behavioural
signals a bubble can't fake — unlike the irreversible, movement-only step-5
bubble filter, which is now only a throughput tool. Every run logs what was cut
(`[aliveness QC] kept N/M crops ...`) and writes a per-crop `crop_qc.csv` with
all the signals (path, net displacement, positional spread, bend amplitude/freq,
event count, `alive`) so you can eyeball the cropper's output and retune. Disable
with `--keep_all`; from a notebook call `load_results(path, require_alive=False)`
or pass any `min_*` threshold.

**CLI (quick standard readouts):**
```bash
python "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/toolscripts/utils/aerotaxis_analysis.py" \
    aerotaxis_results.parquet --outdir analysis --pulse_state 21pct_O2
```
(`finalize_aerotaxis_dataset.sh` in step 7 runs exactly this for you.) Writes to `analysis/`:
- `crop_qc.csv` — per-crop QC signals + the `alive` flag (inspect the cropper's output here)
- `per_state_summary.csv` + `.png` — speed, reversal/turn fraction, bend Hz, reversal onsets/min per `O2_State` × `Condition`. **Crop-weighted** (each crop/fragment counts once, so a long recording no longer dominates the mean); carries `<metric>_sem`, `n_crops`, `n_recordings`. Add `--frame_pooled` for the old frame-weighted means.
- `transition_triggered_<feature>.csv` + `.png` — feature aligned to each gas shift (mean ± 95 % CI)
- `per_cycle_summary.csv` — mean feature per successive cycle (**habituation** across pulses, via `Cycle_Index`)
- `reversal_reaction.csv` — latency from each pulse onset to the first reversal
- `condition_stats.csv` — Condition comparison per gas state (nonparametric test at the **Recording** level, so plates/crops aren't pseudo-replicated). Includes `p_adj` (**Benjamini–Hochberg FDR** across the whole metric×state family) + a `reject_fdr_0.05` flag, and machine-readable `n_units`/`n_per_condition`.

> **Frame rate is automatic.** The analysis reads the true fps from the `fps`
> column the extractor embeds, so you never pass `--fps` for current data — the
> CLI prints `[fps] using N fps (from data)`. `--fps` is only a fallback for
> legacy tables that predate the column, and it warns whenever it is used. This
> closes a latent bug where every rate/duration/latency was silently computed at
> 10 fps regardless of the real recording rate.

> **A crop is a track fragment, not a unique animal.** SWC tracks by
> nearest-centroid proximity with **no re-identification**: short occlusions are
> bridged within a track (the `Occluded` frames), but once a worm is lost long
> enough for its track to end — or blobs merge, or it leaves/re-enters the ~5 px
> gate — the re-detection gets a **new** `_track_N` id. So one worm can become
> several crops and `n_crops` over-counts animals. Crop-weighting (the default
> `per_state_summary`) removes frame-level pseudoreplication but is per-fragment,
> not per-animal — so **base statistical claims on the Recording-level tests**
> (`condition_stats.csv`), which are robust to fragmentation. True per-animal
> counting would require track stitching/re-ID, which SWC does not do.

**Notebook:** `jupyter_notebooks/Aerotaxis_population_grouped.ipynb`
(load → per-state summary → transition-triggered averages → reversal reaction →
per-crop viewer with the gas protocol shaded). See
`toolscripts/jupyter_notebooks/Aerotaxis_Analysis_Instructions.md` for the primitives.

**Open a notebook on the server:**
```bash
conda activate Jupyter_SHARED
cd <notebook folder>
jupyter notebook --no-browser --port=9997
# on your machine:
ssh -CNL localhost:9997:localhost:9997 <user>@login01.lisc.univie.ac.at
```

---

## 7. Monitoring, cleanup & single-crop debug

**Pipeline status:**
```bash
bash "/lisc/data/scratch/neurobiology/zimmer/LeonK/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/quick_status.sh"
```

**Count things (read-only):**
```bash
find . -type f -name "temporal_features.csv" | wc -l   # finished crops
find . -type d -name "*track*" | wc -l                 # track dirs
```

**Cleanup the analysis outputs (dry-run first!):**
```bash
find "$(pwd)" -type f \( -name "temporal_features.csv" -o -name "aerotaxis_temporal_analysis.done" \) -print   # DRY-RUN
find "$(pwd)" -type f \( -name "temporal_features.csv" -o -name "aerotaxis_temporal_analysis.done" \) -delete  # delete
```

**Re-run a single crop (debug), from inside its `*_new/` folder:**
```bash
snakemake --configfile config.yaml --latency-wait 500 \
  --cluster "./submit_wrapper.sh {resources.time} {resources.partition} {threads} {resources.mem_mb} log/log_%x_%A_%a_%j.out {cluster.gres} {rule}" \
  --cluster-config cluster_config.yaml --jobs 1 --keep-going --rerun-incomplete -p \
  <recording>/<recording>_track_0/output/temporal_features.csv
```

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Log warns `track.txt unusable -- local clock ... ABSOLUTE gas alignment NOT guaranteed` | The SWC position log wasn't found for a crop | Ensure `rename_tracks.py` ran and each track dir has `track.txt` (or the SWC `*_track_N.txt`). The extractor globs `*_track_*.txt` as a fallback; if that warning still appears the crop has **no** position file. Without it, gas alignment is wrong. |
| All crops seem shifted onto the wrong gas phase | `t0_offset_s` wrong, or the recording doesn't start at protocol t=0 | Set `t0_offset_s` to the absolute recording time (s) when the gas protocol begins. Verify: `head track.txt` → `time_imputed_seconds` is the absolute clock. |
| `O2_State` is all `pre_protocol` | `t0_offset_s` larger than the recording times | Lower `t0_offset_s`; check units (seconds). |
| `Forward_Velocity` magnitude looks wrong | SWC `parameters.yaml` missing/incomplete, so calibration fell back to `config.yaml` | The pipeline reads px→mm from `{dataset}/parameters.yaml` (`recording.pixel_size_mm`, or `arena_size_cm*10/frame_height_px`). Check that file exists beside the crops and its `arena_size_cm` is right; re-crop in SWC if not. Only if it's genuinely absent, set the `config.yaml` fallback. (Do **not** use `swc_config.json`'s `um_per_pixel` — that's a separate crop-buffer calibration.) |
| `Bend_Frequency` / `Bend_Amplitude` all NaN | Hilbert files empty (kymogram had too many NaNs) or centerline poor for that crop | Usually a bad crop; it will also look poor elsewhere. Bend columns are optional — the rest of the row is still valid. |
| `> 150 crops` in a recording / thousands of tiny crops | Cropper latched onto bubbles | Run the bubble filter (step 5); inspect and delete bubble crops before running. |
| One recording's workflow ends with `❌ No track.tif files found! / Metadata generation failed!` and `❌ Failed` in its `workflow_*.log` | The SWC cropper produced **zero crops** for that recording — its `<recording>/tracks.json` is `{"active_tracks": {}, "inactive_tracks": {}}` | Fails **in isolation** (other recordings keep running — each is its own SLURM array task). **First decide whether the plate was really empty or the cropper failed:** open `<recording>/report/tracking_report.mp4` — if worms are clearly visible but *not* colour-tracked, it's a cropper failure, not an empty plate. A reliable tell is a contaminated background: `python -c "import tifffile,numpy as np; a=tifffile.imread('<rec>/avg_background.tif').astype(float)[100:-100,100:-100]; print(a.std())"` — good recordings read ~4–8; a value of ~40+ means worms got averaged **into** the background, so background-subtraction cancels them and segmentation finds nothing. **Fix:** re-crop that recording in SWC with a worm-robust background (temporal **median**, or more/decorrelated background frames) and/or a lower `thresh_min`; verify the re-cropped background std drops back to single digits. If the plate genuinely had no motile worms, just drop it. |
| `No subfolders with RUNME_cluster.sh found!` | `run_...` script executed from the wrong directory, or step 3 not run | `cd` to the working dir that contains the `*_new/` folders; run step 3 first. |
| Snakemake: `Directory cannot be locked ...` | A previous run died | From the `*_new/` folder: `snakemake --unlock --configfile config.yaml` (the runner does this automatically). |
| `create_results_dict`: `No temporal_features.csv found` | Analysis rule hasn't produced outputs yet, or wrong folder | Check `quick_status.sh`; run from the dataset root. |
| `Metadata generation failed` / `tiffinfo not found` | `libtiff-tools` missing on the node | Ensure the `autoscope_behaviour_shared` env is active (provides `tiffinfo`). |
| Jobs stuck in queue | Cluster busy / too many jobs | Reduce `--folders`/`--jobs`; keep total ≤ 200; `squeue -u $USER`. |
| A rule fails only for some crops | Bad/short tracks (few frames, mostly NaN centerline) | Expected for junk crops; `--keep-going` continues. Filter them in downstream QC. |
| **`annotate_reversals` fails on most or all crops**, with `KeyError: "None of [Index([9.0 ... 38.0])] are in the [columns]"` | The curvature table is narrower than `final_segment` — nearly always because `min_worm_length_mm` is set above your worms, so `create_centerline` blanked almost every frame and the dynamic column crop collapsed the table | **Do not just rerun.** Check the `[swc] ... min_worm_length_px` line in the log against your worms' real length, then run [step 4a](#4-step-by-step-run-protocol) (`calibrate_min_worm_length.py`) and set `min_worm_length_mm` from the measurement. A handful of such failures is normal junk attrition; a *majority* is a threshold bug. Since the guard was added, `create_centerline` output that collapses now raises a message naming this cause directly. |
| `Reversal_Active` ≈ 0 and `Bend_*` almost entirely NaN, yet crops "succeeded" | Same root cause as above, caught one stage later: the crop had only a handful of valid skeleton frames, enough to pass but not to measure behaviour | Check what fraction of frames actually had a skeleton. Recompute after fixing `min_worm_length_mm`; a healthy crop has a skeleton on the large majority of frames, not <1 %. |
| `Turn_Active` implausibly high (e.g. ~50 % of frames) | `min/max_worm_area` came from SWC's *detection* window but is applied to *SAM2* masks, and/or the roundness thresholds were tuned at a different worm size | Inspect `turn_annotation_by_roundness.csv`, which stores `mask_area` and `roundness_mask_convex_hull` per frame. If `mask_area` sits mostly outside `[min_worm_area, max_worm_area]`, the area window is wrong for SAM2 masks; if areas are inside the window but roundness hovers near `min_round_threshold` during plain forward crawling, re-tune `min_round_threshold`/`max_round_threshold` against a few hand-checked turns. |
| A recording's `workflow_*.log` says `✅ Pipeline complete!` but crops are missing | Pre-fix runs printed that banner unconditionally, ignoring Snakemake's exit code | Fixed: `RUNME_cluster.sh` now reports `❌ Pipeline FAILED (snakemake exit code N)` and propagates it. For an **old** log, ignore the banner and check `grep -c '^Error in rule' workflow_*.log` instead. |

**Where to look:** per-job logs in each `*_new/log/log_*.out`; Snakemake log in
`.snakemake/log/`; `grep -i "error\|fail" log/log_*.out`.

---

## 9. Configuration reference

Key `config.yaml` parameters for this pipeline (others feed the untouched upstream rules):

| Key | Default | Notes |
|---|---|---|
| `fps` | `10` | **Fallback only.** Read per recording from SWC `{dataset}/parameters.yaml` (`recording.fps`); config value used only if that file is absent. |
| `factor_px_to_mm` | `'0.01221'` | **Fallback only.** Read per recording from SWC `parameters.yaml` (`recording.pixel_size_mm`, else `arena_size_cm*10/frame_height_px`). Scales `Forward_Velocity`, and converts `min_worm_length_mm` to pixels. |
| `min_worm_length_mm` | `0.30` | Junk floor on skeleton length, in **mm**; converted to px per recording via `factor_px_to_mm`. Frames with a shorter skeleton are blanked by `create_centerline`. Keep it well below a real worm (~0.8–1.1 mm) — see [§2.1](#21-critical-nuances-for-a-bullet-proof-analysis). Replaces the old pixel key `min_worm_lenght`, which is still honoured (with a warning) if `min_worm_length_mm` is absent. |
| `min_worm_area` / `max_worm_area` | `400` / `1000` | **Fallback only.** Read per recording from SWC `parameters.yaml` (`region_extraction.min/max_region_size`). Gates the turn/coil detector: frames outside the window get `turn = 0` **and `roundness = 0`**, which then feeds the smoothing window — so a mismatched range distorts neighbouring frames too. |
| `relative_spacing` | `2.0` | Centerline points every N % of body length ⇒ ~`100/N` curvature columns. Must satisfy `final_segment ≤ 100/relative_spacing`; the Snakefile refuses to start otherwise. |
| `initial_segment` / `final_segment` | `9` / `39` | Curvature columns fed to the PCA reversal model. The count (`final − initial = 30`) must match the trained model at `pca_model_path`. |
| `aerotaxis.t0_offset_s` | `0.0` | Absolute recording time (s) at protocol start. |
| `aerotaxis.baseline_duration_s` | `240` | Baseline length (s). |
| `aerotaxis.baseline_state` | `7pct_O2` | Baseline gas label. |
| `aerotaxis.cycle` | 30 s 21 % / 60 s 7 % | Ordered repeating phase list. |
| `aerotaxis.n_cycles` | `null` | Cap on cycles (`null` = to end of recording). |

Cluster resources for the analysis rule are in `cluster_config.yaml` under
`aerotaxis_temporal_analysis` (light: 2 CPU / 16 G — no large arrays are loaded).

### Processing note (SAM2, upstream)
GPU NVIDIA L4 · ~0.403 s/frame (~2.48 fps) · mask 146 × 146 (uint8 {0,255}).
```
