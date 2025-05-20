import os
import logging
from tqdm import tqdm
import sys

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Or DEBUG, ERROR, etc.

# Create file handler
handler = logging.FileHandler('modify_config_wrapper.log')
handler.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger (avoid adding multiple handlers)
if not logger.handlers:
    logger.addHandler(handler)

# import yaml from ruamel
from ruamel.yaml import YAML

def find_config_file(dataset_path:str, config_name:str, pipline:str)->str:
    """
    find the config file in the dataset path.
    :param dataset_path: the path to the dataset
    :param config_name: the name of the config file to find
    :param pipline: pipeline name

    :return: path to the config file
    """
    if pipline in ["wbfm","population_recordings","ZIM06"]:
       config_sub_folder = "snakemake"
    else:
        logger.warning("find config implemented only for pipelines wbfm, ZIM06 and population_recordings")
        config_sub_folder = "snakemake"

    config_path = os.path.join(dataset_path,config_sub_folder, config_name)

    if not os.path.exists(config_path):
        logger.error(f"Config path {config_path} not found in subfolder {config_sub_folder},\ntrying to find in {dataset_path}")
        return None

    return config_path

def change_config_entry(config_path: str, entry_key:str, entry_value, allow_addition:bool = False):
    """
    Change the entry in the config file
    :param config_path: path to the config file
    :param entry_key: key to change
    :param entry_value: value to change
    :param allow_addition: if True, add the config entry if it does not exist

    :return:
    """
    # open the config file
    yaml = YAML()
    yaml.preserve_quotes = True  # Optional: keeps quotes if present

    with open(config_path, 'r') as f:
        config = yaml.load(f)

    # check if the entry exists
    if entry_key not in config and not allow_addition:
        logger.error(f"Entry {entry_key} not found in config file {config_path}\nif you want to add it, set allow_addition to True")

        return None

    # change the entry
    config[entry_key] = entry_value

    # save the config file
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return

def change_config_entry_wrapper(root_folder:str,
                                config_name:str,
                                entry_key:str,
                                entry_value:str,
                                allow_addition:bool = False,
                                pipline:str = "wbfm"):
    """
    change the config entry in all folders with the config file.
    :param root_folder: str, root folder to search for the config file
    :param config_name: str, name of the config file
    :param entry_key: str, key to change
    :param entry_value: value to change
    :param allow_addition: boo, if True, add the config entry if it does not exist
    :param pipline: pipeline name
    :return:
    """

    logger.info("Starting to change config entry in all folders with the config file")
    logger.info(f"Root folder: {root_folder}")

    # find all project folders with the config file
    all_folders = [os.path.join(root_folder,folder) for folder in os.listdir(root_folder) if os.path.isdir(os.path.join(root_folder,folder))]

    # use find config file to know which folders are valid
    all_folders = [folder for folder in all_folders if find_config_file(folder, config_name, pipline) is not None]

    logger.info(f"Found {len(all_folders)} {pipline} project folders with the expected config file {config_name} in {root_folder}")
    logger.info(f"...entering config entry {entry_key} with {entry_value} in the config file")

    # loop over all folders
    for folder in tqdm(all_folders, desc=f"Changing config file {config_name}", unit="project", total=len(all_folders), file=sys.stdout):
        # find the config file
        config_path = find_config_file(folder, config_name, pipline)
        if config_path is None:
            logger.error(f"Config file {config_name} not found in {folder}")
            continue
        # change the config file
        change_config_entry(config_path, entry_key, entry_value,allow_addition)

    logger.info("Finished!")
    return None

# parse arguments in main
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='change the config entry in all folders with the config file.')
    parser.add_argument('-r', '--root', help='root_folder with all projects', required=True)
    parser.add_argument('-c', '--config_name', help='name of config file to be changed, default snakemake_config.yaml', default="snakemake_config.yaml", required=True)
    parser.add_argument('-e', '--entry_key', help='key to change', required=True)
    parser.add_argument('-v', '--entry_value', help='value to change', required=True)
    parser.add_argument('-a', '--allow_addition', help='if True, add the config entry if it does not exist', default=False, required=False, action='store_true')
    parser.add_argument('-p', '--pipeline', help='pipeline name, important for finding the right folder of config, default wbfm', default="wbfm", required=False, choices=["wbfm","population_recordings","ZIM06"])

    args = parser.parse_args()
    root_folder = args.root
    config_name = args.config_name
    entry_key = args.entry_key
    entry_value = args.entry_value
    allow_addition = args.allow_addition
    pipline = args.pipeline

    change_config_entry_wrapper(root_folder, config_name=config_name, entry_key=entry_key, entry_value=entry_value, allow_addition=allow_addition,pipline=pipline)