#!/usr/bin/env bash

# Parse command line arguments
RUN_LOCAL=false
MAX_JOBS=50  # Default value

while [[ $# -gt 0 ]]; do
  case $1 in
    -c)
      RUN_LOCAL=true
      shift
      ;;
    --jobs|-j)
      MAX_JOBS="$2"
      shift 2
      ;;
    *)
      echo "Usage: $0 [-c] [--jobs|-j NUM]" >&2
      echo "  -c              Run locally instead of on cluster" >&2
      echo "  --jobs, -j NUM  Maximum parallel jobs (default: 50)" >&2
      exit 1
      ;;
  esac
done

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
  SNAKE_RC=$?
else
  # Check wrapper exists
  if [ ! -f "./submit_wrapper.sh" ]; then
    echo "❌ ERROR: submit_wrapper.sh not found!"
    exit 1
  fi
  
  chmod +x ./submit_wrapper.sh

  # SLURM will not create the --output directory; make it up front or every
  # job's stdout/stderr redirect fails and logs are lost.
  mkdir -p log

  snakemake \
    --configfile config.yaml \
    --latency-wait 500 \
    --cluster "./submit_wrapper.sh {resources.time} {resources.partition} {threads} {resources.mem_mb} log/log_%x_%A_%a_%j.out '{cluster.gres}' '{cluster.constraint}' {rule}" \
    --cluster-config cluster_config.yaml \
    --jobs $JOBS \
    --keep-going \
    --rerun-incomplete
  SNAKE_RC=$?
fi

# Report Snakemake's ACTUAL result and propagate it.
#
# This block used to unconditionally print "✅ Pipeline complete!" and exit 0.
# With --keep-going, Snakemake finishes the jobs it can, then exits non-zero
# saying "Exiting because a job execution failed" -- so a run where 4190 of 4576
# crops failed still reported success, in every per-recording log and in the
# controller's summary. A green tick that cannot go red is worse than no tick:
# it is what let a broken run look finished.
echo ""
echo "=========================================="
if [ "${SNAKE_RC:-1}" -eq 0 ]; then
  echo "✅ Pipeline complete — all rules succeeded."
else
  echo "❌ Pipeline FAILED (snakemake exit code ${SNAKE_RC:-1})."
  echo ""
  echo "   With --keep-going, independent jobs still ran, so partial output"
  echo "   exists on disk. DO NOT treat this dataset as finished."
  echo ""
  echo "   Which rule failed, and how often:"
  echo "     grep '^Error in rule' <this log> | sort | uniq -c | sort -rn"
  echo "   Then read the cluster log named in the traceback for the real cause."
fi
echo "=========================================="
exit "${SNAKE_RC:-1}"
