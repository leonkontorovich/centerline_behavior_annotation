# Protocols for running thiophene chemotaxis assay analysis (public)

after login:

ssh 

1, you have to direct to this folder (inside the experiment folder)

cd /lisc/scratch/neurobiology/zimmer/Bin/Population_chemotaxis/Thiophene_population_assay/241129_proper_analysis_Thiophene_concentration_series_chemotaxis_population

2,
module load conda
activate conda on lisc login

3,
conda config --append envs_dirs /lisc/scratch/neurobiology/zimmer/.conda/envs
telling conda to look for shared environment located in the folder.

4,
conda env list 

(list of available environments)

5,
conda activate autoscope_behaviour_shared

6,
python /lisc/scratch/neurobiology/zimmer/schaar/code/tool_scripts/rename_tracks.py /lisc/scratch/neurobiology/zimmer/Bin/patg to the experimenbtfolder
browses expriment folder and renames tif files to pipline needs

7,
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/create_folders_and_copy_chemotaxis_population_pipeline.sh
creates folder structures and copies pipeline files

8,
tmux new -s analysis
(analysis is the name of the open session this allows running even if i am disconnected)

9,
bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/run_chemotaxis_population_pipeline.sh
this runs the analysis (whole dataset)


From Experiment folder run this to generate folderstructure and copy files:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/create_folders_and_copy_chemotaxis_population_pipeline.sh

to just copy files in already existing folder structure run:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/copy_chemotaxis_population_pipeline.sh

to start the pipeline for dataset run:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/run_chemotaxis_population_pipeline.sh

If you want to delete specific output in datafolder (folder where you run analysis on) use this command within the experiment folder:

e.g deleting those 2 final outputfiles from rule chemotaxis_analysis to forece rule to rerun:

find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -delete

e.g deleting whole output folders to rerun everything

find "$(pwd)" -type d -name "output" -exec rm -r {} +
