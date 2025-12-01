#!/bin/bash

# TODO: how does it submit the analysis? Do I need to parse anything new? Especially the config files is what concern me

# Add help function
function usage {
    echo "Usage: $0 [-n] [-c] [-h]"
    echo "  -n: dry run (default: false)"
    echo "  -c: do NOT use cluster (default: false, i.e. run on cluster)"
    echo "  -h: display help (this message)"
    exit 1
}

# Set defaults: not a dry run and on the cluster
DRYRUN=""
USE_CLUSTER="True"

while getopts :nch flag
do
    case "${flag}" in
        n) DRYRUN="True";;
        c) USE_CLUSTER="";;
        h) usage;;
        *) echo "Unknown flag"; usage; exit 1;;
    esac
done

# Package options for SLURM
SBATCH_OPT="sbatch -t {cluster.time} --cpus-per-task {cluster.cpus_per_task} --mem {cluster.mem} --output {cluster.output} --gres {cluster.gres} --job-name {rule} --constraint '{cluster.constraint}'"

# Snakemake options
SNAKEMAKE_OPT="--latency-wait 60 --cores 56 --retries 2"

# Count the number of datasets to submit
NUM_JOBS_TO_SUBMIT=$(find "$PWD/data" -mindepth 1 -maxdepth 1 -type d -name "w*" | wc -l)
echo "Found $NUM_JOBS_TO_SUBMIT datasets to process."
echo "Make sure this matches the number of datasets, otherwise expect errors."

# Create a temporary cluster status script to handle SLURM timeout errors
# This is needed because SLURM doesn't properly deal with TIMEOUT errors in subjobs
# Details: https://snakemake.readthedocs.io/en/v7.7.0/tutorial/additional_features.html#using-cluster-status
CLUSTER_STATUS_SCRIPT=$(mktemp /tmp/slurm_status_script.XXXXXX.py)

cat << 'EOF' > "$CLUSTER_STATUS_SCRIPT"
#!/usr/bin/env python
import subprocess
import sys

jobid = sys.argv[1]

try:
    output = str(subprocess.check_output(
        f"sacct -j {jobid} --format State --noheader | head -1 | awk '{{print $1}}'",
        shell=True
    ).strip())
except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
    output = "UNKNOWN"

# Define the possible running statuses
running_status = ["PENDING", "CONFIGURING", "COMPLETING", "RUNNING", "SUSPENDED", "UNKNOWN"]

# Print statements must be exactly as shown for snakemake to interpret correctly
if "COMPLETED" in output:
    print("success")
elif any(r in output for r in running_status):
    print("running")
else:
    print("failed")
EOF

# Make the script executable
chmod +x "$CLUSTER_STATUS_SCRIPT"

# Create log directory if it doesn't exist
mkdir -p log

# Run snakemake
if [ "$DRYRUN" ]; then
    echo "DRYRUN of snakemake with options: $SNAKEMAKE_OPT"
    snakemake --debug-dag -n $SNAKEMAKE_OPT
elif [ -z "$USE_CLUSTER" ]; then
    echo "Running snakemake locally with options: $SNAKEMAKE_OPT"
    snakemake --unlock  # Unlock the folder, just in case
    snakemake $SNAKEMAKE_OPT
else
    echo "Running snakemake on the cluster with options: $SNAKEMAKE_OPT"
    echo "Submitting $NUM_JOBS_TO_SUBMIT jobs to SLURM"
    snakemake --unlock  # Unlock the folder, just in case
    snakemake $SNAKEMAKE_OPT \
        --cluster "$SBATCH_OPT --parsable" \
        --cluster-config cluster_config.yaml \
        --jobs $NUM_JOBS_TO_SUBMIT \
        --cluster-status "$CLUSTER_STATUS_SCRIPT"
fi

# Clean up the temporary script
rm -f "$CLUSTER_STATUS_SCRIPT"
