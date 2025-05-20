#!/bin/bash

###############################################################################
# Script Name: run_update_config.sh
# Description:
#   This script wraps a Python utility that updates a YAML config entry across
#   multiple project folders under a given root directory. It is designed for
#   Snakemake-based pipelines and assumes a fixed pipeline name ("wbfm").
#
#   It finds the specified config file in each project subfolder and updates
#   (or optionally adds) a specified key with a new value.
#
# Usage:
#   bash run_update_config.sh -r ROOT_FOLDER -c CONFIG_NAME -e ENTRY_KEY -v ENTRY_VALUE [-a]
#
# Example:
#   bash run_update_config.sh \
#     -r /data/projects \
#     -a
#
#
# bash /lisc/scratch/neurobiology/zimmer/ItamarLev/feedback_story/WBFM/all/2per/modify_config_wrapper.sh -r /lisc/scratch/neurobiology/zimmer/ItamarLev/feedback_story/WBFM/all/2per/test_2
#
#
#
###############################################################################

# ------------------- USER CONFIGURATION -------------------
PIPELINE="wbfm"
PYTHON_SCRIPT="/lisc/scratch/neurobiology/zimmer/ItamarLev/feedback_story/WBFM/all/2per/modify_config_wrapper.py"
CONFIG_NAME="snakemake_config.yaml"
ENTRY_KEY="pca_model"
ENTRY_VALUE="/lisc/scratch/neurobiology/zimmer/wbfm/pca_models/2per/2per_segments_30_to_80_components_5_zscore_filtered.pkl"
# ----------------------------------------------------------

# Usage info
usage() {
    echo "Usage: $0 -r ROOT_FOLDER [-a]"
    echo "  -r  Root folder containing the project folders"
    echo "  -a  Allow addition if key is missing (optional flag)"
    exit 1
}

# Parse arguments
ALLOW_ADDITION=false
while getopts ":r:a" opt; do
  case $opt in
    r) ROOT_FOLDER="$OPTARG" ;;
    a) ALLOW_ADDITION=true ;;
    *) usage ;;
  esac
done

# Check required arguments
if [ -z "$ROOT_FOLDER" ]; then
    usage
fi

# Build command
CMD="python3 $PYTHON_SCRIPT \
  --root \"$ROOT_FOLDER\" \
  --config_name \"$CONFIG_NAME\" \
  --entry_key \"$ENTRY_KEY\" \
  --entry_value \"$ENTRY_VALUE\" \
  --pipeline \"$PIPELINE\""

# Add flag only if set
if [ "$ALLOW_ADDITION" = true ]; then
  CMD="$CMD --allow_addition"
fi

# Run the command
echo "Running command:"
echo "$CMD"
eval $CMD