From Experiment folder run this to generate folderstructure and copy files:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/create_folders_and_copy_chemotaxis_population_pipeline.sh

to just copy files in already existing folder structure run:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/copy_chemotaxis_population_pipeline.sh

to start the pipeline for dataset run:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/population_centerline/run_chemotaxis_population_pipeline.sh

If you want to delete specific output in datafolder use this command within the experiment folder:

e.g deleting those 2 outputfiles to forece rule to rerun:

find "$(pwd)" -type f \( -name "chemotaxis_overview.png" -o -name "chemotaxis_params.csv" \) -delete