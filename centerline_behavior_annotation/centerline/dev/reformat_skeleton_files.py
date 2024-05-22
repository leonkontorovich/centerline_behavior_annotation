import pandas as pd
import numpy as np
import os
import argparse


#read skeleton files
#write h5 file multiindex
# format:
# level 0: bodysegment 1, .. 100 or more
# level 1: x, y, k



def read_skeleton_files(main_path):
    """

    :param main_path: folder where the files skeleton_spline**.csv are
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

def main(arg_list=None):
    # run it with cluster_jobs/array_job_directories.sh

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--input_spline_K', help='csv file with the spline curvature', required=True)
    parser.add_argument('--input_spline_X', help='csv file with the spline X coords', required=True)
    parser.add_argument('--input_spline_Y', help='csv file with the spline Y coords', required=True)
    parser.add_argument('--o_path', help='output path, has t be .csv file', required=True)

    args = vars(parser.parse_args(arg_list))
    spline_K = args['input_spline_K']
    spline_X = args['input_spline_X']
    spline_Y = args['input_spline_Y']

    output_path = args['o_path']

    # spline_K = "/Volumes/scratch/neurobiology/zimmer/ulises/test_area/autoscope_snakemake/data/worm1/2022-11-27_12-31_w1_Ch0/skeleton_spline_K.csv"
    # spline_X = "/Volumes/scratch/neurobiology/zimmer/ulises/test_area/autoscope_snakemake/data/worm1/2022-11-27_12-31_w1_Ch0/skeleton_spline_X_coords.csv"
    # spline_Y = "/Volumes/scratch/neurobiology/zimmer/ulises/test_area/autoscope_snakemake/data/worm1/2022-11-27_12-31_w1_Ch0/skeleton_spline_Y_coords.csv"
    # output_path = "/Volumes/scratch/neurobiology/zimmer/ulises/test_area/autoscope_snakemake/data/worm1/2022-11-27_12-31_w1_Ch0/skeleton_merged_spline_data.csv"

    df_splineK = pd.read_csv(spline_K, header=None)
    df_splineX = pd.read_csv(spline_X, header=None)
    df_splineY = pd.read_csv(spline_Y, header=None)

    # TODO: improve this in a loop
    df_splineK = df_splineK.round(decimals=6)
    df_splineX = df_splineX.round(decimals=2)
    df_splineY = df_splineY.round(decimals=2)

    new_df = reformat_skeleton_files(df_splineX, df_splineY, df_splineK)
    new_df.to_csv(output_path)
    print('python complete')


if __name__ == "__main__":

    main(sys.argv[1:])  # exclude the script name from the args when called from shell