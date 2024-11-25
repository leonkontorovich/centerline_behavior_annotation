#!/bin/bash

# Enhanced File Copy Script
# This script:
# 1. Creates a nested folder structure for each subfolder
# 2. Copies all files from source folder to each nested subfolder
#
# Usage:
#   1. Set the 'src_file_folder' variable to the path of your source files.
#   2. Run this script from the directory containing the subfolders to process.

# Define source folder for files to be copied
src_file_folder="/lisc/scratch/neurobiology/zimmer/schaar/Behavior/High_Res_Population/population_centerline/population_sam2"

# Get current directory
current_dir="$PWD"

# Define log file
log_file="${current_dir}/file_copy_log.txt"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$log_file"
}

# Initialize log
log_message "File copy script started."
log_message "Phase 1: Creating nested folder structure"

# First phase: Create nested structure
for subfolder in "${current_dir}"/*/ ; do
    if [ -d "$subfolder" ]; then
        # Remove trailing slash from subfolder path
        subfolder=${subfolder%/}
        # Get just the folder name
        folder_name=$(basename "$subfolder")
        
        # Create temporary directory
        temp_dir="${current_dir}/temp_${folder_name}"
        
        log_message "Processing $folder_name"
        
        # Move contents to temporary directory
        mv "$subfolder"/* "$temp_dir" 2>/dev/null || mkdir "$temp_dir"
        
        # Create nested directory structure
        mkdir -p "${subfolder}/${folder_name}"
        
        # Move contents from temp to nested directory
        mv "$temp_dir"/* "${subfolder}/${folder_name}/" 2>/dev/null
        
        # Clean up temp directory
        rm -r "$temp_dir"
        
        log_message "Created nested structure for $folder_name"
    fi
done

log_message "Phase 1 completed. Starting Phase 2: Copying files"

# Second phase: Copy files to nested folders
for subfolder in "${current_dir}"/*/ ; do
    if [ -d "$subfolder" ]; then
        folder_name=$(basename "${subfolder%/}")
        nested_path="${subfolder}${folder_name}"
        
        if [ -d "$nested_path" ]; then
            log_message "Copying files to $nested_path (overriding any existing files)"
            cp -R "${src_file_folder}/." "$nested_path/"
            log_message "Files copied to $nested_path"
        else
            log_message "Warning: Nested path $nested_path not found. Skipping."
        fi
    fi
done

log_message "File copy script completed."