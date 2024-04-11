# This script was written so that it matches the current snakemake pipeline with files as inputs an ouputs
# If you want to run it per folder there is the annotate_behaviour.py file

def main(arg_list):

    import argparse # comment
    import pandas as pd
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument('-input', '--input', help='path to the input', required=True)
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

    print("initial_segment:")
    print(type(initial_segment))
    print(initial_segment)

    print("final_segment:")
    print(type(final_segment))
    print(final_segment)

    print("threshold:")
    print(type(threshold))
    print(threshold)

    # Reading the CSV file with UTF-8 encoding
    df = pd.read_csv(input_path, header=None, encoding='utf-8')

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
    turns_df = pd.DataFrame({'turns': pd.Series(dtype='int')})
    # Compute the conditional values and force the type to int
    turns_df['turns'] = np.where(ventral_curvature > threshold, 1, np.where(dorsal_curvature < -threshold, -1, 0)).astype(int)

    # Writing the DataFrame to a CSV file with UTF-8 encoding
    turns_df.to_csv(turns_annotation_path, encoding='utf-8')

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])