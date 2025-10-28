#!/bin/bash

# Simple File Copy Script
# This script copies all pipeline files to each subfolder
#
# Usage:
#   ./copy_chemotaxis_population_pipeline.sh
#   Run this script from the directory containing the subfolders to process.

# Define source folder (universal pipeline)
src_folder="/lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/snakemake_files/snakefiles_chemotaxis"

# Get current directory
current_dir="$PWD"
log_file="${current_dir}/file_copy_log.txt"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$log_file"
}

log_message "Script started - copying universal pipeline files"

# Count folders to process
folder_count=0
for subfolder in "${current_dir}"/*/ ; do
    if [ -d "$subfolder" ]; then
        ((folder_count++))
    fi
done

log_message "Found $folder_count folders to process"

# Process each subfolder
processed=0
for subfolder in "${current_dir}"/*/ ; do
    if [ -d "$subfolder" ]; then
        folder_name=$(basename "${subfolder%/}")
        echo "Processing: $folder_name"
        
        # Copy pipeline configuration files
        cp "${src_folder}/cluster_config.yaml" "$subfolder"
        cp "${src_folder}/config.yaml" "$subfolder"
        cp "${src_folder}/Snakefile" "$subfolder"
        
        # Copy execution scripts
        cp "${src_folder}/RUNME_cluster.sh" "$subfolder"
        cp "${src_folder}/submit_wrapper.sh" "$subfolder"
        cp "${src_folder}/generate_metadata.py" "$subfolder"
        
        # Copy documentation
        cp "${src_folder}/README.md" "$subfolder"
        
        ((processed++))
        log_message "[$processed/$folder_count] Processed $folder_name - copied 7 files and set permissions"
    fi
done

log_message "Script completed - processed $processed folders"
echo ""
echo "✅ Done! Copied pipeline files to $processed folders"
echo "📝 Check $log_file for details"
