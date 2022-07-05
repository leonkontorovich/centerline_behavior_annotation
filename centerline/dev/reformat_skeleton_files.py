import pandas as pd
import numpy as np
import os


#read skeleton files
#write h5 file multiindex
# format:
# level 0: bodysegment 1, .. 100 or more
# level 1: x, y, k



def read_skeleton_files(main_path):
    """

    :param main_path:
    :return:
    """
    df_splineX = pd.read_csv(main_path + 'spline_X_coords.csv', header=None)
    df_splineY = pd.read_csv(main_path + 'spline_Y_coords.csv', header=None)
    df_splineK = pd.read_csv(main_path + 'spline_K.csv', header=None)

    return df_splineX, df_splineY, df_splineK


def reformat_skeleton_files(df_splineX, df_splineY, df_splineK):
    """

    :param df_splineX:
    :param df_splineY:
    :param df_splineK:
    :return:
    """
    l=[df_splineX, df_splineY, df_splineK]

    new_df = pd.concat(l, keys= ['x', 'y', 'k'], names= ["coords", "segment"], axis=1)

    new_df.swaplevel(0, 1, axis=1).sort_index(axis=1)
    return new_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--i_path', help='input path', required=True)

    args = vars(parser.parse_args())
    input_path = args['i_path']
    df_splineX, df_splineY, df_splineK = read_skeleton_files(input_path)
    new_df = reformat_skeleton_files(df_splineX, df_splineY, df_splineK)
    new_df.to_csv(input_path + 'skeleton_spline_merged.csv')