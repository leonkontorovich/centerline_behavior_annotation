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
        df
        inital_segment
        end_segment
        n_components

    """
    df.fillna(0, inplace=True)  # alternative change nans to zeros
    features = np.arange(inital_segment, end_segment)  # Separating out the features (starting bodypart, ending bodypart)
    data = df.loc[:, features].values
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
def calculate_cross_product(cross_product_df):
    """
    calcualtes the cross product from the vectors in X and Y in the cross_product_df
    """


    ra = [np.array(np.nan)]  # before was np.nan
    for i, row in enumerate(cross_product_df.iterrows()):
        if i == len(cross_product_df) - 1: continue

        vector_a=[cross_product_df['X'].values[i], cross_product_df['Y'].values[i]]
        vector_b=[cross_product_df['X'].values[i + 1], cross_product_df['Y'].values[i + 1]]
        r = np.cross(vector_a,vector_b)
        ra.append(r)

    cross_product_df['Cross Product'] = ra
    return cross_product_df


#smoothen cross product

#binarize cross product

#generate pandas dataframe or vector or wahtever with Forward and Reversal annotation

#Further behavioural annotation:
    #Turns and Dorsal Turns, Ventral Turns


#path='/Volumes/groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/skeleton_after_new_unet/2020-07-01_18-36-25_control_worm6_spline_K.csv'

# has no reversals path='/groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/all_good_skeleton/2020-06-30_18-17-47_chemotaxis_worm5_spline_K.csv'
# df=pd.read_csv(path, header=None)
# inital_segment, end_segment, n_components = 30, 90, 5
# principalDf=make_pca(df, inital_segment, end_segment, n_components)
#
# cross_product_df=extract_vectors_from_PC_df(principalDf,avg_win=16)
# #calculate cross product
# cross_product_df=calculate_cross_product(cross_product_df)
#
# values = [float(value) for value in cross_product_df['Cross Product'].values]
#
#
# values_arr=np.array(values)
#
# fig, ax =plt.subplots(figsize=(40,2))
# ax.imshow(values_arr.reshape(1,-1),origin="upper",cmap='seismic', aspect=10000, vmin=-0.00005, vmax=0.00005)
# ax.set_axis_off()
# # fig, ax2 =plt.subplots(figsize=(40,2))
# # ax2.plot(values)
# plt.show()