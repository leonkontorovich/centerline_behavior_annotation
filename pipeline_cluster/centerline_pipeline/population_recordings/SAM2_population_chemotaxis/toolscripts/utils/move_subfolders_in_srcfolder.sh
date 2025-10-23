#!/bin/bash

# Function to move contents from _new folders (no deletion)
fix_nested_folders() {
    local parent_dir="$1"
    
    # Find and move contents of folders ending with '_new'
    find "$parent_dir" -mindepth 1 -maxdepth 1 -type d -name "*_new" | while read folder; do
        # Move all contents one level up, keeping the original _new folder
        mv "$folder"/* "$(dirname "$folder")/" 2>/dev/null
    done
}

# Execute the function for current working directory
fix_nested_folders "$PWD"

echo "Files have been moved up one level. Original _new folders remain in place."
