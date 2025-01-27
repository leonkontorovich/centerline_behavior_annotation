
# Protocols for running  chemotaxis assay analysis on population data 

### After login:

1. You have to direct to this folder (inside the experiment folder):

   ```bash
   cd "path/to/folder/of/cropped/recordings"
   ```

2. Load the conda module: (only when never used before)

   ```bash
   module load conda
   ```

3. Activate conda on LISC login:

   ```bash
   conda config --append envs_dirs /lisc/scratch/neurobiology/zimmer/.conda/envs (only when never used before)
   ```

   This tells conda to look for shared environments located in the specified folder.

4. List the available environments:

   ```bash
   conda env list
   ```

5. Activate the desired shared centerline environment:

   ```bash
   conda activate autoscope_behaviour_shared
   ```

6. Rename the TIFF files in the experiment folder:

   ```bash
   python /lisc/scratch/neurobiology/zimmer/schaar/code/tool_scripts/rename_tracks.py /lisc/scratch/neurobiology/zimmer/Bin/path_to_the_experimentfolder
   ```

   This script browses the experiment folder and renames the TIFF files to fit the pipeline's needs.

7. Create folder structures and copy pipeline files:

   ```bash
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/create_folders_and_copy_chemotaxis_population_pipeline.sh
   ```

8. Start a new `tmux` session for running the analysis:

   ```bash
   tmux new -s analysis
   ```

   This allows the analysis to continue running even if you get disconnected.

9. Run the analysis on the entire dataset:

   ```bash
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/run_chemotaxis_population_pipeline.sh
   ```

---

### From the Experiment folder:

- **To generate the folder structure and copy files:**

   ```bash
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/create_folders_and_copy_chemotaxis_population_pipeline.sh
   ```

- **To just copy files into an already existing folder structure:**

   ```bash
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/copy_chemotaxis_population_pipeline.sh
   ```

- **To start the pipeline for the dataset:**

   ```bash
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/run_chemotaxis_population_pipeline.sh
   ```

- **To unlock Snakemake directories:**

   ```bash
   bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/bash_scripts/unlock_snakemake_directories.sh
   ```

- **To delete specific output files in the data folder (where you run the analysis):**

   Example: Deleting the final output files from the rule `chemotaxis_analysis` to force the rule to rerun:

   ```bash
   find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -delete
   ```

   Example: Deleting the entire output folder to rerun everything:

   ```bash
   find "$(pwd)" -type d -name "output" -exec rm -r {} +
   ```

