#!/usr/bin/env bash

# Maximum parallel jobs
MAX_JOBS=4

# Count directories matching the specific pattern
NUM_TRACKS=$(find "$PWD" -type d -name "*track*" | wc -l | tr -d ' ')
# Compute jobs = min(NUM_TRACKS, MAX_JOBS)
if (( NUM_TRACKS < MAX_JOBS )); then
    JOBS=$NUM_TRACKS
else
    JOBS=$MAX_JOBS
fi

# Improved print statement
echo "=========================================="
echo "🔍 Found $NUM_TRACKS track directories"
echo "🚀 Submitting up to $JOBS parallel jobs"
echo "=========================================="

OPT="sbatch -t {cluster.time} -p {cluster.partition} --cpus-per-task {cluster.cpus_per_task} \
--mem {cluster.mem} --output {cluster.output} --gres {cluster.gres} --nice=0"

# First unlock the workflow (in case it was locked from a previous failed run)
echo "Unlocking workflow..."
snakemake --unlock --configfile config.yaml

# Then run the workflow with at most $JOBS parallel submissions
echo "Starting workflow execution..."
snakemake \
    --configfile config.yaml \
    --latency-wait 500 \
    --cluster "$OPT" \
    --cluster-config cluster_config.yaml \
    --jobs $JOBS \
    --keep-going \
    --rerun-incomplete
