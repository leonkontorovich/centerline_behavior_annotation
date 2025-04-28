#!/usr/bin/env bash

# Check if -c flag is provided
RUN_LOCAL=false
while getopts "c" opt; do
  case ${opt} in
    c ) RUN_LOCAL=true ;;
    * ) echo "Usage: $0 [-c]" >&2
        echo "  -c  Run locally instead of on cluster" >&2
        exit 1 ;;
  esac
done

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
if $RUN_LOCAL; then
  echo "🖥️  Running locally with $JOBS cores"
else
  echo "🚀 Submitting up to $JOBS parallel jobs to cluster"
fi
echo "=========================================="

# First unlock the workflow (in case it was locked from a previous failed run)
echo "Unlocking workflow..."
snakemake --unlock --configfile config.yaml

# Run the workflow
echo "Starting workflow execution..."
if $RUN_LOCAL; then
  # Run locally with specified number of cores
  snakemake \
    --configfile config.yaml \
    --cores $JOBS \
    --keep-going \
    --rerun-incomplete
else
  # Run on cluster
  OPT="sbatch -t {cluster.time} -p {cluster.partition} --cpus-per-task {cluster.cpus_per_task} \
  --mem {cluster.mem} --output {cluster.output} --gres {cluster.gres} --nice=0"
  
  snakemake \
    --configfile config.yaml \
    --latency-wait 500 \
    --cluster "$OPT" \
    --cluster-config cluster_config.yaml \
    --jobs $JOBS \
    --keep-going \
    --rerun-incomplete
fi