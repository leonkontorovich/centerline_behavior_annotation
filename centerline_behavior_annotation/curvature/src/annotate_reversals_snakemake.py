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
    parser.add_argument('--upper_threshold', type=float, help='upper threshold', required=False, default=0.0)
    parser.add_argument('--lower_threshold', type=float, help='lower threshold', required=False, default=0.0)

    #args = vars(parser.parse_args())
    args = vars(parser.parse_args(arg_list))
    spline_path = args['i_spline_path']
    pca_path = args['pca_model_path']
    initial_segment = args['initial_segment']
    final_segment = args['final_segment']
    average_window = args['average_window']
    beh_annotation_path = args['o_beh']
    pc_components_path = args['o_pc']
    upper_threshold = args['upper_threshold']
    lower_threshold = args['lower_threshold']

    thresholds = (upper_threshold, lower_threshold)


    features = np.arange(initial_segment, final_segment)
    # print("average window and features are being hard coded, with the following values")
    # print("average window: ", average_window)
    # print("features for PC: ", features)

    df = pd.read_csv(spline_path, header=None)

    # A crop whose curvature table is too narrow has no usable centerline: it is
    # either junk (bubble/debris) or its skeletons were blanked upstream. Slicing
    # `features` out of it raises a pandas KeyError listing 30 missing column
    # labels -- an error that names the symptom and hides the cause, and that
    # takes the whole crop's DAG branch (and its temporal_features.csv) with it.
    #
    # Junk crops are EXPECTED in a population recording, so this is not a
    # pipeline error. Write empty, well-formed outputs and let the analysis-time
    # aliveness gate drop the crop, the way it drops every other inert crop.
    n_cols = df.shape[1]
    if n_cols < final_segment:
        print(f"[annotate_reversals] SKIPPING {spline_path}: curvature table has "
              f"{n_cols} column(s) but segments [{int(initial_segment)},"
              f"{int(final_segment)}) were requested. No usable centerline for "
              f"this crop -- writing empty annotations so the rest of the "
              f"pipeline can proceed.", file=sys.stderr)
        if n_cols and len(df):
            print(f"[annotate_reversals] NOTE: if this is happening on most "
                  f"crops it is not junk data -- check the "
                  f"'[swc] ... min_worm_length_px' line in the run log against "
                  f"your worms' true length in pixels.", file=sys.stderr)
        # Shape matters: downstream readers index these positionally.
        # load_reversal() in extract_temporal_features.py does df.iloc[:, 0], so
        # an index-only CSV would just relocate the crash. Emit one full-length
        # column of NaN -- "not computable", distinct from 0 ("no reversal") --
        # which _fit_length handles and which scores as no-event in the gate.
        n_frames = len(df)
        pd.DataFrame({"PC1": np.full(n_frames, np.nan),
                      "PC2": np.full(n_frames, np.nan)}).to_csv(
            pc_components_path, index=False)
        pd.DataFrame({0: np.full(n_frames, np.nan)}).to_csv(beh_annotation_path)
        return

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
