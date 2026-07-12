#!/bin/bash

# Enhanced File Copy Script
# This script:
# 1. Creates a nested folder structure for each subfolder
# 2. Copies all pipeline files to each nested subfolder
#
# Usage:
#   ./create_folders_and_copy_aerotaxis_population_pipeline.sh
#   Run this script from the directory containing the subfolders to process.

# Define source folder (universal pipeline)
src_folder="/lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_aerotaxis/snakemake_files/snakefiles_aerotaxis"

# Get current directory
current_dir="$PWD"
log_file="${current_dir}/file_copy_log.txt"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$log_file"
}

log_message "Script started - creating nested folders and copying universal pipeline files"

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
        
        # Create folder in current directory
        new_folder="${current_dir}/${folder_name}_new"
        mkdir -p "$new_folder"
        
        # Move original folder
        mv "$subfolder" "$new_folder/"
        
        # Copy pipeline configuration files
        cp "${src_folder}/cluster_config.yaml" "$new_folder/"
        cp "${src_folder}/config.yaml" "$new_folder/"
        cp "${src_folder}/Snakefile" "$new_folder/"
        
        # Copy execution scripts
        cp "${src_folder}/RUNME_cluster.sh" "$new_folder/"
        cp "${src_folder}/submit_wrapper.sh" "$new_folder/"
        cp "${src_folder}/generate_metadata.py" "$new_folder/"
        cp "${src_folder}/extract_temporal_features.py" "$new_folder/"

        # Copy documentation
        cp "${src_folder}/README.md" "$new_folder/"

        # Make scripts executable
        chmod +x "${new_folder}/RUNME_cluster.sh"
        chmod +x "${new_folder}/submit_wrapper.sh"

        ((processed++))
        log_message "[$processed/$folder_count] Processed $folder_name - copied 8 files and set permissions"
    fi
done

log_message "Script completed - processed $processed folders"
echo ""
echo "✅ Done! Created nested folders and copied pipeline files to $processed folders"
echo "📝 Check $log_file for details"
