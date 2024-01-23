#!/bin/bash
# This job requests from SLURM to allocate 1 node.
#SBATCH --job-name=DLC_label_videos_ulises
#SBATCH --nodes=1
# On that node, it will run 4 tasks, each with 1 core and 1 GB of memory.
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
# After Thomas Rattei suggestion I specify mem instead of mem-per-cpu
#SBATCH --mem=12G
# And it will place the output of the commands into following file
#SBATCH --output=/scratch/neurobiology/zimmer/ulises/code/cluster_outputs/%x_%A_%a.txt
#SBATCH --array=1-4

#SBATCH --partition=gpu
#SBATCH --gpus=1


echo "All jobs in this array have:"
echo "- SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "- SLURM_ARRAY_TASK_COUNT=${SLURM_ARRAY_TASK_COUNT}"
echo "- SLURM_ARRAY_TASK_MIN=${SLURM_ARRAY_TASK_MIN}"
echo "- SLURM_ARRAY_TASK_MAX=${SLURM_ARRAY_TASK_MAX}"

echo "This job in the array has:"
echo "- SLURM_JOB_ID=${SLURM_JOB_ID}"
echo "- SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"

#My own function, outputs avi. Very slow. Needs 'Head' and 'Tail' annotated (this last part might be fixed)
# Try to not use cluster_label_videos but dlc_utils.py label_videos() in the future

cd /scratch/neurobiology/zimmer/ulises/wbfm/20220223

DIR_NAME=$(find $PWD -maxdepth 4 -mindepth 3 -type d -wholename "*worm*channel-0-behaviour*" | head -n $SLURM_ARRAY_TASK_ID | tail -n 1)
echo $DIR_NAME

cd $DIR_NAME
echo "cd'ed into the directory"

VIDEOFILE_PATH=$(find $PWD -mindepth 1 -maxdepth 1 -type f -wholename "*/2*background_substracted.avi" | head -n $SLURM_ARRAY_TASK_ID | tail -n 1)

H5_FILEPATH=$(find $PWD -mindepth 1 -maxdepth 1 -type f -wholename "*/2*.h5" | head -n $SLURM_ARRAY_TASK_ID | tail -n 1)
echo $VIDEOFILE_PATH
echo $H5_FILEPATH

#load the conda environment.
echo "Environment loaded?"
source /apps/conda/miniconda3/bin/activate /scratch/neurobiology/zimmer/.conda/envs/HR_tracker


echo "Run python code"
python /scratch/neurobiology/zimmer/ulises/code/dlc_utils_code/cluster_label_videos.py -video ${VIDEOFILE_PATH} -h5 ${H5_FILEPATH}
echo "Done with bash script"