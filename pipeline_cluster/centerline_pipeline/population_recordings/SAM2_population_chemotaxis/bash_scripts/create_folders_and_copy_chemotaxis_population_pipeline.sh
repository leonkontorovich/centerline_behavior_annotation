#!/bin/bash

# Enhanced File Copy Script
# This script:
# 1. Creates a nested folder structure for each subfolder
# 2. Copies all files from source folder to each nested subfolder
#
# Usage:
#   ./script.sh [basic|chemotaxis]
#   Run this script from the directory containing the subfolders to process.

# Check if argument is provided
if [ $# -ne 1 ]; then
    echo "Error: Please provide one argument: 'basic' or 'chemotaxis'"
    echo "Usage: $0 [basic|chemotaxis]"
    exit 1
fi

# Validate argument
if [ "$1" != "basic" ] && [ "$1" != "chemotaxis" ]; then
    echo "Error: Invalid argument. Please use 'basic' or 'chemotaxis'"
    echo "Usage: $0 [basic|chemotaxis]"
    exit 1
fi

# Define source folders
src_folder_basic="/lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/snakemake_files/snakefiles_basic"
src_folder_chemotaxis="/lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/snakemake_files/snakefiles_chemotaxis"

# Select source folder based on argument
if [ "$1" == "basic" ]; then
    src_folder="$src_folder_basic"
else
    src_folder="$src_folder_chemotaxis"
fi

# Get current directory
current_dir="$PWD"
log_file="${current_dir}/file_copy_log.txt"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$log_file"
}

log_message "Script started with mode: $1"

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
        cp "${src_folder}/cluster_config.yaml" "$new_folder/"
        cp "${src_folder}/config.yaml" "$new_folder/"
        cp "${src_folder}/RUNME_cluster.sh" "$new_folder/"
        cp "${src_folder}/Snakefile" "$new_folder/"
        
        log_message "Processed $folder_name"
    fi
done

log_message "Script completed."