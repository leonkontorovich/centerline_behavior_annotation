#!/usr/bin/env bash

# Cluster Script Runner with Console Output & Parallel Cap and Snakemake Unlock
# This script checks each subfolder in the current directory for the presence
# of 'RUNME_cluster.sh', unlocks any existing Snakemake workflow, and executes
# up to MAX_JOBS of them in parallel, printing progress to the console.

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
MAX_JOBS=4

# Gather all subfolders containing RUNME_cluster.sh
mapfile -t folders < <(
    find "$current_dir" -maxdepth 1 -type d \( ! -path "$current_dir" \) \
         -exec test -f "{}/RUNME_cluster.sh" \; -print
)

NUM_FOLDERS=${#folders[@]}

# Header
echo
echo "=========================================="
echo "🔍 Found ${NUM_FOLDERS} subfolders with RUNME_cluster.sh"
if $RUN_LOCAL; then
  echo "🖥️  Running locally with up to ${MAX_JOBS} parallel jobs"
else
  echo "🚀 Dispatching up to ${MAX_JOBS} parallel jobs to cluster"
fi
echo "=========================================="
echo

running=0

for subfolder in "${folders[@]}"; do
    name=$(basename "$subfolder")
    echo "→ Preparing: $name"

    (
        cd "$subfolder" || exit 1

        # Unlock previous Snakemake run
        echo "🔓 Unlocking Snakemake in $name"
        if [[ -f config.yaml ]]; then
            snakemake --unlock --configfile config.yaml &>> runme.log
        fi

        # Execute the pipeline
        echo "🏃 Running RUNME_cluster.sh in $name"
        if $RUN_LOCAL; then
            # Pass the -c flag to the RUNME_cluster.sh script
            bash RUNME_cluster.sh -c &>> runme.log
        else
            bash RUNME_cluster.sh &>> runme.log
        fi

        exitcode=$?
        if (( exitcode == 0 )); then
            echo "✅ Completed: $name"
        else
            echo "❌ Failed:    $name (exit $exitcode)"
        fi
    ) &

    (( running++ ))
    # throttle parallel jobs
    if (( running >= MAX_JOBS )); then
        wait -n
        (( running-- ))
    fi

done

# Wait for any remaining background jobs
wait

echo
echo "=========================================="
echo "✅ All dispatched jobs have completed"
echo "=========================================="