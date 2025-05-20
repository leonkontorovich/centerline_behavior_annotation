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
# Each workflow submits up to 4 jobs (as defined in RUNME_cluster.sh)

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

# Create an array of workflow folders for use with job arrays
for i in "${!folders[@]}"; do
    echo "$i ${folders[$i]}" >> workflow_folders.txt
done

# Submit job array with limited concurrency
if $RUN_LOCAL; then
    RUN_OPTION="-c"
else
    RUN_OPTION=""
fi

# Create workflow runner script
cat > workflow_runner.sh << 'EOF'
#!/usr/bin/env bash
RUN_OPTION="$1"
FOLDER_FILE="$2"
ARRAY_ID=$SLURM_ARRAY_TASK_ID

# Get the folder for this array task
FOLDER=$(awk -v id="$ARRAY_ID" '$1 == id {print $2}' "$FOLDER_FILE")
FOLDER_NAME=$(basename "$FOLDER")

echo "→ Processing workflow in: $FOLDER_NAME at $(date)"
cd "$FOLDER" || { echo "Failed to change directory to $FOLDER"; exit 1; }

# Run the workflow script with the provided option
bash RUNME_cluster.sh $RUN_OPTION
EXIT_CODE=$?

echo "✅ Completed workflow in: $FOLDER_NAME with exit code $EXIT_CODE at $(date)"
exit $EXIT_CODE
EOF

chmod +x workflow_runner.sh

# Submit the job array with limited concurrent jobs
job_array_id=$(sbatch --parsable \
    --job-name="snake_workflows" \
    --output="workflow_%A_%a.log" \
    --time=5-00:00:00 \
    --cpus-per-task=1 \
    --mem=4G \
    --array="0-$((NUM_FOLDERS-1))%${MAX_CONCURRENT_WORKFLOWS}" \
    ./workflow_runner.sh "$RUN_OPTION" workflow_folders.txt)

echo "=========================================="
echo "🚀 Submitted job array ${job_array_id} to process all workflows"
echo "👥 Maximum of ${MAX_CONCURRENT_WORKFLOWS} workflows will run concurrently"
echo "⏳ Waiting for all workflows to complete..."
echo "=========================================="

# Wait for the job array to complete
srun --dependency=afterok:${job_array_id} --cpus-per-task=1 --mem=100M --time=0:01:00 \
    /bin/bash -c "echo '✅ All workflows completed successfully at $(date)'"

echo "=========================================="
echo "🏁 Controller script finished at $(date)"
echo "=========================================="