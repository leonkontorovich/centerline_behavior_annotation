# This script was written so that it matches the current snakemake pipeline with files as inputs an ouputs
# If you want to run it per folder there is the annotate_behaviour.py file


def main(arg_list):
    import argparse # comment
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser()
    parser.add_argument('-input', '--input', help='path to theinput', required=True)
    parser.add_argument('-t', '--threshold', help='threshold on the curvature', type=float, required=True)
    parser.add_argument('-i_s', '--initial_segment', help='', type=int, required=True)
    parser.add_argument('-f_s', '--final_segment', help='', type=int, required=True)
    parser.add_argument('-avg_window', '--averaging_window', help='', type=int, required=True)
    parser.add_argument('-bh', '--beh', help='path to the behavioural output', required=True)

    args = vars(parser.parse_args(arg_list))
    input_path = args['input']
    threshold = args['threshold']
    initial_segment, final_segment = args['initial_segment'], args['final_segment']
    avg_window = args['averaging_window']
    turns_annotation_path = args['beh']
    #
    # input_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/skeleton_spline_K_signed_avg.csv"
    # threshold = 1
    # initial_segment, final_segment = 10, 90
    # avg_window = 500

    print("initial_segment:")
    print(type(initial_segment))
    print(initial_segment)

    print("final_segment:")
    print(type(final_segment))
    print(final_segment)

    print("threshold:")
    print(type(threshold))
    print(threshold)

    df = pd.read_csv(input_path, header=None)
    df.fillna(0, inplace=True)
    df = df.rolling(avg_window, center=True).mean()# alternative change nans to zeros
    features = np.arange(initial_segment, final_segment)  # Separating out the features (starting bodypart, ending bodypart),a dd to config yaml
    data = df.loc[:, features].values

    #to split data into ventral and dorsal to see if this improves
    ventral_data = np.where(data > 0, data, 0) #where data is positive, keep it, otherwise set it to 0
    ventral_curvature = ventral_data.sum(axis=1)

    dorsal_data = np.where(data < 0, data, 0) #where data is negative, keep it, otherwise set it to 0
    dorsal_curvature = dorsal_data.sum(axis=1)

    # add a column in the dataframe which contains 1 if another column is higher than 0.05, -1 if lower than -0.05, and 0 if in between -0.5 and 0.5
    turns_df = pd.DataFrame()
    turns_df['turn'] = np.where(ventral_curvature > threshold, 1, np.where(dorsal_curvature < -threshold, -1, 0))

    turns_df.to_csv(turns_annotation_path)

    #plotting part
    # fig, ax = plt.subplots(dpi=100)
    # ax.plot(ventral_curvature, color='Green', linestyle='--', alpha=.5)
    # ax.plot(-dorsal_curvature, color='Purple', linestyle='--', alpha=.5)
    # ax.axhline(y=threshold, color='Red', linestyle='--')


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])