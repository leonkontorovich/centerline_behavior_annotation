# This script was written so that it matches the current snakemake pipeline with files as inputs an ouputs
# If you want to run it per folder there is the annotate_behaviour.py file


if __name__ == "__main__":
    import argparse # comment
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser()
    parser.add_argument('-input', '--input', help='path to theinput', required=True)
    parser.add_argument('-t', '--threshold', help='threshold on the curvature', type=float, required=True)
    parser.add_argument('-i_s', '--initial_segment', help='', type=float, required=True)
    parser.add_argument('-f_s', '--final_segment', help='', type=float, required=True)
    parser.add_argument('-bh', '--beh', help='path to the behavioural output', required=True)

    args = vars(parser.parse_args())
    input_path = args['input']
    threshold = args['threshold']
    initial_segment, final_segment = args['initial_segment'], args['final_segment']
    turns_annotation_path = args['beh']

    # input_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/skeleton_spline_K_signed_avg.csv"
    # threshold = 0.1
    # initial_segment, final_segment = 10, 90

    df = pd.read_csv(input_path, header=None)
    df.fillna(0, inplace=True)  # alternative change nans to zeros
    features = np.arange(initial_segment, final_segment)  # Separating out the features (starting bodypart, ending bodypart),a dd to config yaml
    data = df.loc[:, features].values

    signed_curvature = data.sum(axis=1)
    # add a column in the dataframe which contains 1 if another column is higher than 0.05, -1 if lower than -0.05, and 0 if in between -0.5 and 0.5
    new_df = pd.DataFrame()
    new_df['turn'] = np.where(signed_curvature > threshold, 1, np.where(signed_curvature < -threshold, -1, 0))

    turns_df = pd.DataFrame(new_df['turn'])
    turns_df.to_csv(turns_annotation_path)


