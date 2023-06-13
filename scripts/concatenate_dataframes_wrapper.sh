#!/bin/bash
# This job requests from SLURM to allocate 1 node.
#SBATCH --job-name=array_job_directories
#SBATCH --nodes=1
# On that node, it will run 4 tasks, each with 1 core and 1 GB of memory.
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem-per-cpu=2G
# Running time will be:
#SBATCH --time=0-00:30:00
# And it will place the output of the commands into following file
#SBATCH --output=/scratch/neurobiology/zimmer/ulises/code/cluster_outputs/%x_output_%A_%a_.txt.txt
#SBATCH --array=1

echo "All jobs in this array have:"
echo "- SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "- SLURM_ARRAY_TASK_COUNT=${SLURM_ARRAY_TASK_COUNT}"
echo "- SLURM_ARRAY_TASK_MIN=${SLURM_ARRAY_TASK_MIN}"
echo "- SLURM_ARRAY_TASK_MAX=${SLURM_ARRAY_TASK_MAX}"

echo "This job in the array has:"
echo "- SLURM_JOB_ID=${SLURM_JOB_ID}"
echo "- SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"


cd /scratch/neurobiology/zimmer/ulises/wbfm/

DATAFRAME_LIST=$(find $PWD -mindepth 1 -maxdepth 10 -type f -wholename "*20221[1,2][0,1,2,3][0,3,5,7]*/data/*worm*/skeleton_spline_K_signed_avg.csv")

echo $DATAFRAME_LIST

#load the conda environment.
source /apps/conda/miniconda3/bin/activate /scratch/neurobiology/zimmer/ulises/.conda/envs/openCV
echo "Environment loaded?"

echo "Entering python...:"
python /scratch/neurobiology/zimmer/ulises/code/curvature/scripts/concatenate_dataframes_wrapper.py --dataframe_path_list $DATAFRAME_LIST
echo "end of script"
