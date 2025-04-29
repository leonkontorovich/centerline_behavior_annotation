import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from tqdm import tqdm
import matplotlib.pyplot as plt
# adjust matplotlib tkinter backend
# import matplotlib
# matplotlib.use('TkAgg') #TODO: uncomment when debugging on a local machine

import pickle
import numpy as np
import os

from centerline_behavior_annotation.curvature.src.annotate_reversals import extract_vectors_from_PC_df, calculate_cross_product, binarize_cross_product

def make_pca(df:pd.DataFrame, inital_segment:int, end_segment:int, n_components:int):
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
    explained_variance = pca.explained_variance_ratio_
    print(f"finished building PC model, explained variance: {explained_variance}")

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


def concatenate_dataframes_behavior_specific(dataframe_path_list: list, behavior_specific: str, behavior_file_name: str):
    """
    Concatenate dataframes from a list of dataframe paths only if a specific behavior is true
    :param dataframe_path_list:
     :param behavior_specific: str, name of the behavior, in case you want to make the PCA-model only from
            specific timepoints in a recording. Default is None: the whole recording will be used
    :param behavior_file_name: str, name of the behavior file eg. manual_annotation.csv, has to be located in the same
            folder as the curvature file
    :return: concatenated_df
    """

    if behavior_file_name is None:
        raise ValueError("behavior_file_name cannot be None.")

    dfs = []

    for p in dataframe_path_list:
        try:
            df_new = pd.read_csv(p, encoding='utf8', header=None)

            behavior_path = os.path.join(os.path.dirname(p), behavior_file_name)
            behavior = pd.read_csv(behavior_path, encoding='utf8')

            # Select the specific behavior column
            if behavior_specific not in behavior.columns:
                print(f"Warning: Behavior column '{behavior_specific}' not found in {behavior_path}. Skipping.")
                continue
            behavior_column = behavior[behavior_specific]

            # Check if lengths match
            if len(df_new) != len(behavior_column):
                print(
                    f"Warning: Length mismatch between data ({len(df_new)}) and behavior ({len(behavior_column)}) in {p}. Skipping.")
                continue

            # Now, select only the rows where behavior == 1
            filtered_df = df_new[behavior_column == 1]

            dfs.append(filtered_df)

        except FileNotFoundError as e:
            print(f"Warning: File not found: {p} or its behavior file. Skipping. ({e})")
            continue
        except Exception as e:
            print(f"Warning: Error processing file {p}. Skipping. ({e})")
            continue

    concatenated_df = pd.concat(dfs, ignore_index=True)
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

    :param root_folder: path to the folder containing the wbfm projects, or a list of paths containing folders with
    wbfm projects
    :return: list of curvature files
    """
    # checks if input is one directory or list of directories, if singular directory transforms it into list
    if isinstance(root_folder, str):
        root_folders = [root_folder]
    elif isinstance(root_folder, list):
        root_folders = root_folder
    else:
        raise ValueError("root_folder must be a string or list of strings")

    curvature_file_list = []

    # loop through the list of root folders
    for root in root_folders:
        if not os.path.isdir(root):
            continue

        # loop through projects in root folder
        for project in os.listdir(root):
            behavior_path = os.path.join(root, project, 'behavior')
            curvature_file = os.path.join(behavior_path, 'skeleton_spline_K_signed_avg.csv')

            # add to curvature file to curvature file list
            if os.path.isfile(curvature_file):
                curvature_file_list.append(curvature_file)

    print(f"Found {len(curvature_file_list)} curvature files in {len(curvature_file_list)} projects.")

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
    print(f"interpolating data, maximum frames to interpolate is set to {seg_frac_to_interp}%, meaning {seg_limit} frames")

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


def save_pc_model(pca, output_folder: str, pc_model_name: str = "pca_model") -> str:
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

    return pca_filename

def get_pca_variance_explained_report(pca_path):
    pca = pickle.load(open(pca_path, 'rb'))
    explained_variance = pca.explained_variance_ratio_
    report = "Explained Variance by Principal Component:\n\n"
    for idx, variance in enumerate(explained_variance, start=1):
        report += f"  PC{idx}: {variance:.2%} of total variance\n"
    pc1_pc2_variance = explained_variance[0] + explained_variance[1]
    report += f"\nCombined Variance of PC1 and PC2:\n"
    report += f"  PC1 + PC2: {pc1_pc2_variance:.2%} of total variance\n"
    if pc1_pc2_variance >= 0.5:
        report += "\n✅ The first two principal components explain more than 50% of the variance.\nThe dimensionality reduction is sufficiently good."
    else:
        report += "\n⚠️ Warning: The first two principal components explain less than 50% of the variance.\nConsider reviewing the model or using more components."
    return report

def get_pc_scatter_plot(df:pd.DataFrame, title_name:str=""):
    """
    produce a scatter plot of the first two principal components.
    :param df: dataframe containing the PCA transformed data
    :param title_name: text to add to title
    :return: (fig, ax) matplotlib figure and axes objects
    """

    # make a scatter plot of the first two principal components
    fig, ax = plt.subplots(figsize=(10, 10))
    scatter = ax.scatter(df['PC1'], df['PC2'], c=df.index, cmap='viridis', s=0.5)
    fig.colorbar(scatter, label='Frames')
    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.set_title(f"PCA Scatter Plot\nA clear circle should appear\n{title_name}")

    return fig, ax

def make_pc_model_wrapper(root_folder: str,
                          pc_model_name: str = None,
                          output_folder: str = None,
                          initial_segment: int = 30,
                          end_segment: int = 80,
                          n_components: int = 5,
                          zscore_filter: bool = True,
                          behavior_specific: str = None,
                          behavior_file_name: str = None):
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
    :param n_components: number of PC components. for usual reversal annotation PC1 and 2 are used, and for other things sometimes we used PC3 and 4
    :param zscore_filter: boolean, whether to apply z-score filtering
            it is not necessary to filter the curvature data.
            however, after checking histogram of values, and comparing it seems to not disturb much.
            Itamar: I know from experience it makes the PC model more stable and better in quality
            this is because PC is very sensitive to outliers
<<<<<<< Updated upstream
    :param behavior_specific: str, name of the behavior, in case you want to make the PCA-model only from
            specific timepoints in a recording. Default is None: the whole recording will be used
    :param behavior_file_name: str, name of the behavior file eg. manual_annotation.csv, has to be located in the same
            folder as the curvature file
=======
            the default is to remove any values that are more than 3 standard deviations away from the mean.
    :return:
>>>>>>> Stashed changes
    """

    if output_folder is None:
        output_folder = root_folder

    final_output_folder = os.path.join(output_folder, 'behavior_pca_model')
    os.makedirs(final_output_folder, exist_ok=True)

    # find all curvature files in the wbfm projects
    curvature_files = get_curvature_filelist_from_wbfm_projects(root_folder)

    # concatenate curvature dataframes


    if behavior_specific is None:
        print(f"concatenating curvature files, it will take a while...")
        df = concatenate_dataframes(curvature_files)
    else:
        print(f"concatenating curvature files when behavior {behavior_specific} is True, it will take a while...")
        df = concatenate_dataframes_behavior_specific(curvature_files, behavior_file_name)

#
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

    pc_model_name += f"_segments_{initial_segment}_to_{end_segment}_components_{n_components}"

    if zscore_filter:
        pc_model_name += "_zscore_filtered"

    pca_model_path = save_pc_model(pc_model, output_folder=final_output_folder, pc_model_name=pc_model_name)

    # make quality control reports
    report = get_pca_variance_explained_report(pca_model_path)

    # calculate cross-product of the first two principal components
    cross_product_values = []

    # produce scatter plot of the first two principal components
    for curvature_file in tqdm(curvature_files, desc="producing PCA quality control scatter plots", unit="dataset", total=len(curvature_files)):
        # get the dataset name from the file path
        dataset_name = os.path.basename(os.path.dirname(os.path.dirname(curvature_file)))
        # load data
        data = pd.read_csv(curvature_file, header=None)
        # restrict data to the columns of interest
        data = data.iloc[:, initial_segment:end_segment]
        # find indices of NaN values
        nan_indices = data.index[data.isna().any(axis=1)]
        # replace NaN values with 0
        data = data.fillna(0)
        # transform data using PCA
        df = pca_transform_data(pca_model_path, data)
        # bring back the NaN values, for all columns
        df.loc[nan_indices] = np.nan
        # plot the first two principal-components
        fig, ax = get_pc_scatter_plot(df, dataset_name)
        # save the figure
        scatter_plot_filename = os.path.join(final_output_folder, f"{dataset_name}_PCA_scatter_plot.png")
        fig.savefig(scatter_plot_filename)
        # collect the cross-product values
        pc1_pc2_df = extract_vectors_from_PC_df(df, avg_win=1)
        cross_product_df = calculate_cross_product(pc1_pc2_df)
        # accumulate the cross product values
        cross_product_values += [float(value) for value in cross_product_df['Cross_Product'].values]

    # make histogram of cross-product values
    fig, ax = make_cross_product_histogram(cross_product_values)
    # save the histogram
    histogram_filename = os.path.join(final_output_folder, f"{pc_model_name}_cross_product_histogram.png")
    fig.savefig(histogram_filename)
    print(f"saved histogram of all cross-product values to {histogram_filename}")
    # estimate the directionality of the cross-product values
    report += estimate_cross_product_directionality(cross_product_values)
    # save the quality control report to file
    report_filename = os.path.join(final_output_folder, pc_model_name + "_quality_report.txt")
    with open(report_filename, 'w') as f:
        f.write(report)
    print(f"saved report to {report_filename}")

def pca_transform_data(pca_path, data):
    pca = pickle.load(open(pca_path, 'rb'))
    principalComponents = pca.transform(data)
    print(principalComponents.shape)
    principalDf = pd.DataFrame(data=principalComponents, columns=['PC1', 'PC2', 'PC3', 'PC4', 'PC5'])
    return principalDf



def make_cross_product_histogram(cross_product_values:list, iqr_scalar:float = 3)->tuple:
    """
    make a histogram of the cross-product values
    :param cross_product_values: cross-product value list
    :param iqr_scalar: float, IQR scalar for filtering
    :return: tuple
    """
    # plot histogram of the cross-product values
    fig, ax = plt.subplots(figsize=(10, 10))

    # calculate quantiles and IQR based on absolute values
    abs_cross_product_values = np.abs(cross_product_values)
    q1 = np.nanquantile(abs_cross_product_values, 0.25)
    q3 = np.nanquantile(abs_cross_product_values, 0.75)
    iqr = q3 - q1

    # define bounds based on absolute values
    lower_bound = q1 - iqr_scalar * iqr
    upper_bound = q3 + iqr_scalar * iqr

    # filter original values based on absolute value bounds
    filtered_values = [value for value in cross_product_values if
                       np.abs(value) >= lower_bound and np.abs(value) <= upper_bound]

    #plot histogram of the cross-product values
    ax.hist(filtered_values, bins=50, color='blue', alpha=0.5)
    plt.xlabel('Cross Product Values')
    plt.ylabel('Number of Occurrences')
    plt.title('Histogram of Cross Product Values')
    # add a red-dashed line at the median
    median = np.nanmedian(filtered_values)
    ax.axvline(median, color='red', linestyle='dashed', linewidth=1, label=f"Median(={round(median,4)})")
    ax.axvline(0, color='black', linestyle='dashed', linewidth=1, label="0")
    # add a legend
    plt.legend()
    return fig, ax


def estimate_cross_product_directionality(cross_product_values:list)->str:
    """
    guess the directionality the cross-product values
    :param cross_product_values: list cross-product values
    :return: str, directionality of the cross-product values
    """
    median = round(np.nanmedian(cross_product_values), 4)
    threshold = "< 0" if median > 0 else "> 0"
    report_text = (f"\n===================================================\n"
                   f"Median of cross product values: {median}."
            f"\nAssuming worms are mostly moving forward\n"
            f"use a threshold of {threshold} to annotate reversals.")
    return report_text

# pc_path = r"Z:\neurobiology\zimmer\ItamarLev\feedback_story\WBFM\1per_barlow\1per_barlow_segments_30_to_80_5_components_zscore_filtered.pkl"
# data_path = r"Z:\neurobiology\zimmer\ItamarLev\feedback_story\WBFM\1per_barlow\2024-07-12_15-29_1per_worm1-2024-07-12\behavior\skeleton_spline_K_signed_avg.csv"
# var_explained = get_pca_variance_explained_report(pc_path)
#
# # format the var_explained text to a nice format
#
#


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

