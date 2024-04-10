# This script was written so that it matches the current snakemake pipeline with files as inputs an ouputs
# If you want to run it per folder there is the annotate_behaviour.py file
import argparse
import numpy as np
import pandas as pd
import sys
from centerline_behavior_annotation.curvature.src.annotate_reversals import \
    extract_vectors_from_PC_df, calculate_cross_product, binarize_cross_product
from centerline_behavior_annotation.curvature.src.make_PCA import pca_transform_data

def main(arg_list=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--i_spline_path', help='input path', required=True)
    parser.add_argument('-pca', '--pca_model_path', help='path to the PCA model', required=True)
    parser.add_argument('-i_s', '--initial_segment', type=float, help='initial segment to calculate PCA', required=True)
    parser.add_argument('-f_s', '--final_segment', type=float, help='final segment to calculate PCA', required=True)
    parser.add_argument('-win', '--average_window', type=int, help='average_window', required=True)
    parser.add_argument('-o_bh', '--o_beh', help='path to save the behavioural output', required=True)
    parser.add_argument('-o_pc', '--o_pc', help='path to save the PC components', required=True)
    parser.add_argument('-t', '--thresholds', type=float, nargs=2, help='Input two thresholds separated by space, e.g., -t 20.0 21.0', required=False)

    #args = vars(parser.parse_args())
    args = vars(parser.parse_args(arg_list))
    spline_path = args['i_spline_path']
    pca_path = args['pca_model_path']
    initial_segment = args['initial_segment']
    final_segment = args['final_segment']
    average_window = args['average_window']
    beh_annotation_path = args['o_beh']
    pc_components_path = args['o_pc']

    # threshhold for binarisation of reverse and forward
    thresholds = tuple(args.thresholds) if args.thresholds else (0.0, 0.0)


    features = np.arange(initial_segment, final_segment)
    # print("average window and features are being hard coded, with the following values")
    # print("average window: ", average_window)
    # print("features for PC: ", features)

    df = pd.read_csv(spline_path, header=None)
    df.fillna(0, inplace=True)  # alternative change nans to zeros

    # Separating out the features (starting bodypart, ending bodypart)
    data = df.loc[:, features].values
    principal_components_df = pca_transform_data(pca_path, data)
    # save PCs
    principal_components_df.to_csv(pc_components_path, index=False)

    pc1_pc2_df = extract_vectors_from_PC_df(principal_components_df, avg_win=average_window)
    cross_product_df = calculate_cross_product(pc1_pc2_df)

    # Does cross product result in the per convention accepted sign? (cp<0==rev, cp>0==fwd?)
    # if not, flip the sign
    #cross_product_df = - cross_product_df

    values_arr = binarize_cross_product(cross_product_df, thresholds)
    values_df = pd.DataFrame(values_arr)
    values_df.to_csv(beh_annotation_path)


if __name__ == "__main__":
    main(sys.argv[1:])
