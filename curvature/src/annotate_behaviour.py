#The functions here should help generating behaviour annotations based on PCA (and other parameters)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

#make PCA from skeleton spline file

#extract vectors from PC space
def extract_vectors_from_PC_df(df, avg_win):
    """
    extracts PC1 and PC2 from PC dataframe (principalDf), averages them, and writes them in a new dataframe
    #TODO: delete. pc1_df=df.loc[:,'PC1'].rolling(window=avg_window, center=True).mean() does the job. Needs to be combined with the TODO from calculate_cross_product()
    """
    x = df.loc[:, 'PC1'].rolling(window=avg_win, center=True).mean()
    y = df.loc[:, 'PC2'].rolling(window=avg_win, center=True).mean()
    frame = {'X': x, 'Y': y}
    pc1_pc2_df = pd.DataFrame(data=frame)

    return pc1_pc2_df

#calculate cross product
def calculate_cross_product(pc1_pc2_df):
    """
    calcualte the cross product from the vectors in X and Y in the pc1_pc2_df
    #TODO: take as input two separate df (or vectors)
    """

    # create empty array where each cross product value will be appended
    ra = [np.array(np.nan)]  # before was np.nan
    for i, row in enumerate(pc1_pc2_df.iterrows()):
        if i == len(pc1_pc2_df) - 1: continue

        vector_a=[pc1_pc2_df['X'].values[i], pc1_pc2_df['Y'].values[i]]
        vector_b=[pc1_pc2_df['X'].values[i + 1], pc1_pc2_df['Y'].values[i + 1]]

        # calculate cross product
        r = np.cross(vector_a,vector_b)

        ra.append(r)

    cross_product_df = pd.DataFrame()

    cross_product_df['Cross_Product'] = ra

    return cross_product_df


def binarize_cross_product(cross_product_df):
    """"Binarize cross product dataframe"""
    values = [float(value) for value in cross_product_df['Cross_Product'].values]
    values_arr = np.array(values)
    # simple binarization of cross product, output will depend on model (?),
    values_arr[values_arr > 0] = 1
    values_arr[values_arr < 0] = -1

    return values_arr


def ethogram_figure(kymogram_df, ethogram_df):
    """
    Make an ethogram figure with the kymogram
    """
    fig = plt.figure(dpi=150, figsize=(100,0.5))#, dpi=200
    fig.tight_layout()
    plt.subplots_adjust(left=0, bottom=0, wspace = 0, hspace = 0)
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, (2))
    ax1.imshow(ethogram_df.values.T, origin="upper",cmap='seismic',  vmin=-0.00005, vmax=0.00005, aspect=20*100) #
    ax1.set_axis_off()
    ax2.imshow(kymogram_df.T, origin="upper", cmap='seismic', extent=[0, kymogram_df.shape[0], kymogram_df.shape[1], 0], vmin=-0.06, vmax=0.06, aspect=20)
    
    return fig

def rename_beh_annotation(df, rename_dict):
    """
    rename from -1,1 to 'reversal, 'forward' with a dictionary
    """
    renamed_df=df #modify
    return renamed_df


#generate pandas dataframe or vector or wahtever with Forward and Reversal annotation

#Further behavioural annotation:
    #Turns and Dorsal Turns, Ventral Turns

if __name__ == "__main__":
    import argparse
    import os
    import pandas as pd
    import numpy as np
    from curvature.src.make_PCA import *

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--i_path', help='input path', required=True)
    parser.add_argument('-pca', '--pca_model_path', help='path tot he PCA model', required=True)

    average_window=167
    features = np.arange(30, 80) # Separating out the features (starting bodypart, ending bodypart)
    print("average window and features are being hard coded, with the following values")
    print("average window: ", average_window)
    print("features for PC: ", features)


    args = vars(parser.parse_args())
    main_path = args['i_path']
    pca_path = args['pca_model_path']


    df = pd.read_csv(os.path.join(main_path, 'skeleton_spline_K.csv'), header=None)
    df.fillna(0, inplace=True)  # alternative change nans to zeros
    data = df.loc[:, features].values
    principal_components_df = pca_transform_data(pca_path, data)
    # save PCs?
    principal_components_df.to_csv(os.path.join(main_path, 'principal_components.csv'), index=False)

    pc1_pc2_df = extract_vectors_from_PC_df(principal_components_df, avg_win=average_window)
    cross_product_df = calculate_cross_product(pc1_pc2_df)

    values_arr = binarize_cross_product(cross_product_df)
    values_df = pd.DataFrame(values_arr)
    values_df.to_csv(os.path.join(main_path, 'beh_annotation.csv'))
