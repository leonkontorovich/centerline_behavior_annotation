# The scripts here aim to invert the sign of some spline_K
# recordings so that Ventral and Dorsal Curvatures have the same sign across worms

import pandas as pd
import yaml

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
        print('ventral is on the left side of the image, changing signs')
        invert_df(spline_K_path, output_file_path)

    else:
        if ventral == 'right':
            print('ventral is on the right side of the image, keeping signs')
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
