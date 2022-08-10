if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--i_path', help='input path', required=True)
    args = vars(parser.parse_args())
    main_path = args['i_path']

    # main_path = '/Users/ulises.rey/local_data/PCA_analysis'

    kymo_path = os.path.join(main_path, 'skeleton_spline_K.csv')
    print(kymo_path)

    df = pd.read_csv(kymo_path)#, header=None)
    df.fillna(0, inplace=True)
    initial_segment, end_segment, n_components = 30, 80, 5

    pca, principalDf = make_pca(df, initial_segment, end_segment, n_components)
    pc1_pc2_df = extract_vectors_from_PC_df(principalDf, avg_win=167)
    cross_product_df = calculate_cross_product(pc1_pc2_df)

    values_arr = binarize_cross_product(cross_product_df)
    values_df = pd.DataFrame(values_arr)
    values_df.to_csv(os.path.join(main_path, 'beh_annotation_single_worm.csv'))