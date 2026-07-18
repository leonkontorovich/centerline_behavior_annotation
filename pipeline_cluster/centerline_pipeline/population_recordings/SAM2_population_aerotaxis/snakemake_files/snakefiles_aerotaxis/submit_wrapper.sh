#!/usr/bin/env bash
# Wrapper to conditionally add --gres and --constraint flags for SLURM submission
# SLURM rejects --gres and --constraint with empty value or "None"

TIME="$1"
PART="$2"
CPU="$3"
MEM="$4"
OUT="$5"
GRES="$6"
CONSTRAINT="$7"
JOB="$8"
shift 8

# Build sbatch command
CMD="sbatch -t $TIME -p $PART --cpus-per-task $CPU --mem ${MEM}M --output $OUT --job-name=$JOB --nice=0"

# Only add --gres if it has a value AND is not the string "None"
if [ -n "$GRES" ] && [ "$GRES" != "None" ]; then
    CMD="$CMD --gres $GRES"
fi

# Only add --constraint if it has a value AND is not empty/None
if [ -n "$CONSTRAINT" ] && [ "$CONSTRAINT" != "None" ] && [ "$CONSTRAINT" != "" ]; then
    CMD="$CMD --constraint=$CONSTRAINT"
fi

# One concise line per submission (kept for troubleshooting; the verbose per-arg
# dump was removed as it flooded the controller log at ~200 concurrent jobs).
echo "[submit_wrapper] $CMD" >&2

# Execute
exec $CMD "$@"