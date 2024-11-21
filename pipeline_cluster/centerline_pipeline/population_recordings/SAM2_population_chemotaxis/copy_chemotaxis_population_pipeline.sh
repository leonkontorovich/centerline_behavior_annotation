#!/bin/bash

# File Copy Script
# This script copies all files from a specified source folder to each subfolder in the current directory,
# overriding any existing files in those subfolders.

# Usage:
#   1. Set the 'src_file_folder' variable to the path of your source files.
#   2. Run this script from the directory containing the subfolders to process.
# 
# Note: Ensure you have the necessary permissions to read from the source folder 
# and write to the destination folders.
#from within dataset directory: bash /lisc/scratch/neurobiology/zimmer/schaar/Behavior/High_Res_Population/population_centerline/copy_chemotaxis_population_pipeline.sh 

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

# Main loop to copy files to each subfolder
for subfolder in "${current_dir}"/*/ ; do
    if [ -d "$subfolder" ]; then
        log_message "Copying files to $subfolder (overriding any existing files)"
        cp -R "${src_file_folder}/." "$subfolder/"
        log_message "Files copied to $subfolder"
    else
        log_message "$subfolder is not a directory. Skipping."
    fi
done

log_message "File copy script completed."
