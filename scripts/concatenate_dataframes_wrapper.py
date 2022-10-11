if __name__ == "__main__":
    import argparse
    import glob
    import os
    from curvature.src.make_PCA import *

    ###############
    ## IMPORTANT!##
    print("Do not use this code to reformat. To reformat the files there is another function: https://github.com/Zimmer-lab/centerline/blob/master/centerline/dev/reformat_skeleton_files.py")
    ## IMPORTANT!##
    ###############

    main_path='/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20220729/20220729_12ms/data/'
    dataframe_path_list = glob.glob(os.path.join(main_path, '*worm*/*BH/*skeleton_spline_K.csv'))

    #print(dataframe_path_list)

    concatenated_dataframe = concatenate_dataframes(dataframe_path_list)

    output_path = '/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20220729/20220729_12ms/analysis/merged_skeleton_spline_K.csv'
    #very important to have index and header to False!
    concatenated_dataframe.to_csv(output_path, index=False, header=False)
