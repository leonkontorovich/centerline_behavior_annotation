import os
import glob
from snakemake.logging import logger
from ruamel.yaml import YAML
from typing import Any, Dict



# I need a function that reads the project_config and finds all of the relevant paths!!
# such as the: raw_data_path, behavior_output_dir, snakemake and cluster config?

logger = logging.getLogger(__name__)
# --------------------------
# HELPER FUNCTIONS
# --------------------------


def load_config(config_path):
    """Load a config.yaml, logging a warning if missing."""

    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return {}

    with open(config_path, 'r') as f:
        return YAML().load(f)

def deep_config_update(original: Dict[str, Any], updates: Dict[str, Any], path="") -> Dict[str, Any]:
    """
    Recursively update original dict with updates dict (nested merge).
    Logs which keys are updated or added.
    """
    for key, value in updates.items():
        full_path = f"{path}.{key}" if path else key
        if key in original and isinstance(original[key], dict) and isinstance(value, dict):
            # Nested dictionary -> recurse
            deep_config_update(original[key], value, path=full_path)
        else:
            if key in original:
                logger.info(f"Updating config key '{full_path}': {original[key]} -> {value}")
            else:
                logger.info(f"Adding new config key '{full_path}' with value: {value}")
            original[key] = value
    return original

def load_and_merge_configs(*config_paths) -> Dict[str, Any]:
    """
    Load multiple YAML config files and merge them in order.
    Later files override earlier ones (deep merge).
    """
    final_config: Dict[str, Any] = {}

    for path in config_paths:
        logger.info(f"Loading config: {path}")
        cfg = load_config(path)
        deep_config_update(final_config, cfg)

    return final_config



def find_background_file(raw_data_folder, keyword="background", ext="*.tif"):
    """
    Finds a single background file by:
    - Going to the parent directory of `raw_data_folder`
    - Locating a folder whose name contains `keyword`
    - Inside that folder, finding exactly one file matching the glob pattern `ext`
    """

    # Parent directory of raw_data_folder
    data_path = os.path.dirname(raw_data_folder)

    # Step 1: find folder containing keyword
    bg_folders = [
        os.path.join(data_path, f)
        for f in os.listdir(data_path)
        if os.path.isdir(os.path.join(data_path, f))
        and keyword.lower() in f.lower()
    ]

    if not bg_folders:
        raise FileNotFoundError(
            f"No folder containing '{keyword}' found in '{data_path}'."
        )
    if len(bg_folders) > 1:
        raise ValueError(
            f"Multiple folders containing '{keyword}' found: {bg_folders}. "
            "Expected exactly one."
        )

    bg_folder = bg_folders[0]

    # Step 2: find matching file using glob
    search_pattern = os.path.join(bg_folder, ext)
    candidates = glob.glob(search_pattern)

    if not candidates:
        raise FileNotFoundError(
            f"No file matching '{ext}' found in background folder '{bg_folder}'."
        )

    if len(candidates) > 1:
        raise ValueError(
            f"Multiple files matching '{ext}' found in '{bg_folder}': {candidates}. "
            "Expected exactly one."
        )
    background_img_path = candidates[0]

    return background_img_path



def load_autoscope_dataset_config(project_config_path: str) -> Dict[str, Any]:
    """
    Load an Autoscope dataset based on its project config file.
    Returns a dictionary containing merged configs and key paths.
    """

    # Load project config
    project_config = load_config(project_config_path)
    project_dir = os.path.dirname(project_config_path)

    # Determine raw data directories
    raw_data_dir = project_config["parent_data_folder"]
    if not os.path.isdir(raw_data_dir):
        raise FileNotFoundError(f"Parent data folder does not exist: {raw_data_dir}")

    # Detect the unique subfolder containing "Ch0"
    ch0_folders = [
        os.path.join(raw_data_dir, f)
        for f in os.listdir(raw_data_dir)
        if os.path.isdir(os.path.join(raw_data_dir, f)) and "Ch0" in f
    ]
    if len(ch0_folders) != 1:
        raise RuntimeError(f"Expected exactly one 'Ch0' subfolder in {raw_data_dir}, found: {ch0_folders}")
    raw_data_subfolder = ch0_folders[0]

    # Output directory
    output_behavior_dir = os.path.join(project_dir, "behavior")
    os.makedirs(output_behavior_dir, exist_ok=True)

    # Build config file paths
    worm_config = os.path.join(raw_data_dir, "worm_config.yaml")
    cluster_config = os.path.join(project_dir, project_config["subfolder_configs"]["cluster"])
    snakemake_config = os.path.join(project_dir, project_config["subfolder_configs"]["snakemake"])

    # Load and merge configs
    config = load_and_merge_configs(worm_config, cluster_config, snakemake_config)

    # Add key paths to the config
    config.update({
        "project_dir": project_dir,
        "raw_data_dir": raw_data_dir,
        "raw_data_subfolder": raw_data_subfolder,
        "output_behavior_dir": output_behavior_dir
    })

    return config
