#!/bin/bash

# Get the current directory
current_dir=$(pwd)

# Define a function to clean the folder name
clean_folder_name() {
    local filename="$1"
    
    # Remove the unwanted parts from the filename
    cleaned_name=$(echo "$filename" | sed -e 's/_Ch0//g' -e 's/-TablePosRecord//g')

    # Remove the file extension for the folder name
    cleaned_name="${cleaned_name%.*}"
    echo "$cleaned_name"
}

# Loop through each file in the current directory
for file in "$current_dir"/*; do
    if [ -f "$file" ]; then

        # Get the base name of the file
        base_name=$(basename "$file")

        # Clean the base name to create the folder name
        folder_name=$(clean_folder_name "$base_name")

        # Target directory path
        target_dir="$current_dir/$folder_name"

        # Check if the target directory already exists
        if [ ! -d "$target_dir" ]; then
 
           # Create the new directory if it doesn't exist
            mkdir -p "$target_dir"
            echo "Created directory: $target_dir"
        fi

        # Check if the file is already in the target directory
        if [ ! -f "$target_dir/$base_name" ]; then

            # Move the file into the new directory
            mv "$file" "$target_dir"
            echo "Moved $file to $target_dir"
        else
            echo "File $base_name already exists in $target_dir, not moving."
        fi

        # Move all files and folders in the current directory that include the cleaned name in their name
        for item in "$current_dir"/*"$folder_name"*; do

            # Skip if item is the target directory itself
            if [ "$item" != "$target_dir" ]; then

                # Check if the item is a file or directory
                if [ -e "$item" ]; then
                    mv "$item" "$target_dir"
                    echo "Moved $item to $target_dir"
                fi
            fi
        done
    fi
done


# Path to the source file
source_file="/lisc/data/scratch/neurobiology/zimmer/EvaGratzl/autoscope/code/config_files/worm_config.yaml"

# Check if the source file exists
if [ ! -f "$source_file" ]; then
    echo "Source file not found: $source_file"
    exit 1
fi

# Find all main folders in the current directory containing the word "worm"
target_folders=$(find "$current_dir" -maxdepth 1 -type d -name "*worm*")

# Loop through each target folder and copy the file
for folder in $target_folders; do
    if [ -d "$folder" ]; then
        destination_folder="$folder"
        cp "$source_file" "$destination_folder"
        if [ $? -eq 0 ]; then
            echo "File copied to $destination_folder"
        else
            echo "Failed to copy file to $destination_folder"
        fi
    else
        echo "Directory not found: $folder"
    fi
done