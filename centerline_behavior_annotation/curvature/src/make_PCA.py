import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import pickle
import numpy as np
import os

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

def get_curvature_filelist_from_wbfm_projects(root_folder) -> list:
    """
    get a list of curvature files from the wbfm projects folder
    the code assumes the following structure:
    - root_folder should contain folders with the project names
    -- project_folder_1
    --- behavior
    ---- skeleton_spline_K_signed_avg.csv
    -- project_folder_2
    --- behavior
    ---- skeleton_spline_K_signed_avg.csv

    :param root_folder: path to the folder containing the wbfm projects
    :return: list of curvature files
    """
    curvature_file_list = []

    project_behavior_dirs = [os.path.join(root_folder, folder, 'behavior') for folder in os.listdir(root_folder)]
    project_behavior_dirs = [folder for folder in project_behavior_dirs if os.path.exists(folder)]

    print(f"looking for skeleton_spline_K_signed_avg.csv files in the {len(project_behavior_dirs)} projects")

    # the curvature files are found inside each project folder,
    # inside a behavior folder, and they are called
    # skeleton_spline_K_signed_avg.csv
    for behavior_folder in project_behavior_dirs:
            curvature_file = os.path.join(behavior_folder, 'skeleton_spline_K_signed_avg.csv')
            if os.path.exists(curvature_file):
                curvature_file_list.append(curvature_file)

    print(f"found {len(curvature_file_list)} curvature files in {len(project_behavior_dirs)} projects")

    return curvature_file_list

def filter_curvature_data_zscore(curvature_df: pd.DataFrame, zscore_threshold: float = 3) -> pd.DataFrame:
    """
    filter curvature data based on a Z-score threshold.
    @param curvature_df: dataframe containing the curvature data
    @param zscore_threshold: z-score threshold for filtering
    @return:
    """

    from scipy.stats import zscore

    print(f"filtering curvature data with Z-score threshold of {zscore_threshold}...")
    z_scores = curvature_df.apply(zscore, nan_policy='omit')
    mask = z_scores.abs() > zscore_threshold
    num_filtered = mask.sum().sum()
    filtered_df = curvature_df.mask(mask)
    # logger.debug(f"Validation: {(len(filtered_df) / len(curvature_df)) * 100:.2f}% of original rows retained")
    print(f"in total, {num_filtered} ({num_filtered / curvature_df.size * 100:.5f}%) values were filtered")
    return filtered_df

def interpolate_curvature_data(curvature_df: pd.DataFrame, seg_frac_to_interp: float = 0.1,
                               interp_method: str = "linear") -> pd.DataFrame:
    """
    interpolate curvature data using a specified method.
    :param curvature_df: dataframe containing curvature data
    :param seg_frac_to_interp: fraction of segments to interpolate
    :param interp_method: interpolation method to use: linear, polynomial, etc.
    :return: interpolated dataframe
    """

    seg_limit = round(curvature_df.shape[1] * seg_frac_to_interp)
    print(f"interpolating data, maximum interpolation is set to: {seg_limit}")

    nan_rows = curvature_df.isna().any(axis=1)
    rows_to_interp = curvature_df[nan_rows]

    interpolated = curvature_df.copy()

    for idx in rows_to_interp.index:
        original = interpolated.loc[idx].copy()
        interpolated.loc[idx] = original.interpolate(
            method=interp_method,
            limit=seg_limit,
            limit_direction='both',
            axis=0
        )

    print(f"...in total, {len(rows_to_interp)} ({len(rows_to_interp) / curvature_df.shape[0] * 100:.5f}%)"
          f" frames were interpolated")
    return interpolated


def save_pc_model(pca, output_folder: str, pc_model_name: str = "pca_model") -> None:
    """
    save the PCA model and principal components to a file
    :param pca: PCA object
    :param pc_model_name: name of the PCA model
    :param output_folder: folder to save the model and components
    :return:
    """

    # save the PC model
    pca_filename = os.path.join(output_folder, pc_model_name + ".pkl")
    print(f"saving PC model to {pca_filename}")

    with open(pca_filename, 'wb') as f:
        pickle.dump(pca, f)


def make_pc_model_wrapper(root_folder: str,
                          pc_model_name: str = None,
                          output_folder: str = None,
                          initial_segment: int = 30,
                          end_segment: int = 80,
                          n_components: int = 5,
                          zscore_filter: bool = True):
    """
    wrapper function to make the PC model from curvature data in wbfm projects
    it saves a pickle file with the PCA model and the principal components

    :param root_folder: path to the folder containing the wbfm projects
        expects this folder structure:
            - root_folder should contain folders with the project names
            -- project_folder_1
            --- behavior
            ---- skeleton_spline_K_signed_avg.csv
            -- project_folder_2
            --- behavior
            ---- skeleton_spline_K_signed_avg.csv
    :param pc_model_name: name of the PCA model, defaults to main folder name
    :param output_folder: folder to save the model and components, defaults to root_folder
    :param initial_segment: int, initial segment
    :param end_segment: int, end segment
    :param n_components: number of PC components
    :param zscore_filter: boolean, whether to apply z-score filtering
            it is not necessary to filter the curvature data.
            however, after checking histogram of values, and comparing it seems to not disturb much.
            Itamar: I know from experience it makes the PC model more stable and better in quality
            this is because PC is very sensitive to outliers
    :return:
    """

    if output_folder is None:
        output_folder = root_folder

    # find all curvature files in the wbfm projects
    curvature_files = get_curvature_filelist_from_wbfm_projects(root_folder)

    # concatenate curvature dataframes
    df = concatenate_dataframes(curvature_files)

    if zscore_filter:
        df_filtered = filter_curvature_data_zscore(df)
        df_interpolated = interpolate_curvature_data(df_filtered, seg_frac_to_interp=0.1, interp_method='linear')
    else:
        df_interpolated = df

    # do PCA
    print(f"calculating PC model on data from {len(curvature_files)} files")

    pc_model, _ = make_pca(df_interpolated, initial_segment, end_segment, n_components)

    if pc_model_name is None:
        pc_model_name = f"{os.path.basename(root_folder)}"

    pc_model_name += f"_segments_{initial_segment}_to_{end_segment}_{n_components}_components"

    if zscore_filter:
        pc_model_name += "_zscore_filtered"

    save_pc_model(pc_model, output_folder=output_folder, pc_model_name=pc_model_name)

def pca_transform_data(pca_path, data):
    pca = pickle.load(open(pca_path, 'rb'))
    principalComponents = pca.transform(data)
    print(principalComponents.shape)
    principalDf = pd.DataFrame(data=principalComponents, columns=['PC1', 'PC2', 'PC3', 'PC4', 'PC5'])
    return principalDf


"""
    example manual use of code to produce PC model
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
"""

