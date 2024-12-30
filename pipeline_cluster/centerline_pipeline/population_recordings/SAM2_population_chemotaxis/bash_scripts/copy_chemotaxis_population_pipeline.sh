#!/bin/bash

# Simple File Copy Script
# This script copies specified files from source folder to each subfolder
#
# Usage:
#   Run this script from the directory containing the subfolders to process.

# Define source folder
src_file_folder="/lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/snakemake_files"

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
        
        # Copy specific files
        cp "${src_file_folder}/cluster_config.yaml" "$subfolder"
        cp "${src_file_folder}/config.yaml" "$subfolder"
        cp "${src_file_folder}/RUNME_cluster.sh" "$subfolder"
        cp "${src_file_folder}/Snakefile" "$subfolder"
        
        log_message "Processed $folder_name"
    fi
done

log_message "Script completed."