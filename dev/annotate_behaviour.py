#The functions here should help generating behaviour annotations based on PCA (and other parameters)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

#make PCA from skeleton spline file
def make_pca(df, inital_segment, end_segment, n_components):
    """"
    calculates PCA from dataframe
    Parameters:
        df, nans need to be removed before hand
        inital_segment, initial segment of the worm body from where to do PCA
        end_segment, end segment of the worm body
        n_components, int
        number of components
    TODO: At the moment the columns names are hard coded and would crash with n_components!=5
    """
    #df.fillna(0, inplace=True)  # alternative change nans to zeros
    features = np.arange(inital_segment, end_segment)  # Separating out the features (starting bodypart, ending bodypart)
    data = df.loc[:, features].values
    data = StandardScaler().fit_transform(data)
    print('data shape: ', data.shape)

    # PCA
    pca = PCA(n_components=n_components)
    principalComponents = pca.fit_transform(data)
    print(principalComponents.shape)
    principalDf = pd.DataFrame(data=principalComponents, columns=['PC1', 'PC2', 'PC3', 'PC4', 'PC5'])
    return principalDf

#extract vectors from PC space
def extract_vectors_from_PC_df(df, avg_win):
    """
    extracts PC1 and PC2 from PC dataframe (principalDf), averages them, and writes them in a new dataframe

    """
    x = df.loc[:, 'PC1'].rolling(window=avg_win, center=True).mean()
    y = df.loc[:, 'PC2'].rolling(window=avg_win, center=True).mean()
    frame = {'X': x, 'Y': y}
    pc1_pc2_df = pd.DataFrame(data=frame)

    return pc1_pc2_df

#calculate cross product
def calculate_cross_product(pc1_pc2_df):
    """
    calcualtes the cross product from the vectors in X and Y in the pc1_pc2_df
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
    # simple binarization of cross product
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
#generate pandas dataframe or vector or wahtever with Forward and Reversal annotation

#Further behavioural annotation:
    #Turns and Dorsal Turns, Ventral Turns

if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--i_path', help='input path', required=True)
    args = vars(parser.parse_args())
    main_path = args['i_path']


    kymo_path = os.path.join(main_path, 'skeleton_spline_K.csv')
    print(kymo_path)

    df = pd.read_csv(kymo_path, header=None)
    df.fillna(0, inplace=True)
    initial_segment, end_segment, n_components = 30, 80, 5

    principalDf = make_pca(df, initial_segment, end_segment, n_components)
    pc1_pc2_df = extract_vectors_from_PC_df(principalDf, avg_win=167)
    cross_product_df = calculate_cross_product(pc1_pc2_df)

    values_arr = binarize_cross_product(cross_product_df)
    values_df = pd.DataFrame(values_arr)
    values_df.to_csv(os.path.join(main_path, 'beh_annotation.csv'))

    # Plotting part

    # fig, ax = plt.subplots(figsize=(10, 2))
    # ax.imshow(values_arr.reshape(1, -1), origin="upper", cmap='seismic', aspect=10000, vmin=-0.00005, vmax=0.00005)
    # ax.set_axis_off()
    # plt.show()
    #
    # fig2, axes = plt.subplots(nrows=3, figsize=(10, 2), sharex=True)
    # axes[0].imshow(df.T, origin="upper", cmap='seismic', extent=[0, df.shape[0], df.shape[1], 0], aspect=10,
    #             vmin=-0.06, vmax=0.06)
    #
    # pc1_pc2_df.plot(ax=axes[1])
    # axes[2].imshow(values_arr.reshape(1, -1), origin="upper", cmap='seismic', aspect=1000, vmin=-0.00005, vmax=0.00005)
    # plt.show()
