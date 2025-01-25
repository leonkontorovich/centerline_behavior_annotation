#!/bin/bash

# Script to unlock all Snakemake working directories across multiple folders
# Logs all operations for tracking

# Get current directory
current_dir="$PWD"

# Define log file
log_file="${current_dir}/unlock_log.txt"

# Function to log messages with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$log_file"
}

# Initialize log
log_message "Starting batch Snakemake unlock process"

# Find all directories containing Snakefile or snakefile
find "$current_dir" -type f \( -name "Snakefile" -o -name "snakefile" \) -exec dirname {} \; | while read -r snakedir; do
    log_message "Processing directory: $snakedir"
    
    # Check if config.yaml exists
    if [ ! -f "${snakedir}/config.yaml" ]; then
        log_message "Warning: config.yaml not found in ${snakedir}"
        continue
    fi
    
    # Change to the Snakefile directory
    cd "$snakedir" || continue
    
    # Run snakemake unlock
    log_message "Unlocking Snakemake working directory in: $snakedir"
    if snakemake --unlock --configfile config.yaml; then
        log_message "Successfully unlocked: $snakedir"
    else
        log_message "Error unlocking: $snakedir"
    fi
    
    # Return to original directory
    cd "$current_dir" || exit
done

log_message "Batch unlock process completed"