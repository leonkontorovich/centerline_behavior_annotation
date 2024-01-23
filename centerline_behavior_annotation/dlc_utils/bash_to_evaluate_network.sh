#!/bin/bash
# This job requests from SLURM to allocate 1 node.
#SBATCH --job-name=DLC_analyze_videos
#SBATCH --nodes=1
# On that node, it will run 4 tasks, each with 1 core and 1 GB of memory.
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=20
# After Thomas Rattei suggestion I specify mem instead of mem-per-cpu
#SBATCH --mem=20G
# And it will place the output of the commands into following file
#SBATCH --output=/scratch/neurobiology/zimmer/ulises/code/cluster_outputs/%x_%A_%a.txt
#SBATCH --array=1-6



echo "All jobs in this array have:"
echo "- SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "- SLURM_ARRAY_TASK_COUNT=${SLURM_ARRAY_TASK_COUNT}"
echo "- SLURM_ARRAY_TASK_MIN=${SLURM_ARRAY_TASK_MIN}"
echo "- SLURM_ARRAY_TASK_MAX=${SLURM_ARRAY_TASK_MAX}"

echo "This job in the array has:"
echo "- SLURM_JOB_ID=${SLURM_JOB_ID}"
echo "- SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"



echo "NEVER TRIED IT BEFORE YET"

MAIN_PATH="/scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/wbfm_nose_tail-ulises-2023-01-04/config.yaml"
#$"/scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/wbfm_noise_tail-Ulises-2022-06-13/config.yaml"
echo "Config file is: ${MAIN_PATH}"

echo "Load cudnn module"

module load cudnn/7.6.5

echo "Run python code:"

#Activate the following env in the terminal
#load the conda environment.
echo "Environment loaded?"
source /apps/conda/miniconda3/bin/activate /scratch/neurobiology/zimmer/.conda/envs/HR_tracker

#python /groups/zimmer/Ulises/code/unet-master/unet_script_train.py >log_${SLURM_JOB_ID}.txt
python /scratch/neurobiology/zimmer/ulises/code/dlc_utils_code/cluster_evaluate_network.py -path_config_file ${MAIN_PATH}








