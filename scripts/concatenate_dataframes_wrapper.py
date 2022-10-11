if __name__ == "__main__":
    import argparse
    import glob
    import os
    from curvature.src.make_PCA import *

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i_K', '--input_spline_K', help='csv file with the spline curvature', required=True)
    parser.add_argument('-i_X', '--input_spline_X', help='csv file with the spline X coords', required=True)
    parser.add_argument('-i_Y', '--input_spline_Y', help='csv file with the spline Y coords', required=True)
    parser.add_argument('-o', '--o_path', help='output path, has t be .csv file', required=True)

    args = vars(parser.parse_args())
    spline_K = args['input_spline_K']
    spline_X = args['input_spline_X']
    spline_Y = args['input_spline_Y']

    o_path = args['o_path']

    #main_path='/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20220729/20220729_12ms/data/'
    #dataframe_path_list = glob.glob(os.path.join(main_path, '*_spline_K.csv'))

    dataframe_path_list = [spline_K,
    spline_X,
    spline_Y]
    print(dataframe_path_list)

    # call the funcgtion
    concatenated_dataframe = concatenate_dataframes(dataframe_path_list)

    #o_path = '/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20220729/20220729_12ms/analysis/merged_skeleton_spline_K.csv'
    #very important to have index and header to False!
    concatenated_dataframe.to_csv(o_path, index=False, header=False)
