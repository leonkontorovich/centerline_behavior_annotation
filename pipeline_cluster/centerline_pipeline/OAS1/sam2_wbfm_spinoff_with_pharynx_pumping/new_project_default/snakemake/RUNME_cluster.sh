#!/bin/bash

# -------------------------------
# HELP
# -------------------------------
usage() {
    echo "Usage: $0 [-s rule] [-n] [-c] [-R restart_rule] [-h]"
    echo "  -s: target rule to run (default: run_autoscope_behavior)"
    echo "  -R: restart rule (default: none)"
    echo "  -n: dry run (default: false)"
    echo "  -c: run locally (default: false → run on cluster)"
    echo "  -h: display help"
    exit 1
}

# -------------------------------
# DEFAULTS
# -------------------------------
RULE="run_autoscope_behavior"
RESTART_RULE=""
DRYRUN=""
USE_CLUSTER="True"

# -------------------------------
# FLAG PARSING
# -------------------------------
while getopts :s:R:nch flag; do
    case "${flag}" in
        s) RULE="${OPTARG}";;
        R) RESTART_RULE="${OPTARG}";;
        n) DRYRUN="True";;
        c) USE_CLUSTER="";;
        h) usage;;
        *) echo "Unknown flag"; usage;;
    esac
done

# -------------------------------
# CREATE LOGS DIRECTORY
# -------------------------------
mkdir -p logs

# -------------------------------
# SNAKEMAKE OPTIONS
# -------------------------------
SNAKEMAKE_OPT="-s Snakefile.smk --latency-wait 60 --cores 56 --retries 2"

if [[ -n "$RESTART_RULE" ]]; then
    SNAKEMAKE_OPT="$SNAKEMAKE_OPT -R $RESTART_RULE"
fi

# -------------------------------
# SBATCH OPTIONS (Snakemake-expanded)
# -------------------------------
# Package options
SBATCH_OPT="sbatch -t {cluster.time} --cpus-per-task {cluster.cpus_per_task} --mem {cluster.mem} --output {cluster.output} --gres {cluster.gres} --job-name {rule} --constraint '{cluster.constraint}'"
SNAKEMAKE_OPT="-s Snakefile.smk --latency-wait 60 --cores 56 --retries 3"

NUM_JOBS_TO_SUBMIT=8

# -------------------------------
# CREATE TEMPORARY CLUSTER-STATUS SCRIPT
# -------------------------------
CLUSTER_STATUS_SCRIPT=$(mktemp /tmp/slurm_status.XXXXXX.py)

cat << 'EOF' > "$CLUSTER_STATUS_SCRIPT"
#!/usr/bin/env python3
import subprocess
import sys

jobid = sys.argv[1]

try:
    cmd = f"sacct -j {jobid} --format State --noheader | head -1 | awk '{{print $1}}'"
    output = subprocess.check_output(cmd, shell=True).decode().strip()
except Exception:
    output = "UNKNOWN"

running = ["PENDING", "CONFIGURING", "RUNNING", "COMPLETING", "SUSPENDED", "UNKNOWN"]

if "COMPLETED" in output:
    print("success")
elif any(r in output for r in running):
    print("running")
else:
    print("failed")
EOF

chmod +x "$CLUSTER_STATUS_SCRIPT"

# -------------------------------
# RUN SNAKEMAKE
# -------------------------------
if [[ "$DRYRUN" ]]; then
    echo "DRY-RUN: snakemake $RULE"
    snakemake "$RULE" --debug-dag -n $SNAKEMAKE_OPT

elif [[ -z "$USE_CLUSTER" ]]; then
    echo "Running locally: snakemake $RULE"
    snakemake -s Snakefile.smk --unlock
    snakemake "$RULE" $SNAKEMAKE_OPT

else
    echo "Running on SLURM cluster: snakemake $RULE"
    snakemake -s Snakefile.smk --unlock
    snakemake "$RULE" \
        $SNAKEMAKE_OPT \
        --cluster "$SBATCH_OPT --parsable" \
        --cluster-config cluster_config.yaml \
        --jobs $NUM_JOBS_TO_SUBMIT \
        --cluster-status "$CLUSTER_STATUS_SCRIPT" \
        --printshellcmds
fi