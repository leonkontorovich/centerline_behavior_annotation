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
    df_splineX = pd.read_csv(os.path.join(main_path, 'skeleton_spline_X_coords.csv'), header=None)
    df_splineY = pd.read_csv(os.path.join(main_path, 'skeleton_spline_Y_coords.csv'), header=None)
    df_splineK = pd.read_csv(os.path.join(main_path, 'skeleton_spline_K.csv'), header=None)

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

    new_df = new_df.swaplevel(0, 1, axis=1).sort_index(axis=1)

    return new_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--i_path', help='input path', required=True)

    args = vars(parser.parse_args())
    input_path = args['i_path']
    print('This is the input path python is seeing: ', input_path)
    df_splineX, df_splineY, df_splineK = read_skeleton_files(input_path)

    # TODO: improve this in a loop
    df_splineX = df_splineX.round(decimals=2)
    df_splineY = df_splineY.round(decimals=2)
    df_splineK = df_splineK.round(decimals=6)

    new_df = reformat_skeleton_files(df_splineX, df_splineY, df_splineK)
    new_df.to_csv(os.path.join(input_path, 'skeleton_spline_merged.csv'))
    print('python complete')

    # input_path = '/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20220216/data/worm6/2022-02-16_17-14-18_worm6-channel-0-behaviour-'
    # df_splineX, df_splineY, df_splineK = read_skeleton_files(input_path)
    # new_df = reformat_skeleton_files(df_splineX, df_splineY, df_splineK)
    # new_df.to_csv(os.path.join(input_path, 'skeleton_spline_merged.csv'))
    #
    # df = pd.read_csv(os.path.join(input_path, 'skeleton_spline_merged.csv'))
    #
    # print('end')
