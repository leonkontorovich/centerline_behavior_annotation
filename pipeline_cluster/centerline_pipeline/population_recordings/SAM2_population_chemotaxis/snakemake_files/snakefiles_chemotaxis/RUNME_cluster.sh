#!/bin/bash
# Example from: https://hackmd.io/@bluegenes/BJPrrj7WB
OPT="sbatch -t {cluster.time} -p {cluster.partition} --cpus-per-task {cluster.cpus_per_task} --mem {cluster.mem} --output {cluster.output} --gres {cluster.gres} --nice=0"

# Count directories matching the specific pattern
NUM_JOBS_TO_SUBMIT=$(find "$PWD" -type d -name "*track*" | wc -l)

# Improved print statement
echo "=========================================="
echo "🔍 Found $NUM_JOBS_TO_SUBMIT track directories"
echo "🚀 Submitting $NUM_JOBS_TO_SUBMIT parallel jobs"
echo "=========================================="

# First unlock the workflow (in case it was locked from a previous failed run)
echo "Unlocking workflow..."
snakemake --unlock --configfile config.yaml

# Then run the workflow
echo "Starting workflow execution..."
snakemake --configfile config.yaml --latency-wait 500 --cluster "$OPT" --cluster-config cluster_config.yaml --jobs $NUM_JOBS_TO_SUBMIT --keep-going --rerun-incomplete