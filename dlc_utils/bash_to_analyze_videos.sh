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
#SBATCH --array=1-15


 
echo "All jobs in this array have:"
echo "- SLURM_ARRAY_JOB_ID=${SLURM_ARRAY_JOB_ID}"
echo "- SLURM_ARRAY_TASK_COUNT=${SLURM_ARRAY_TASK_COUNT}"
echo "- SLURM_ARRAY_TASK_MIN=${SLURM_ARRAY_TASK_MIN}"
echo "- SLURM_ARRAY_TASK_MAX=${SLURM_ARRAY_TASK_MAX}"
 
echo "This job in the array has:"
echo "- SLURM_JOB_ID=${SLURM_JOB_ID}"
echo "- SLURM_ARRAY_TASK_ID=${SLURM_ARRAY_TASK_ID}"



#RUN THE CODE
# cd /groups/zimmer/Ulises/code/unet-master/

MAIN_PATH="/scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/zim2391_RIA-josefine_meyer-2023-06-22/config.yaml"
#$"/scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/wbfm_noise_tail-Ulises-2022-06-13/config.yaml"
echo "Config file is: ${MAIN_PATH}"

#cd /scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/new_worms_5_7_8-fabio-2022-04-15/videos/
cd /scratch/neurobiology/zimmer/active_sensing/zim06/zim2391/for_pipeline


VIDEOFILE_PATH=$(find $PWD -maxdepth 6 -type f -wholename "*200*cropped_normalised.avi" | head -n $SLURM_ARRAY_TASK_ID | tail -n 1)

echo "Video to analyze is: ${VIDEOFILE_PATH}"

echo "Load cudnn module"

#module load cudnn/7.6.5

echo "Run python code:"

#Activate the following env in the terminal
#load the conda environment.
echo "Environment loaded?"
source /apps/conda/miniconda3/bin/activate /scratch/neurobiology/zimmer/.conda/envs/HR_tracker


#echo "Running analyze videos:"
#python /scratch/neurobiology/zimmer/ulises/code/dlc_utils_code/cluster_analyze_videos.py -path_config_file ${MAIN_PATH} -videofile_path ${VIDEOFILE_PATH}
#echo "Done with analyze videos:"

# If you want to label too:
echo "Running labelling too:"
python /scratch/neurobiology/zimmer/ulises/code/dlc_utils_code/cluster_create_labeled_videos.py -path_config_file ${MAIN_PATH} -videofile_path ${VIDEOFILE_PATH}
echo "Bash script finished"






