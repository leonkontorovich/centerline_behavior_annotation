"""
prepare_oas_project_folders.py

This script organizes recordings into project folders for OAS projects.
It searches a root folder for valid recording folders (containing 'worm' in their name)
and creates a new project folder for each valid recording inside the output folder.
the code also modifies the project_config.yaml raw and parent_data_folder paths to the correct raw data folders.

Requirements for a valid recording folder:
1. Contains a subfolder ending with 'Ch0'.
2. Contains a 'worm_config.yaml' file.
3. Contains a file ending with '-TablePosRecord.txt'.

Usage:
    python prepare_oas_project_folders.py --root /path/to/root --output /path/to/output --default_project /path/to/default_project_folder
    #TODO: update with the final path
"""

import os
import shutil
import argparse
import yaml

def find_recording_folders(root_folder):
    """
    Find folders in the root folder that contain 'worm' in their name.
    Only looks one level deep (direct subfolders of root_folder).
    Returns a list of folder paths.
    """
    worm_folders = []
    for item in os.listdir(root_folder):
        item_path = os.path.join(root_folder, item)
        if os.path.isdir(item_path) and "worm" in item.lower():
            worm_folders.append(item_path)
    return worm_folders

def validate_recording_folder(folder_path):
    """
    Check if the folder contains required items:
    - a folder ending with 'Ch0'
    - 'worm_config.yaml'
    - a file ending with '-TablePosRecord.txt'

    Returns:
        (bool, dict): (is_valid, details about missing items)
    """
    details = {"Ch0_folder": None, "worm_config": False, "table_pos_record": False}

    # Check for Ch0 folder
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path) and item.endswith("Ch0"):
            details["Ch0_folder"] = item_path
            break

    # Check for worm_config.yaml
    details["worm_config"] = "worm_config.yaml" in os.listdir(folder_path)

    # Check for -TablePosRecord.txt
    details["table_pos_record"] = any(f.endswith("-TablePosRecord.txt") for f in os.listdir(folder_path))

    is_valid = all([details["Ch0_folder"], details["worm_config"], details["table_pos_record"]])
    return is_valid, details

def create_project_folder(output_root, default_project_folder, recording_folder, ch0_folder):
    """
    Create a project folder based on default_project_folder
    and update its project_config.yaml with correct paths.
    """
    project_name = os.path.basename(recording_folder)
    project_path = os.path.join(output_root, project_name)

    if os.path.exists(project_path):
        print(f"Warning: Project folder '{project_name}' already exists. Skipping copy.")
        return project_path

    # Copy default project folder
    shutil.copytree(default_project_folder, project_path)
    print(f"Created project folder: {project_path}")

    # Update project_config.yaml
    config_path = os.path.join(project_path, "project_config.yaml")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        config['raw_data'] = ch0_folder
        config['parent_data_folder'] = recording_folder

        with open(config_path, 'w') as f:
            yaml.safe_dump(config, f)
        print(f"Updated project_config.yaml for project '{project_name}'")
    else:
        print(f"Warning: project_config.yaml not found in {project_path}")

    return project_path

def main():
    parser = argparse.ArgumentParser(description="Prepare OAS project folders from recordings.")
    parser.add_argument("--root", required=True, help="Root folder containing recordings")
    parser.add_argument("--output", required=True, help="Output folder for projects")
    parser.add_argument("--default_project", required=True, help="Path to default project folder")
    args = parser.parse_args()

    # Step 1: Find all worm recording folders
    worm_folders = find_recording_folders(args.root)
    print(f"Found {len(worm_folders)} folders containing 'worm' in their name.")

    # Step 2: Validate folders and create projects
    valid_count = 0
    for folder in worm_folders:
        is_valid, details = validate_recording_folder(folder)
        if is_valid:
            create_project_folder(args.output, args.default_project, folder, details["Ch0_folder"])
            valid_count += 1
        else:
            missing = []
            if not details["Ch0_folder"]:
                missing.append("Ch0 folder")
            if not details["worm_config"]:
                missing.append("worm_config.yaml")
            if not details["table_pos_record"]:
                missing.append("-TablePosRecord.txt")
            print(f"Skipping '{folder}' - missing: {', '.join(missing)}")

    print(f"Process complete. {valid_count} project(s) created.")

if __name__ == "__main__":
    main()
