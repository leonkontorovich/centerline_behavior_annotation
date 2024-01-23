# import pckgs
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import pickle
import numpy as np
import matplotlib.pyplot as plt


def make_pca(df, inital_segment, end_segment, n_components):
    """
    Perform PCA analysis on a dataframe, specifying the start and end in the dataframe
    #TODO: Probably the dataframe should be curated outside this function
    :param df: dataframe without Nans
    :param inital_segment: int, initial segment
    :param end_segment: int, end segment
    :param n_components: number of PC components
    :return:
    pca, pca object
    principal_components, principal components
    """

    features = np.arange(inital_segment,
                         end_segment)  # Separating out the features (starting bodypart, ending bodypart)
    data = df.loc[:, features].values
    # scale data
    data = StandardScaler().fit_transform(data)
    # print('data shape: ', data.shape)

    # PCA
    pca = PCA(n_components=n_components)
    principal_components = pca.fit_transform(data)

    return pca, principal_components


def concatenate_dataframes(dataframe_path_list: list):
    """
    Concatenate dataframes from a list of dataframe paths
    :param dataframe_path_list:
    :return: concatenated_df
    """
    dfs = (pd.read_csv(p, encoding='utf8', header=None) for p in dataframe_path_list)
    concatenated_df = pd.concat(dfs)
    return concatenated_df


def pca_transform_data(pca_path, data):
    pca = pickle.load(open(pca_path, 'rb'))
    principalComponents = pca.transform(data)
    print(principalComponents.shape)
    principalDf = pd.DataFrame(data=principalComponents, columns=['PC1', 'PC2', 'PC3', 'PC4', 'PC5'])
    return principalDf


if __name__ == "__main__":
    import os
    from datetime import datetime

    # variables
    spline_path='/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/merged_skeleton_spline_K_signed.csv'
    df = pd.read_csv(spline_path, header = None)
    df.fillna(0, inplace=True)
    initial_segment, end_segment = 30, 80
    n_components = 5
    #output folder
    output_folder = '/Volumes/scratch/neurobiology/zimmer/ulises/code/curvature/curvature/models/'


    #do PCA
    pca, principal_components = make_pca(df, initial_segment, end_segment, n_components)

    # save principal components
    columns = ['PC' + str(i) for i in range(1, n_components + 1)]
    principal_df = pd.DataFrame(data=principal_components, columns=columns)
    principal_df.to_csv(os.path.join(output_folder, 'principal_components.csv'), index=False)

    # save pca object
    date_string=datetime.now().strftime("%H%M_%Y%m%d")
    print(date_string)
    pca_path = os.path.join(output_folder,
                            date_string+"_eigenworm_PCA_bodypart_" + str(initial_segment) + "_to_" + str(end_segment) + ".pkl")
    pickle.dump(pca, open(pca_path, "wb"))
    print('done')
