# Protocols for running chemotaxis assay analysis on population data 

## Initial Setup (for first time users of conda)

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
______________________________________________________________________________________________
## Start here if you already did set up your conda on user login!

   ## RUN
1. Navigate to the experiment folder:
   ```bash
   cd "path/to/folder/of/cropped/recordings"
   ```

   Important: for this pipeline run every command from within the dataset working directory (path/to/folder/of/cropped/recordings) !
      e.g type PWD in shell
   
3. Activate the centerline environment:
   ```bash
   conda activate autoscope_behaviour_shared
   ```

4. Rename TIFF files in the experiment folder:
   ```bash
   python /lisc/scratch/neurobiology/zimmer/schaar/code/tool_scripts/rename_tracks.py $PWD
   ```
   This script renames the TIFF files to fit the pipeline's needs.

5. Create folder structures and copy pipeline files (don't run this if folderstructure already exists, but use alternative that just copys!):
   ```bash
   # For chemotaxis pipeline files:
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/create_folders_and_copy_chemotaxis_population_pipeline.sh chemotaxis

   # For basic pipeline files:
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/create_folders_and_copy_chemotaxis_population_pipeline.sh basic
   ```

6. **Use `annotate_odor_pos` GUI to annotate `top_left` and `odor_pos`**  
   - If no odor is used, only annotate the `top_left` position with the GUI.  
   - A config file will be created in the dataset folder that saves the positions, and Snakemake will access these positions automatically for the corresponding experiments.

7. Start a new tmux session:
   ```bash
   tmux new -s analysis
   ```
   This allows the analysis to continue running even if you get disconnected.

8. Run the analysis:
   ```bash
   sbatch /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/run_chemotaxis_population_pipeline.sh
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
sbatch /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/run_chemotaxis_population_pipeline.sh
```

Unlock Snakemake directories: (starting the pipeline also includes unlock step)
```bash
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/unlock_snakemake_directories.sh
```

### Essential Shell Count Commands
run all from dataset cirectory

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

Cleanup Commands

Delete specific output files:

```bash
# Dry-run: Show what would be deleted for chemotaxis_analysis rule outputs
find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -print

# Delete chemotaxis_analysis rule outputs
find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -delete

# Dry-run: Show what output folders would be deleted
find "$(pwd)" -type d -name "output" -print

# Delete all output folders

#Dryrun
find "$(pwd)" -type d -name "output" -exec echo "Would remove: {}" \;

#Real command - use with care after DRYRUN!!
find "$(pwd)" -type d -name "output" -exec rm -r {} +
```
