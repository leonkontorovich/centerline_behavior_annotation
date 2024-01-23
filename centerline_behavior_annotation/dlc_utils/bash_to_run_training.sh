#!/bin/bash
# This job requests from SLURM to allocate 1 node.
#SBATCH --job-name=DLC_training
#SBATCH --nodes=1
# On that node, it will run 4 tasks, each with 1 core and 1 GB of memory.
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
# Running time will be:
#SBATCH --time=2-00:00:00
# After Thomas Rattei suggestion I specify mem instead of mem-per-cpu
#SBATCH --mem=0
# And it will place the output of the commands into following file
#SBATCH --output=/scratch/neurobiology/zimmer/ulises/code/cluster_outputs/%x_%A_%a.txt



 
echo "All jobs in this array have:"
echo "- SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "- SLURM_ARRAY_TASK_COUNT=${SLURM_ARRAY_TASK_COUNT}"
echo "- SLURM_ARRAY_TASK_MIN=${SLURM_ARRAY_TASK_MIN}"
echo "- SLURM_ARRAY_TASK_MAX=${SLURM_ARRAY_TASK_MAX}"
 
echo "This job in the array has:"
echo "- SLURM_JOB_ID=${SLURM_JOB_ID}"
echo "- SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"



#RUN THE CODE

MAIN_PATH=$"/scratch/neurobiology/zimmer/active_sensing/zim06/DLC_annotations/zim2391_RIA-josefine_meyer-2023-06-22/config.yaml"

echo ${MAIN_PATH}

echo "Load cudnn module"

#module load cudnn/7.6.5
module load cudnn/8.9.1_cuda11

#load the conda environment.
source /apps/conda/miniconda3/bin/activate /scratch/neurobiology/zimmer/.conda/envs/HR_tracker
echo "Environment loaded?"

echo "Run python code:"
#python /groups/zimmer/Ulises/code/unet-master/unet_script_train.py >log_${SLURM_JOB_ID}.txt
python /scratch/neurobiology/zimmer/ulises/code/dlc_utils_code/cluster_train_network.py -path_config_file ${MAIN_PATH} -displayiters 500 -saveiters 2500








