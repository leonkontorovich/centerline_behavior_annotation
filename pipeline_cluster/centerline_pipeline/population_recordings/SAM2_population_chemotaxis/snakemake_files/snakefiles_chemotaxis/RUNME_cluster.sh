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
MAX_JOBS=10

# Count directories matching the specific pattern
NUM_TRACKS=$(find "$PWD" -type d -name "*track*" | wc -l | tr -d ' ')
# Compute jobs = min(NUM_TRACKS, MAX_JOBS)
if (( NUM_TRACKS < MAX_JOBS )); then
    JOBS=$NUM_TRACKS
else
    JOBS=$MAX_JOBS
fi

echo "=========================================="
echo "🎬 Found $NUM_TRACKS track directories"
if $RUN_LOCAL; then
  echo "🖥️  Running locally with $JOBS cores"
else
  echo "🚀 Submitting up to $JOBS parallel jobs to cluster"
fi
echo "=========================================="

# STEP 1: Pre-generate all metadata for dynamic resources
echo ""
echo "📊 Step 1: Generating video metadata for resource scaling..."
echo "----------------------------------------"
python3 ./generate_metadata.py
if [ $? -ne 0 ]; then
    echo "❌ Metadata generation failed!"
    exit 1
fi

# STEP 2: Unlock workflow
echo ""
echo "🔓 Step 2: Unlocking workflow..."
echo "----------------------------------------"
snakemake --unlock --configfile config.yaml

# STEP 3: Run the workflow with dynamically scaled resources
echo ""
echo "⚙️  Step 3: Running pipeline with scaled resources..."
echo "----------------------------------------"
if $RUN_LOCAL; then
  snakemake \
    --configfile config.yaml \
    --cores $JOBS \
    --keep-going \
    --rerun-incomplete
else
  # Check wrapper exists
  if [ ! -f "./submit_wrapper.sh" ]; then
    echo "❌ ERROR: submit_wrapper.sh not found!"
    exit 1
  fi
  
  chmod +x ./submit_wrapper.sh
  
  snakemake \
    --configfile config.yaml \
    --latency-wait 500 \
    --cluster "./submit_wrapper.sh {resources.time} {resources.partition} {threads} {resources.mem_mb} log/log_%x_%A_%a_%j.out {cluster.gres} {rule}" \
    --cluster-config cluster_config.yaml \
    --jobs $JOBS \
    --keep-going \
    --rerun-incomplete
fi

echo ""
echo "=========================================="
echo "✅ Pipeline complete!"
echo "=========================================="
