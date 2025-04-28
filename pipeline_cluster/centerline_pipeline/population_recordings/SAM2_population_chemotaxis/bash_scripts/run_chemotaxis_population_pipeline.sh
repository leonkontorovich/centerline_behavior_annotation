#!/usr/bin/env bash

#SBATCH --job-name=snake_controller
#SBATCH --output=controller_%j.log
#SBATCH --time=20-00:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --mail-type=END,FAIL

# This script manages the submission of multiple Snakemake workflows
# with controlled overall parallelism

# Parse command line arguments
RUN_LOCAL=false
while getopts "c" opt; do
  case ${opt} in
    c ) RUN_LOCAL=true ;;
    * ) echo "Usage: $0 [-c]" >&2
        echo "  -c  Run locally instead of on cluster" >&2
        exit 1 ;;
  esac
done

current_dir="$PWD"
# Control how many Snakemake workflows can run simultaneously
MAX_CONCURRENT_WORKFLOWS=4
# Each workflow will submit up to 4 jobs in parallel (as defined in RUNME_cluster.sh)
# This means a maximum of ~40 concurrent jobs at any time

# Gather all subfolders containing RUNME_cluster.sh
mapfile -t folders < <(
    find "$current_dir" -maxdepth 1 -type d \( ! -path "$current_dir" \) \
         -exec test -f "{}/RUNME_cluster.sh" \; -print
)

NUM_FOLDERS=${#folders[@]}

echo "=========================================="
echo "🔍 Found ${NUM_FOLDERS} subfolders with RUNME_cluster.sh"
echo "🚀 Will run up to ${MAX_CONCURRENT_WORKFLOWS} workflows simultaneously"
echo "=========================================="

# Array to store job IDs
declare -a job_ids

for subfolder in "${folders[@]}"; do
    name=$(basename "$subfolder")
    echo "→ Preparing: $name at $(date)"
    
    # Build the sbatch command for this workflow
    if $RUN_LOCAL; then
        cmd="cd $subfolder && bash RUNME_cluster.sh -c"
    else
        cmd="cd $subfolder && bash RUNME_cluster.sh"
    fi
    
    # Submit the job and capture its ID
    job_id=$(sbatch --parsable \
        --job-name="snake_${name}" \
        --output="${subfolder}/workflow_%j.log" \
        --time=5-00:00:00 \
        --cpus-per-task=1 \
        --mem=4G \
        --wrap="$cmd")
    
    echo "📋 Submitted job ${job_id} for ${name}"
    job_ids+=("$job_id")
    
    # If we've reached the maximum number of concurrent workflows,
    # wait for one to finish before submitting more
    if [ ${#job_ids[@]} -ge $MAX_CONCURRENT_WORKFLOWS ]; then
        echo "⏳ Reached maximum concurrent workflows, waiting for one to complete..."
        # Wait for any job to complete
        srun --dependency=afterany:$(IFS=:; echo "${job_ids[*]}") --cpus-per-task=1 --mem=100M --time=0:01:00 /bin/true
        
        # Remove completed jobs from our tracking array
        new_job_ids=()
        for jid in "${job_ids[@]}"; do
            if squeue -j "$jid" &>/dev/null; then
                new_job_ids+=("$jid")
            fi
        done
        job_ids=("${new_job_ids[@]}")
        
        echo "✅ Slot available, continuing submission (${#job_ids[@]}/${MAX_CONCURRENT_WORKFLOWS} workflows running)"
    fi
done

# Wait for all remaining jobs to complete
if [ ${#job_ids[@]} -gt 0 ]; then
    echo "⏳ Waiting for all remaining workflows to complete..."
    srun --dependency=afterany:$(IFS=:; echo "${job_ids[*]}") --cpus-per-task=1 --mem=100M --time=0:01:00 /bin/true
fi

echo "=========================================="
echo "✅ All workflow submissions completed at $(date)"
echo "=========================================="