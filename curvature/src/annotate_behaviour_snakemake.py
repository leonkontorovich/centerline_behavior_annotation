# This script was written so that it matches the current snakemake pipeline with files as inputs an ouputs
# If you want to run it per folder there is the annotate_behaviour.py file


if __name__ == "__main__":
    import argparse
    import pandas as pd
    import numpy as np
    from curvature.src.make_PCA import *
    from curvature.src.annotate_behaviour import *

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--i_spline_path', help='input path', required=True)
    parser.add_argument('-pca', '--pca_model_path', help='path to the PCA model', required=True)
    parser.add_argument('-o_bh', '--o_beh', help='path to save the behavioural output', required=True)
    parser.add_argument('-o_pc', '--o_pc', help='path to save the PC components', required=True)

    args = vars(parser.parse_args())
    spline_path = args['i_spline_path']
    pca_path = args['pca_model_path']
    beh_annotation_path = args['o_beh']
    pc_components_path = args['o_pc']

    # TODO: This should not be hard coded
    average_window = 167
    features = np.arange(30, 80)

    df = pd.read_csv(spline_path, header=None)
    df.fillna(0, inplace=True)  # alternative change nans to zeros

    # Separating out the features (starting bodypart, ending bodypart)
    data = df.loc[:, features].values
    principal_components_df = pca_transform_data(pca_path, data)
    # save PCs?
    principal_components_df.to_csv(pc_components_path, index=False)

    pc1_pc2_df = extract_vectors_from_PC_df(principal_components_df, avg_win=average_window)
    cross_product_df = calculate_cross_product(pc1_pc2_df)

    values_arr = binarize_cross_product(cross_product_df)
    values_df = pd.DataFrame(values_arr)
    values_df.to_csv(beh_annotation_path)
