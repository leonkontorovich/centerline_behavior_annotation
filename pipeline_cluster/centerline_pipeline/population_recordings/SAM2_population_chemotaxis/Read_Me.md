# Protocols for running chemotaxis assay analysis on population data 

## Initial Setup (for first time users of conda)

<span style="color: red;"><strong>Before you run this validate your worm/noise ration - sometimes the cropper with certin settings crops bubbles and the jitter will create thousand of crops which overflood the server with wastefull jobs - when a recording has more than 150 crops evakluate data quality and delete bubbles before running!

## Dataset Folder Structure
```
Datasetfolder/
├── condition1/ (e.g., 2024-07-26_13-01-01_benzaldehyde_control)
├── condition2/ (e.g., 2024-07-26_12-23-11_benzaldehyde_0_07)
└── condition3/ (or more conditions)
```

**Important Notes:**
- Each repeat needs a **unique string identifier** in the folder name
- Downstream code uses this identifier to read the dataset and separate by condition (e.g., `benzaldehyde_0_07` or `control`)
- Multiple conditions per dataset are supported (e.g., concentration series of an odor)
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
   bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/create_folders_and_copy_chemotaxis_population_pipeline.sh
   ```

4.1 Just copy new Files
```bash
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/copy_chemotaxis_population_pipeline.sh
```

5. **Use `annotate_odor_pos` GUI to annotate `top_left` and `odor_pos`**  
   - If no odor is used, only annotate the `top_left` position with the GUI.  
   - A config file will be created in the dataset folder that saves the positions, and Snakemake will access these positions automatically for the corresponding experiments.
  
6. **Run the cluster based Bublefilter with default settings if not done so locally already, local bubblefilter has a better bubble/worm ratio andn early removes all bubbles **

  # Dry-run first:
```bash
python /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/toolscripts/bubble_filter/NTF_compact.py --src . --threshold 15.0
```

# Then delete:
```bash
python /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/toolscripts/bubble_filter/NTF_compact.py --src . --threshold 15.0 --delete
```


7. Run the analysis - Define parallelism but don't go above 200 -> e.g 20 folders with 10 paralell jobs = 200 jobs:
   ```bash
   sbatch /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/run_chemotaxis_population_pipeline.sh -- --folders 20 --jobs 10
   ```

## Additional Commands for the Experiment Folder (run everything from experiment folder as current pwd)


Show current status of pipeline:
   ```bash
   bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/quick_status.sh
   ```

### Copy Files Only
To copy files into an existing folder structure:
```bash
bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/copy_chemotaxis_population_pipeline.sh
```

### Essential Shell Count Commands
run all from dataset directory

Count files by exact name:
```bash
# Count files named "chemotaxis_params.csv"
find . -type f -name "chemotaxis_params.csv" | wc -l
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
# Dry-run: Show what would be deleted for chemotaxis_analysis rule outputs
find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -print

# Delete chemotaxis_analysis rule outputs
find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -delete

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
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/chemotaxis_analysis.pdf \
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/chemotaxis_params.csv \
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/chemotaxis_analysis_complete.h5 \
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/chemotaxis_analysis.done \
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/hilbert_regenerated_carrier.csv \
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/hilbert_inst_freq.csv \
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/hilbert_inst_phase.csv \
  2024-07-26_12-23-11_benzaldehyde_0.07/2024-07-26_12-23-11_benzaldehyde_0.07%_track_0/output/hilbert_inst_amplitude.csv
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
