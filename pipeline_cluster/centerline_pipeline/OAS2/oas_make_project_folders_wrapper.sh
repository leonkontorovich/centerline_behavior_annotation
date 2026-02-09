#!/bin/bash

# -------------------------------------------
# prepare_oas_project_folders.sh
# Simple script to call the Python organizer
#
# This script organizes recordings into project folders for OAS projects.
# It searches a root folder for valid recording folders (containing 'worm' in their name)
# and creates a new project folder for each valid recording inside the output folder.
# the code also modifies the project_config.yaml raw and parent_data_folder paths to the correct raw data folders.
#
# Requirements for a valid recording folder:
# 1. Contains a subfolder ending with 'Ch0'.
# 2. Contains a 'worm_config.yaml' file.
# 3. Contains a file ending with '-TablePosRecord.txt'.
#
# Example usage:
# PROJECT_DEFAULT_PATH "/lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/OAS1/sam2_wbfm_spinoff_with_pharynx_pumping/new_project_default"
# ./prepare_oas_project_folders.sh /path/to/root /path/to/output /path/to/default_project_folder
# Specific example:
# bash /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/OAS2/oas_make_project_folders_wrapper.sh /lisc/data/scratch/neurobiology/zimmer/ItamarLev/pepita/test2 /lisc/data/scratch/neurobiology/zimmer/ItamarLev/pepita/test2_projects /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/OAS1/sam2_wbfm_spinoff_with_pharynx_pumping/new_project_default
# -------------------------------------------

ROOT_FOLDER="$1"
OUTPUT_FOLDER="$2"
DEFAULT_PROJECT="$3"

if [ -z "$ROOT_FOLDER" ] || [ -z "$OUTPUT_FOLDER" ] || [ -z "$DEFAULT_PROJECT" ]; then
    echo "Usage: $0 <root_folder> <output_folder> <default_project_folder>"
    exit 1
fi

echo "Preparing OAS project folders..."
python3 /lisc/data/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/OAS2/oas_make_project_folders.py --root "$ROOT_FOLDER" --output "$OUTPUT_FOLDER" --default_project "$DEFAULT_PROJECT"
