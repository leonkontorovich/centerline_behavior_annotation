#!/bin/bash

# Cluster Script Runner
# This script checks each subfolder in the current directory for the presence of 'RUNME_cluster.sh'
# and executes it in parallel by sending each to the server via sbatch.

# Usage:
#   Run this script from the directory containing the subfolders.
#   Example:
#   bash /lisc/scratch/neurobiology/zimmer/schaar/Behavior/High_Res_Population/population_centerline/run_chemotaxis_population_pipeline.sh

# Get current directory
current_dir="$PWD"

# Define log file
log_file="${current_dir}/cluster_run_log.txt"

# Function to log messages with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$log_file"
}

# Initialize log
log_message "Cluster script runner started."

# Main loop to execute RUNME_cluster.sh in each subfolder in parallel
for subfolder in "${current_dir}"/*/ ; do
    if [ -d "$subfolder" ]; then
        runme_script="${subfolder}RUNME_cluster.sh"
        if [ -f "$runme_script" ]; then
            log_message "Dispatching RUNME_cluster.sh in $subfolder"
            (
                cd "$subfolder" && bash RUNME_cluster.sh
                if [ $? -eq 0 ]; then
                    log_message "Successfully dispatched RUNME_cluster.sh in $subfolder"
                else
                    log_message "Error dispatching RUNME_cluster.sh in $subfolder"
                fi
            ) &
        else
            log_message "RUNME_cluster.sh not found in $subfolder"
        fi
    fi
done

# Wait for all background processes to finish
wait

log_message "Cluster script runner completed."
