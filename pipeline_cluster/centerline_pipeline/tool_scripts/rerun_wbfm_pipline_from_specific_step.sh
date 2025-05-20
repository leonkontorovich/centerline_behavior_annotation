#!/bin/bash
# TODO: we should probably move this to WBFM package, its just a bit aggresive script becuase of "touch" so i leave it here for now
# This script runs Snakemake workflows for all valid projects inside a parent directory.
#
# For each project, it performs:
#   1. A --touch pass to mark outputs as up to date.
#   2. Then executes a specific rule using `-R <step>`.
#
# Valid projects are subfolders that contain a "project_config.yaml" file.
# Runs can be submitted via SLURM or executed locally using -c.
#
# Usage:
#   bash test.sh -t /path/to/projects -r <step_to_repeat>
#
# Example dry run:
#   bash /lisc/scratch/neurobiology/zimmer/ItamarLev/feedback_story/WBFM/all/trust_in_chatGPT/test.sh -t /data/projects -r process_skeleton_curvature -n
#
# Example actual run (via SLURM):
#   bash /lisc/scratch/neurobiology/zimmer/ItamarLev/feedback_story/WBFM/all/rerun_from_specific_spot.sh -t /lisc/scratch/neurobiology/zimmer/ItamarLev/feedback_story/WBFM/all/2per -r annotate_behaviour
#
#
# The Snakemake command executed for each project is:
#   snakemake behavior -R <step> -s pipeline.smk --latency-wait 60 --cores 56 --retries 3
#

function usage {
  echo "Usage: $0 [-t folder_of_projects] [-n] [-r step_to_repeat] [-c] [-h]"
  echo "  -t: folder of projects (required)"
  echo "  -n: dry run of this script (default: false)"
  echo "  -r: specific Snakemake step to repeat (required unless dry run)"
  echo "  -c: run locally instead of sbatch"
  echo "  -h: display help (this message)"
  exit 1
}

STEP_TO_REPEAT=""
is_dry_run=""
RUNME_ARGS=""

while getopts t:n:r:ch flag; do
  case "${flag}" in
    t) folder_of_projects=${OPTARG};;
    n) is_dry_run="True";;
    r) STEP_TO_REPEAT=${OPTARG};;
    c) RUNME_ARGS="-c";;
    h) usage;;
    *) echo "Unknown option"; usage;;
  esac
done

# Check for required params
if [ -z "$folder_of_projects" ]; then
  echo "Error: -t (folder_of_projects) is required."
  usage
fi

if [ -z "$is_dry_run" ] && [ -z "$STEP_TO_REPEAT" ]; then
  echo "Error: -r (step to repeat) is required when not in dry run mode."
  usage
fi

conda_setup_cmd="conda activate /lisc/scratch/neurobiology/zimmer/.conda/envs/wbfm/"

for f in "$folder_of_projects"/*; do
  if [ -d "$f" ] && [ ! -L "$f" ]; then
    echo "Checking folder: $f"

    for f_config in "$f"/*; do
      if [ -f "$f_config" ] && [ "${f_config##*/}" = "project_config.yaml" ]; then
        snakemake_folder="$f/snakemake"
        cd "$snakemake_folder" || exit

        if [ "$is_dry_run" ]; then
          echo "DRYRUN: Would run --touch pass:"
          echo "snakemake -s pipeline.smk --latency-wait 60 --cores 56 --touch"
          echo "DRYRUN: Would run actual step with -R:"
          echo "snakemake behavior -R $STEP_TO_REPEAT -s pipeline.smk --latency-wait 60 --cores 56 --retries 3"
        else
          touch_cmd="snakemake -s pipeline.smk --latency-wait 60 --cores 56 --touch"
          run_cmd="snakemake behavior -R $STEP_TO_REPEAT -s pipeline.smk --latency-wait 60 --cores 56 --retries 3"
          full_cmd="$conda_setup_cmd; $touch_cmd; $run_cmd"

          JOB_NAME="$(basename "$f")_${STEP_TO_REPEAT}"

          if [ "$RUNME_ARGS" = "-c" ]; then
            echo "Running locally: $touch_cmd && $run_cmd"
            eval "$touch_cmd"
            eval "$run_cmd" &
          else
            sbatch --time 5-00:00:00 \
              --cpus-per-task 1 \
              --mem 1G \
              --mail-type=FAIL,TIME_LIMIT,END \
              --wrap="$full_cmd" \
              --job-name="$JOB_NAME"
          fi
        fi
      fi
    done
  fi
done
