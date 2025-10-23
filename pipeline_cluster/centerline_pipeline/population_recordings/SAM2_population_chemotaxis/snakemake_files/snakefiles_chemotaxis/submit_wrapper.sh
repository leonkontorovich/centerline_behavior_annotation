#!/usr/bin/env bash
# Wrapper to conditionally add --gres flag for SLURM submission
# SLURM rejects --gres with empty value or "None"

TIME="$1"
PART="$2"
CPU="$3"
MEM="$4"
OUT="$5"
GRES="$6"
JOB="$7"
shift 7

# Build sbatch command
CMD="sbatch -t $TIME -p $PART --cpus-per-task $CPU --mem ${MEM}M --output $OUT --job-name=$JOB --nice=0"

# Only add --gres if it has a value AND is not the string "None"
if [ -n "$GRES" ] && [ "$GRES" != "None" ]; then
    CMD="$CMD --gres $GRES"
fi

# Execute
exec $CMD "$@"
