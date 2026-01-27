#!/bin/bash

# -------------------------------------------
# Script: run_prepare_recordings.sh
# Purpose: Wrapper to run prepare_OAS_formatting.py
# Usage:
#   ./run_prepare_recordings.sh <root_folder>
# Example:
#   ./run_prepare_recordings.sh /lisc/data/recordings #TODO: make an example with the final path of this bash script
# Notes:
#   - The Python script will process all subfolders
#     containing "worm" in their names
#     and will convert OAS2 data to OAS1 format.
#     this includes: 1. converting .btf file to ndtiff format,
#                    2. copying the worm_config.yaml file to the recording folder
#                    3. changing the gantry position filename and format to standard "TablePosRecord.txt" format
# -------------------------------------------

# Function to display usage instructions
usage() {
    echo "Usage: $0 <root_folder>"
    echo "Example: $0 /lisc/data/recordings"
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

# Optional: specify Python version explicitly
PYTHON=python3

# Check if Python exists
if ! command -v $PYTHON &> /dev/null; then
    echo "Error: $PYTHON not found. Please install Python 3."
    exit 1
fi

# Check if the Python script exists
PY_SCRIPT="/lisc/data/scratch/neurobiology/zimmer/ItamarLev/Code/bash/test_adapt_OAS_data_to_be_analyzed.py" #TODO: adapt to its new position

if [ ! -f "$PY_SCRIPT" ]; then
    echo "Error: Python script not found at $PY_SCRIPT"
    exit 1
fi

# Run the Python script with verbose output
echo "Running Python script on folder: $ROOT_FOLDER"
$PYTHON "$PY_SCRIPT" "$ROOT_FOLDER"

# Check exit status of Python script
if [ $? -ne 0 ]; then
    echo "Python script failed. Check the output above for errors."
    exit 1
else
    echo "Python script completed successfully!"
fi
