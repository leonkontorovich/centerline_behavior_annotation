#!/usr/bin/env bash

# Cluster Script Runner with Console Output & Parallel Cap and Snakemake Unlock
# This script checks each subfolder in the current directory for the presence
# of 'RUNME_cluster.sh', unlocks any existing Snakemake workflow, and executes
# up to MAX_JOBS of them in parallel, printing progress to the console.

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
 echo "🚀 Dispatching up to ${MAX_JOBS} parallel jobs"
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
        bash RUNME_cluster.sh &>> runme.log

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
