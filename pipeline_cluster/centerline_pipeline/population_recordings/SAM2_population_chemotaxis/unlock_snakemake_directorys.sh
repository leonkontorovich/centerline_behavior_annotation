#!/bin/bash

# Get current directory
current_dir="$PWD"

# Process each subdirectory in src
for dir in "${current_dir}"/src/*/; do
    if [ -d "$dir" ]; then
        cd "$dir"
        snakemake --unlock
        cd "$current_dir"
    fi
done
