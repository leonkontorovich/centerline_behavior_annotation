From Experiment folder run this to generate folderstructure and copy files:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/create_folders_and_copy_chemotaxis_population_pipeline.sh

to just copy files in already existing folder structure run:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/copy_chemotaxis_population_pipeline.sh

to start the pipeline for dataset run:

bash /lisc/scratch/neurobiology/zimmer/autoscope/code/centerline_behavior_annotation/pipeline_cluster/centerline_pipeline/population_recordings/SAM2_population_chemotaxis/population_centerline/run_chemotaxis_population_pipeline.sh


# Folder Search and Deletion Commands

This guide provides two shell commands to:
1. Search for directories with a specific name within the current working directory.
2. Delete directories with a specific name within the current working directory.

## Commands

### 1. Searching for Directories Named `frame_directory`

To locate all folders named `frame_directory` in the current directory and its subdirectories, use the following command:

```bash
find "$(pwd)" -type d -name "frame_directory"
```

**Explanation**:
- `find "$(pwd)"`: Initiates the search in the current working directory (`$(pwd)` represents the present directory path).
- `-type d`: Restricts the search to directories only.
- `-name "frame_directory"`: Looks for directories that match the exact name `"frame_directory"`.

### 2. Deleting Directories Named `frame_directory`

To delete all directories named `frame_directory` in the current working directory and its subdirectories, run this command:

```bash
find "$(pwd)" -type d -name "frame_directory" -exec rm -rf {} +
```

**Explanation**:
- `find "$(pwd)"`: Starts the search in the current working directory.
- `-type d`: Limits the search to directories only.
- `-name "frame_directory"`: Searches for directories that match the specified name.
- `-exec rm -rf {} +`: Deletes each matching directory and its contents recursively and forcefully. Be cautious when using this command, as it permanently deletes all matching directories.

### Summary

| Command                                                     | Description                                                  |
| ----------------------------------------------------------- | ------------------------------------------------------------ |
| `find "$(pwd)" -type d -name "frame_directory"`             | Searches for all `frame_directory` folders in the current directory. |
| `find "$(pwd)" -type d -name "frame_directory" -exec rm -rf {} +` | Deletes all `frame_directory` folders in the current directory. |

**Note**: Use these commands carefully, especially the delete command, as it will permanently remove folders and their contents.
