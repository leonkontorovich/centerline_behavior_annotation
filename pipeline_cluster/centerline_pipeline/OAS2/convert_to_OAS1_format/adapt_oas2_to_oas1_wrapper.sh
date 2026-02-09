#!/bin/bash
#SBATCH --job-name=submit_prepare_oas1
#SBATCH --time=00:10:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --output=submit_prepare_oas1_%j.out
#SBATCH --error=submit_prepare_oas1_%j.err

# -------------------------------------------
# Script: submit_prepare_recordings.sh
# Purpose:
#   Discover recording folders containing "worm"
#   and submit one SLURM job per folder
#
# Usage:
#   sbatch submit_prepare_recordings.sh <root_folder>
#   sbatch /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/OAS2/convert_to_OAS1_format/adapt_oas2_to_oas1_wrapper.sh /lisc/data/scratch/neurobiology/zimmer/ItamarLev/pepita/test2
# -------------------------------------------

set -euo pipefail

# ------------------------
# Argument handling
# ------------------------
if [[ $# -ne 1 ]]; then
    echo "Usage: sbatch $0 <root_folder>"
    exit 1
fi

ROOT_FOLDER="$(realpath "$1")"

if [[ ! -d "$ROOT_FOLDER" ]]; then
    echo "Error: root folder does not exist: $ROOT_FOLDER"
    exit 1
fi

PY_SCRIPT="/lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/OAS2/convert_to_OAS1_format/adapt_oas2_to_oas1.py"

if [[ ! -f "$PY_SCRIPT" ]]; then
    echo "Error: Python script not found at $PY_SCRIPT"
    exit 1
fi

echo "Searching for recording folders under:"
echo "  $ROOT_FOLDER"
echo

# ------------------------
# Find and submit jobs
# ------------------------
FOUND_ANY=false

while IFS= read -r RECORDING_DIR; do
    FOUND_ANY=true
    RECORDING_NAME="$(basename "$RECORDING_DIR")"

    echo "Submitting job for: $RECORDING_NAME"

    sbatch <<EOF
#!/bin/bash
#SBATCH --job-name=prepare_oas1_${RECORDING_NAME}
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=20G
#SBATCH --output=prepare_oas1_${RECORDING_NAME}_%j.out
#SBATCH --error=prepare_oas1_${RECORDING_NAME}_%j.err

set -euo pipefail

echo "Processing recording:"
echo "  $RECORDING_DIR"
echo

python3 "$PY_SCRIPT" "$RECORDING_DIR"
EOF

done < <(find "$ROOT_FOLDER" -maxdepth 1 -type d -iname '*worm*')

if [[ "$FOUND_ANY" = false ]]; then
    echo "No recording folders containing 'worm' were found."
else
    echo
    echo "All jobs submitted successfully."
fi



