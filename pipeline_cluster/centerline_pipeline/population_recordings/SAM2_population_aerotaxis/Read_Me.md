# Protocols for running aerotaxis (temporal gas-shift) assay analysis on population data

This pipeline analyses **temporal** behavioural state changes (speed, turns, reversals)
locked to **global plate-level gas shifts** (e.g. an O2 baseline followed by repeating
pulse/return cycles). There is **no spatial navigation** component: no odor position,
no concentration gradient, no chemotaxis index.

The gas protocol is defined in `config.yaml` under the `aerotaxis:` block and can be
edited freely per assay / oxygen-sensing paradigm (see **Gas protocol** below).

## Initial Setup (for first time users of conda)

<span style="color: red;"><strong>Before you run this validate your worm/noise ration - sometimes the cropper with certin settings crops bubbles and the jitter will create thousand of crops which overflood the server with wastefull jobs - when a recording has more than 150 crops evakluate data quality and delete bubbles before running!

## Dataset Folder Structure
```
Datasetfolder/
├── condition1/ (e.g., 2025-03-10_13-01-01_N2_7pct_baseline)
├── condition2/ (e.g., 2025-03-10_12-23-11_gcy35_7pct_baseline)
└── condition3/ (or more conditions)
```

**Important Notes:**
- Each repeat needs a **unique string identifier** in the folder name
- Downstream code uses this identifier to read the dataset and separate by condition (e.g., `N2` or `gcy35`)
- Multiple conditions per dataset are supported (e.g., a genotype panel)
- **No subfolders** - all scripts expect this flat folder structure

1. Load the conda module (first-time setup only):
   ```bash
   module load conda
   echo 'module load conda' >> ~/.bashrc
   ```

2. Configure conda on LISC login (first-time setup only):
   ```bash
   conda config --append envs_dirs /lisc/data/scratch/neurobiology/zimmer/.conda/envs
   ```
   This tells conda to look for shared environments located in the specified folder.

3. List available environments:
   ```bash
   conda env list
   ```

## Gas protocol (temporal alignment)

The assay timing lives in `config.yaml` and is applied per frame by
`extract_temporal_features.py`. The default matches a global O2 shift assay:

```yaml
aerotaxis:
  t0_offset_s: 0.0             # seconds of recording BEFORE the protocol starts
  baseline_duration_s: 240     # 4-min baseline
  baseline_state: "7pct_O2"
  cycle:                       # one repeating unit; phases applied in order
    - {state: "21pct_O2", duration_s: 30}   # pulse
    - {state: "7pct_O2",  duration_s: 60}    # return
  n_cycles: null               # null = repeat to end of recording; or an int to cap
```

To adapt to a different paradigm, just edit `baseline_*` and the `cycle` phase list -
no code change is needed.

Alignment uses the **absolute recording time** from each track's SWC `track.txt`
(`time_imputed_seconds`), so crops that start at different times in the recording
all lock to the same global gas protocol. `Frame` and `Time_Seconds` in the output
are therefore absolute (recording-wide). `t0_offset_s` sets the recording time at
which the protocol begins; frames before it are labelled `pre_protocol`.
______________________________________________________________________________________________
## Start here if you already did set up your conda on user login!

   ## RUN
1. Navigate to the experiment folder:
   ```bash
   cd "path/to/folder/of/cropped/recordings"
   ```

   Important: for this pipeline run every command from within the dataset working directory (path/to/folder/of/cropped/recordings) !
      e.g type PWD in shell

2. Activate the centerline environment:
   ```bash
   conda activate autoscope_behaviour_shared
   ```

3. Rename TIFF files in the experiment folder:
   ```bash
   python /lisc/data/scratch/neurobiology/zimmer/schaar/code/tool_scripts/rename_tracks.py $PWD
   ```
   This script renames the TIFF files to fit the pipeline's needs.

4. Create folder structures and copy pipeline files (don't run this if folder structure already exists, but use alternative that just copies!):

   ```bash
   bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/create_folders_and_copy_aerotaxis_population_pipeline.sh
   ```

**4.1 Just copy new Files**
```bash
bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/copy_aerotaxis_population_pipeline.sh
```

5. **Confirm the gas protocol in `config.yaml`** (`aerotaxis:` block) matches this experiment.
   There is **no GUI / position-annotation step** in the aerotaxis pipeline - the gas shifts
   are global to the plate, so alignment is purely temporal (see **Gas protocol** above).

6. **Run the cluster based Bublefilter with default settings if not done so locally already, local bubblefilter has a better bubble/worm ratio andn early removes all bubbles **

  # Dry-run first:
```bash
python /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/toolscripts/bubble_filter/NTF_compact.py --src . --threshold 15.0
```

# Then delete:
```bash
python /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/toolscripts/bubble_filter/NTF_compact.py --src . --threshold 15.0 --delete
```


7. Run the analysis - Define parallelism but don't go above 200 -> e.g 20 folders with 10 paralell jobs = 200 jobs:
   ```bash
   bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/run_aerotaxis_population_pipeline.sh -- --folders 20 --jobs 10
   ```

8. When analysis is finished, create the tidy results table for downstream analysis (Pandas / Seaborn / R):
   ```bash
   python /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/toolscripts/utils/create_results_dict_server.py . --format parquet
   ```
   Output: `aerotaxis_results.parquet` (or `--format csv` / `--format pkl`) saved in the current
   dataset folder. It is a flat tidy table with columns
   `[Condition, Recording, Crop_ID, Frame, Time_Seconds, O2_State, Forward_Velocity, Reversal_Active, Turn_Active]`.

## Additional Commands for the Experiment Folder (run everything from experiment folder as current pwd)


Show current status of pipeline:
   ```bash
   bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/quick_status.sh
   ```

### Copy Files Only
To copy files into an existing folder structure:
```bash
bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/bash_scripts/copy_aerotaxis_population_pipeline.sh
```

### Essential Shell Count Commands
run all from dataset directory

Count files by exact name:
```bash
# Count files named "temporal_features.csv"
find . -type f -name "temporal_features.csv" | wc -l
```

Count folders by exact name:
```bash
# Count directories named "output"
find . -type d -name "output" | wc -l
```

Count folders by pattern in name:
```bash
# Count directories with "track" in their name
find . -type d -name "*track*" | wc -l
```

> **Note:**
> All commands above are read-only and won't delete or modify any files or directories.

### Cleanup Commands

Delete specific output files:

```bash
# Dry-run: Show what would be deleted for aerotaxis_temporal_analysis rule outputs
find "$(pwd)" -type f \( -name "temporal_features.csv" -o -name "aerotaxis_temporal_analysis.done" \) -print

# Delete aerotaxis_temporal_analysis rule outputs
find "$(pwd)" -type f \( -name "temporal_features.csv" -o -name "aerotaxis_temporal_analysis.done" \) -delete

# Delete all output folders

# Dryrun
find "$(pwd)" -type d -name "output" -exec echo "Would remove: {}" \;

# Real command - use with care after DRYRUN!!
find "$(pwd)" -type d -name "output" -exec rm -r {} +
```

### Cleanup Commands - Debug run for one specific crop folder

```bash
snakemake --configfile config.yaml \
  --latency-wait 500 \
  --cluster "./submit_wrapper.sh {resources.time} {resources.partition} {threads} {resources.mem_mb} log/log_%x_%A_%a_%j.out {cluster.gres} {rule}" \
  --cluster-config cluster_config.yaml \
  --jobs 1 \
  --keep-going \
  --rerun-incomplete \
  -p \
  2025-03-10_12-23-11_gcy35_7pct_baseline/2025-03-10_12-23-11_gcy35_7pct_baseline_track_0/output/temporal_features.csv \
  2025-03-10_12-23-11_gcy35_7pct_baseline/2025-03-10_12-23-11_gcy35_7pct_baseline_track_0/output/aerotaxis_temporal_analysis.done \
  2025-03-10_12-23-11_gcy35_7pct_baseline/2025-03-10_12-23-11_gcy35_7pct_baseline_track_0/output/hilbert_regenerated_carrier.csv \
  2025-03-10_12-23-11_gcy35_7pct_baseline/2025-03-10_12-23-11_gcy35_7pct_baseline_track_0/output/hilbert_inst_freq.csv \
  2025-03-10_12-23-11_gcy35_7pct_baseline/2025-03-10_12-23-11_gcy35_7pct_baseline_track_0/output/hilbert_inst_phase.csv \
  2025-03-10_12-23-11_gcy35_7pct_baseline/2025-03-10_12-23-11_gcy35_7pct_baseline_track_0/output/hilbert_inst_amplitude.csv
```

### Processing logs for SAM2

GPU: NVIDIA L4
Per-frame processing time: ~0.403 s/frame (≈403 ms, ~2.48 fps)
Mask resolution: 146 × 146 (uint8 {0, 255})

### Opening Jupyter-Notebooks on server for later grouped analysis

```bash
   conda activate Jupyter_SHARED

   cd <to notebook folder>

   jupyter notebook --no-browser --port=9997 -> pick a port e.g 9997 and stick to it

   ssh -CNL localhost:9997:localhost:9997 schaar@login01.lisc.univie.ac.at -> use same port as before when opening the notebook

```
