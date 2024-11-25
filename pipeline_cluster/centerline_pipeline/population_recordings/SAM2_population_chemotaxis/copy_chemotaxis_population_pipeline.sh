#!/bin/bash

# Enhanced File Copy Script
# This script:
# 1. Creates a nested folder structure for each subfolder
# 2. Copies all files from source folder to each nested subfolder
#
# Usage:
#   1. Set the 'src_file_folder' variable to the path of your source files.
#   2. Run this script from the directory containing the subfolders to process.
#from Experimentfolder run: bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/copy_chemotaxis_population_pipeline.sh

# Define source folder
src_file_folder="/lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/population_sam2"

# Get current directory
current_dir="$PWD"
log_file="${current_dir}/file_copy_log.txt"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$log_file"
}

log_message "Script started."

for subfolder in "${current_dir}"/*/ ; do
    if [ -d "$subfolder" ]; then
        folder_name=$(basename "${subfolder%/}")
        echo "Processing: $folder_name"
        
        # Create folder in current directory
        new_folder="${current_dir}/${folder_name}_new"
        mkdir -p "$new_folder"
        
        # Move original folder
        mv "$subfolder" "$new_folder/"
        
        # Copy specific files
        cp "${src_file_folder}/cluster_config.yaml" "$new_folder/"
        cp "${src_file_folder}/config.yaml" "$new_folder/"
        cp "${src_file_folder}/RUNME_cluster.sh" "$new_folder/"
        cp "${src_file_folder}/Snakefile" "$new_folder/"
        
        log_message "Processed $folder_name"
    fi
done

log_message "Script completed."