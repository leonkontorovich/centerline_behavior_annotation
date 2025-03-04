# Protocols for running chemotaxis assay analysis on population data 

## Initial Setup

1. Load the conda module (first-time setup only):
   ```bash
   module load conda
   ```

2. Configure conda on LISC login (first-time setup only):
   ```bash
   conda config --append envs_dirs /lisc/scratch/neurobiology/zimmer/.conda/envs
   ```
   This tells conda to look for shared environments located in the specified folder.

3. List available environments:
   ```bash
   conda env list
   ```

   ## RUN
1. Navigate to the experiment folder:
   ```bash
   cd "path/to/folder/of/cropped/recordings"
   ```
   
2. Activate the centerline environment:
   ```bash
   conda activate autoscope_behaviour_shared
   ```

3. Rename TIFF files in the experiment folder:
   ```bash
   python /lisc/scratch/neurobiology/zimmer/schaar/code/tool_scripts/rename_tracks.py .
   ```
   This script renames the TIFF files to fit the pipeline's needs.

4. Create folder structures and copy pipeline files:
   ```bash
   # For chemotaxis pipeline files:
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/create_folders_and_copy_chemotaxis_population_pipeline.sh chemotaxis

   # For basic pipeline files:
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/create_folders_and_copy_chemotaxis_population_pipeline.sh basic
   ```

5. Start a new tmux session:
   ```bash
   tmux new -s analysis
   ```
   This allows the analysis to continue running even if you get disconnected.

6. Run the analysis:
   ```bash
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/run_chemotaxis_population_pipeline.sh
   ```

## Additional Commands for the Experiment Folder

### Copy Files Only
To copy files into an existing folder structure:
```bash
# For chemotaxis pipeline files:
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/copy_chemotaxis_population_pipeline.sh chemotaxis

# For basic pipeline files:
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/copy_chemotaxis_population_pipeline.sh basic
```

### Pipeline Management
Start the pipeline:
```bash
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/run_chemotaxis_population_pipeline.sh
```

Unlock Snakemake directories:
```bash
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/unlock_snakemake_directories.sh
```

### Cleanup Commands
Delete specific output files:
```bash
# Delete chemotaxis_analysis rule outputs
find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -delete

# Delete all output folders
find "$(pwd)" -type d -name "output" -exec rm -r {} +
```
