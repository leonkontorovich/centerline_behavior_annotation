# The scripts here aim to invert the sign of some spline_K
# recordings so that Ventral and Dorsal Curvatures have the same sign across worms

import pandas as pd
import yaml
import logging


def invert_df(spline_K_path, output_file_path):
    """
    Invert the sign of a dataframe from the input_path and save it in the output_path
    Works when the dataframe does not have header nor index.
    Not clear it would work if the df ahas actually headers or index.
    
    :param input_path: 
    :param output_path: 
    :return: 
    """
    df = pd.read_csv(spline_K_path, index_col=None, header=None)
    df = - df
    df.to_csv(output_file_path, header=None, index=None)

    return df


def invert_df_based_on_ventral(spline_K_path, output_file_path, ventral):

    if ventral == 'left':
        logging.info('ventral is on the left side of the image, changing signs')
        invert_df(spline_K_path, output_file_path)

    else:
        if ventral == 'right':
            logging.info('ventral is on the right side of the image, keeping signs')
            df = pd.read_csv(spline_K_path, index_col=None, header=None)
            df.to_csv(output_file_path, header=None, index=None)
        else:
            raise AttributeError(f"ventral should be either 'left' or 'right', you have: {ventral}")

    return None


def main(arg_list):
    # Invert sign with folder name PREFERABLY with DATASET FOLDER (NOT BH folder)
    import argparse
    import os
    import glob
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--input_path', help='folder of wbfm dataset', required=True)
    parser.add_argument('-r', '--raw_data_path', help='folder of raw dataset', required=True)

    args = vars(parser.parse_args(arg_list))
    project = args['input_path']
    raw_data_path = args['raw_data_path']

    logging.info(f"Output folder: {project}, raw data folder: {raw_data_path}")

    input_path = glob.glob(os.path.join(project, "skeleton_spline_K.csv"))[0]
    output_path = os.path.splitext(input_path)[0]+"_signed.csv"

    # Get config file
    config_yaml_path = glob.glob(os.path.join(raw_data_path, "config.yaml"))
    if len(config_yaml_path) == 1:
        config_yaml_path = config_yaml_path[0]
    elif len(config_yaml_path) == 0:
        logging.warning(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        logging.warning(f"No config file found in {raw_data_path}; SKIPPING THIS STEP!!!!!!!!")
        logging.warning(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        ventral = 'right'  # Doesn't change anything
        invert_df_based_on_ventral(input_path, output_path, ventral)
        return
        # raise FileNotFoundError(f"No config file found in {raw_data_path}")
    else:
        raise FileNotFoundError(f"More than one config file found in {raw_data_path}")

    # Read yaml file and get ventral parameter (only one needed)
    with open(config_yaml_path, 'r') as f:
        config = yaml.safe_load(f)

    ventral = config.get('ventral', None)
    if ventral is None:
        raise AttributeError(f"ventral parameter not found in config file: {config_yaml_path}")

    invert_df_based_on_ventral(input_path, output_path, ventral)


def main_benjamin(arg_list):
    # Invert sign with folder name PREFERABLY with DATASET FOLDER (NOT BH folder)
    import argparse
    parser = argparse.ArgumentParser(description='invert curvature sign')
    parser.add_argument('--spline_K_path', help='spline_K file', required=True)
    parser.add_argument('--ventral', help='ventral annotation from config', required=True)
    parser.add_argument('--output_file_path', help='output file', required=True)

    args = parser.parse_args(arg_list)
    spline_K_path = args.spline_K_path
    ventral = args.ventral
    output_file_path = args.output_file_path

    invert_df_based_on_ventral(spline_K_path, output_file_path, ventral)
    

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
