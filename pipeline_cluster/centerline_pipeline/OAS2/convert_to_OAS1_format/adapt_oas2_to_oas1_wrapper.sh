#!/bin/bash
#SBATCH --job-name=prepare_oas1
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=20G
#SBATCH --output=prepare_oas1_%j.out
#SBATCH --error=prepare_oas1_%j.err

# -------------------------------------------
# Script: run_prepare_recordings.sh
# Purpose: Wrapper to run adapt_oas2_to_oas1.py via SLURM
# Usage:
#   sbatch run_prepare_recordings.sh <root_folder>
# Example:
#   sbatch run_prepare_recordings.sh /lisc/data/recordings
# Specific example:
#   sbatch /lisc/data/scratch/neurobiology/zimmer/ItamarLev/pepita/code_temp/adapt_oas2_to_oas1_wrapper.sh /lisc/data/scratch/neurobiology/zimmer/ItamarLev/pepita/test2
#
# Notes:
#   - The Python script will process all subfolders
#     containing "worm" in their names
#     and will convert OAS2 data to OAS1 format.
#     this includes:
#       1. converting .btf file to ndtiff format,
#       2. copying the worm_config.yaml file to the recording folder
#       3. changing the gantry position filename and format to standard
#          "TablePosRecord.txt" format
# -------------------------------------------

# Function to display usage instructions
usage() {
    echo "Usage: sbatch $0 <root_folder>"
    echo "Example: sbatch $0 /lisc/data/recordings"
    exit 1
}

# Check for help argument
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
fi

# Check if root folder argument is provided
if [ "$#" -ne 1 ]; then
    usage
fi

ROOT_FOLDER="$1"

# Python script path
PY_SCRIPT="/lisc/data/scratch/neurobiology/zimmer/ItamarLev/pepita/code_temp/adapt_oas2_to_oas1.py"

if [ ! -f "$PY_SCRIPT" ]; then
    echo "Error: Python script not found at $PY_SCRIPT"
    exit 1
fi

echo "Running Python script on folder: $ROOT_FOLDER"
python3 "$PY_SCRIPT" "$ROOT_FOLDER"

# Check exit status
if [ $? -ne 0 ]; then
    echo "Python script failed. Check the output above for errors."
    exit 1
else
    echo "Python script completed successfully!"
fi