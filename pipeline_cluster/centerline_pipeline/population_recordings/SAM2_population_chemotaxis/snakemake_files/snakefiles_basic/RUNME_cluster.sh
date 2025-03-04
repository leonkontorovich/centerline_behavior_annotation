#!/bin/bash
# Example from: https://hackmd.io/@bluegenes/BJPrrj7WB
OPT="sbatch -t {cluster.time} -p {cluster.partition} --cpus-per-task {cluster.cpus_per_task} --mem {cluster.mem} --output {cluster.output} --gres {cluster.gres}"

# Count the number of directories three levels deep that match the specific pattern and end in 'Ch0'
NUM_JOBS_TO_SUBMIT=$(find "$PWD" -mindepth 3 -maxdepth 3 -type d -wholename "*/*track*/" | wc -l)
echo "Submitting $NUM_JOBS_TO_SUBMIT Jobs. Make sure that these are the number of datasets otherwise expect errors."

# Use snakemake with specified options
snakemake --configfile config.yaml --latency-wait 500 --cluster "$OPT" --cluster-config cluster_config.yaml --jobs $NUM_JOBS_TO_SUBMIT --keep-going
