if __name__ == "__main__":
    import argparse
    import glob
    import os
    from centerline_behavior_annotation.curvature.src.make_PCA import *

    ###############
    ## IMPORTANT!##
    print("Use this code to concatenate. Do not use this code to reformat. To reformat the files there is another function: https://github.com/Zimmer-lab/centerline/blob/master/centerline/dev/reformat_skeleton_files.py")
    ## IMPORTANT!##
    ###############

    #specify list in bash
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataframe_path_list', nargs='+', help='list of paths to dataframes to concatenate')

    args = parser.parse_args()
    dataframe_path_list = args.dataframe_path_list

    #specify list in python
    # main_path='/scratch/neurobiology/zimmer/ulises/wbfm/2022*/data/'
    # dataframe_path_list = glob.glob(os.path.join(main_path, '*worm*/*BH*/*skeleton_spline_K_signed_avg.csv'))

    print("There are ", len(dataframe_path_list), "spline_K_files to concatenate")
    print("These are the files that you will concatenate: ", dataframe_path_list)

    concatenated_dataframe = concatenate_dataframes(dataframe_path_list)

    output_path = '/scratch/neurobiology/zimmer/ulises/wbfm/merged_skeleton_spline_K_signed_avg_cluster.csv'
    #very important to have index and header to False!
    concatenated_dataframe.to_csv(output_path, index=False, header=False)
    print("Done!")
