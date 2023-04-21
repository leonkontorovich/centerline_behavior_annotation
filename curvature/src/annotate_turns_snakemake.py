# This script was written so that it matches the current snakemake pipeline with files as inputs an ouputs
# If you want to run it per folder there is the annotate_behaviour.py file


if __name__ == "__main__":
    import argparse # comment
    import pandas as pd
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument('-pc', '--pc', help='path to the PC components', required=True)
    parser.add_argument('-t', '--threshold', help='threshold on the PC3', type=float, required=True)
    parser.add_argument('-bh', '--beh', help='path to the behavioural output', required=True)


    args = vars(parser.parse_args())
    pc_components_path = args['pc']
    threshold = args['threshold']
    turns_annotation_path = args['beh']


    df = pd.read_csv(pc_components_path)

    # add a column in the dataframe which contains 1 if another column is higher than 0.05, -1 if lower than -0.05, and 0 if in between -0.5 and 0.5
    df['turn'] = np.where(df['PC3'] > threshold, 1, np.where(df['PC3'] < -threshold, -1, 0))

    turns_df = pd.DataFrame(df['turn'])
    turns_df.to_csv(turns_annotation_path)
