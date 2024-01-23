#!/bin/bash
# This job requests from SLURM to allocate 1 node.
#SBATCH --job-name=DLC_label_videos
#SBATCH --nodes=1
# On that node, it will run 4 tasks, each with 1 core and 1 GB of memory.
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
# Running time will be:
#SBATCH --time=2-00:00:00
# After Thomas Rattei suggestion I specify mem instead of mem-per-cpu
#SBATCH --mem=0

#SBATCH --partition=gpu
#SBATCH --gpus=1

# And it will place the output of the commands into following file
#SBATCH --output=/scratch/neurobiology/zimmer/ulises/code/cluster_outputs/%x_%A_%a.txt
#SBATCH --array=1-3


 
echo "All jobs in this array have:"
echo "- SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "- SLURM_ARRAY_TASK_COUNT=${SLURM_ARRAY_TASK_COUNT}"
echo "- SLURM_ARRAY_TASK_MIN=${SLURM_ARRAY_TASK_MIN}"
echo "- SLURM_ARRAY_TASK_MAX=${SLURM_ARRAY_TASK_MAX}"
 
echo "This job in the array has:"
echo "- SLURM_JOB_ID=${SLURM_JOB_ID}"
echo "- SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"

# ONE WAY (OUT OF THREE)
#DLC function: outputs mp4


cd /scratch/neurobiology/zimmer/active_sensing/zim06/zim2391/test_dlc_pipeline/20230515/

PATH_CONFIG_FILE="/scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/zim2391_RIA-josefine_meyer-2023-06-22/config.yaml"

echo $PATH_CONFIG_FILE

VIDEOFILE_PATH=$(find $PWD -maxdepth 4 -wholename "/*worm*/Ch0/raw_stack_normalised.avi" | head -n $SLURM_ARRAY_TASK_ID | tail -n 1)
echo $VIDEOFILE_PATH

#load the conda environment.
source /apps/conda/miniconda3/bin/activate /scratch/neurobiology/zimmer/.conda/envs/HR_tracker
echo "Environment loaded?"

#FILTERED = "False"
echo "Entering python code"
python /scratch/neurobiology/zimmer/ulises/code/dlc_utils_code/cluster_create_labeled_videos.py -path_config_file ${PATH_CONFIG_FILE} -videofile_path ${VIDEOFILE_PATH}
echo "Bash script finished"

# SECOND WAY OUT OF THREE:
# DLC but without .py file
#
#MAIN_PATH=$"/scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/new_worms_5_7_8-fabio-2022-04-15/config.yaml"
#
#cd /scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/new_worms_5_7_8-fabio-2022-04-15/videos/
##cd /scratch/neurobiology/zimmer/ulises/active_sensing/epifluorescence_recordings/20220408/data
#
#VIDEOFILE_PATH=$(find $PWD -maxdepth 3 -type f -wholename "*kept_stack.avi" | head -n $SLURM_ARRAY_TASK_ID | tail -n 1)
#
#echo "main path is: "
#echo ${MAIN_PATH}
#
#echo "videofile is "
#echo ${VIDEOFILE_PATH}
#
#echo "Load cudnn module"
#
#module load cudnn/7.6.5
#
#echo "Run python code:"
#
##python /groups/zimmer/Ulises/code/unet-master/unet_script_train.py >log_${SLURM_JOB_ID}.txt
##python /scratch/neurobiology/zimmer/ulises/code/dlc_utils_code/cluster_create_labeled_videos.py -path_config_file ${MAIN_PATH} -videofile_path ${VIDEOFILE_PATH} -filtered False
#
#python -c "print('entering python code');
#import os
#import pandas as pd
#import numpy as np
##os.environ["DLClight"]="True"
#import deeplabcut
#deeplabcut.create_labeled_video('$MAIN_PATH', '$VIDEOFILE_PATH')
#print('end of python code')"
#echo "script ended"


# THIRD WAY OUT OF THREE: SEE bash_to_label_videos_ulises







