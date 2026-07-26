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

current_dir="$PWD"

# Default values
MAX_CONCURRENT_WORKFLOWS=4
MAX_JOBS_PER_WORKFLOW=50
FINALIZE=false
PULSE_STATE=""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --folders|-f)
      MAX_CONCURRENT_WORKFLOWS="$2"
      shift 2
      ;;
    --jobs|-j)
      MAX_JOBS_PER_WORKFLOW="$2"
      shift 2
      ;;
    --finalize)
      FINALIZE=true
      shift
      ;;
    --pulse_state)
      PULSE_STATE="$2"
      shift 2
      ;;
    *)
      echo "Usage: $0 [--folders|-f NUM] [--jobs|-j NUM] [--finalize] [--pulse_state STATE]" >&2
      echo "  --folders, -f NUM   Max concurrent workflows (default: 4)" >&2
      echo "  --jobs, -j NUM      Max jobs per workflow (default: 50)" >&2
      echo "  --finalize          After the array finishes, submit a dependent job that" >&2
      echo "                      combines results + runs the analysis (finalize_aerotaxis_dataset.sh)" >&2
      echo "  --pulse_state STATE gas state for the reversal-reaction analysis (e.g. 21pct_O2)" >&2
      exit 1
      ;;
  esac
done

echo "=========================================="
echo "🔍 Scanning for workflows in: $current_dir"
echo "=========================================="

# Find all subfolders containing RUNME_cluster.sh
mapfile -t folders < <(
    find "$current_dir" -maxdepth 1 -type d \( ! -path "$current_dir" \) \
         -exec test -f "{}/RUNME_cluster.sh" \; -print | sort
)

NUM_FOLDERS=${#folders[@]}

if [ $NUM_FOLDERS -eq 0 ]; then
    echo "❌ Error: No subfolders with RUNME_cluster.sh found!"
    exit 1
fi

echo "📁 Found ${NUM_FOLDERS} workflow folders"
echo "🚀 Max concurrent workflows: ${MAX_CONCURRENT_WORKFLOWS}"
echo "⚡ Max jobs per workflow: ${MAX_JOBS_PER_WORKFLOW}"
echo "🎯 Total max parallel jobs: $((MAX_CONCURRENT_WORKFLOWS * MAX_JOBS_PER_WORKFLOW))"
echo "⏱️  Started at: $(date)"
echo "=========================================="
echo ""

# Create list of workflow folders for job array
> workflow_folders.txt
for i in "${!folders[@]}"; do
    echo "${folders[$i]}" >> workflow_folders.txt
    echo "  [$i] $(basename "${folders[$i]}")"
done

echo ""
echo "=========================================="

# Create the workflow runner script
cat > workflow_runner.sh << RUNNER_EOF
#!/usr/bin/env bash
set -e

ARRAY_ID=\${SLURM_ARRAY_TASK_ID}
FOLDER=\$(sed -n "\$((ARRAY_ID + 1))p" workflow_folders.txt)

if [ -z "\$FOLDER" ] || [ ! -d "\$FOLDER" ]; then
    echo "❌ Error: Invalid folder for array ID \$ARRAY_ID"
    exit 1
fi

FOLDER_NAME=\$(basename "\$FOLDER")
echo "=========================================="
echo "🎬 Starting: \$FOLDER_NAME"
echo "⏰ Time: \$(date)"
echo "=========================================="

cd "\$FOLDER" || exit 1

# Run the workflow with specified max jobs.
# NOTE the '|| EXIT_CODE=\$?' -- this script runs under 'set -e', so a bare call
# would abort the moment RUNME_cluster.sh returns non-zero, skipping the failure
# report below and losing the exit code we want to surface.
EXIT_CODE=0
bash RUNME_cluster.sh --jobs ${MAX_JOBS_PER_WORKFLOW} || EXIT_CODE=\$?

if [ \$EXIT_CODE -eq 0 ]; then
    echo "✅ Completed: \$FOLDER_NAME"
else
    echo "❌ Failed: \$FOLDER_NAME (exit code: \$EXIT_CODE)"
fi

echo "⏰ Finished at: \$(date)"
echo "=========================================="
exit \$EXIT_CODE
RUNNER_EOF

chmod +x workflow_runner.sh

# Submit job array
echo "Submitting job array..."
job_id=$(sbatch --parsable \
    --job-name="snake_workflow" \
    --output="workflow_%A_%a.log" \
    --time=5-00:00:00 \
    --cpus-per-task=1 \
    --mem=4G \
    --array="0-$((NUM_FOLDERS-1))%${MAX_CONCURRENT_WORKFLOWS}" \
    workflow_runner.sh)

# Optional dependent finalize job: combine results + run analysis once every
# recording has finished (afterany so it still runs if some recordings failed,
# since the per-recording runs use --keep-going).
if $FINALIZE; then
    FINALIZE_ARGS=("$current_dir")
    [[ -n "$PULSE_STATE" ]] && FINALIZE_ARGS+=(--pulse_state "$PULSE_STATE")
    finalize_id=$(sbatch --parsable \
        --job-name="aero_finalize" \
        --output="finalize_%j.log" \
        --time=0-02:00:00 \
        --cpus-per-task=2 \
        --mem=16G \
        --dependency="afterany:${job_id}" \
        --wrap "bash '${SCRIPT_DIR}/finalize_aerotaxis_dataset.sh' ${FINALIZE_ARGS[*]}")
    echo "🧾 Submitted dependent finalize job: $finalize_id (runs after array ${job_id})"
fi

echo ""
echo "=========================================="
echo "🚀 Submitted job array: $job_id"
echo "📊 Total workflows: $NUM_FOLDERS"
echo "👥 Concurrent workflows: $MAX_CONCURRENT_WORKFLOWS"
echo "⚡ Jobs per workflow: $MAX_JOBS_PER_WORKFLOW"
echo ""
echo "Monitor with:"
echo "  squeue -j $job_id"
echo "  watch 'squeue -j $job_id'"
echo ""
echo "Check logs:"
echo "  tail -f workflow_${job_id}_*.log"
echo "  ls -ltr workflow_${job_id}_*.log"
echo "=========================================="
