#!/bin/bash

# wrapper designed to generate a Principal Component (PC) model from curvature data extracted from multiple wbfm project folders.
# It automates the process of loading, optionally filtering (using z-score), interpolating, and performing PCA on curvature data.
# It expects this folder structure in the root folder:
# Expects this folder structure:
#      - root_folder should contain folders with the project names
#      -- project_folder_1
#      --- behavior
#      ---- skeleton_spline_K_signed_avg.csv
#      -- project_folder_2
#      --- behavior
#      ---- skeleton_spline_K_signed_avg.csv
# The function saves the resulting PCA model and its principal components as a pickle file for later use.
# Optional filtering is included to enhance model quality and stability by reducing the impact of outliers,
# which are known to affect PCA results significantly.

# Usage example:
# ./run_make_pc_model.sh -r /data/project -n my_model

# Default internal parameters
OUTPUT_FOLDER="" # default to the same folder as the root folder
INITIAL_SEGMENT=30 # default of wbfm pipline
END_SEGMENT=80 # default of wbfm pipline
N_COMPONENTS=5 # default of wbfm pipline
ZSCORE_FILTER=true # recommended by Itamar, but not a must

# Parse only root_folder and pc_model_name
while getopts ":r:n:" opt; do
  case ${opt} in
    r ) ROOT_FOLDER=$OPTARG ;;
    n ) PC_MODEL_NAME=$OPTARG ;;
    \? )
      echo "Invalid option: -$OPTARG" 1>&2
      exit 1
      ;;
    : )
      echo "Option -$OPTARG requires an argument." 1>&2
      exit 1
      ;;
  esac
done

# Check required arguments
if [ -z "$ROOT_FOLDER" ] || [ -z "$PC_MODEL_NAME" ]; then
  echo "Usage: $0 -r <root_folder> -n <pc_model_name>"
  exit 1
fi

# Activate Conda environment
conda activate wbfm

# Run Python script
python make_PC_model_wrapper.py \
  --root_folder "$ROOT_FOLDER" \
  --pc_model_name "$PC_MODEL_NAME" \
  --output_folder "$OUTPUT_FOLDER" \
  --initial_segment "$INITIAL_SEGMENT" \
  --end_segment "$END_SEGMENT" \
  --n_components "$N_COMPONENTS" \
  --zscore_filter "$ZSCORE_FILTER"
