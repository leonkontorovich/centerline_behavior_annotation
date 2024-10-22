# Import all required packages
import csv
import itertools
import math
import numpy as np
import pandas as pd
import skan
from imutils import MicroscopeDataReader
import dask.array as da
from skan.csr import skeleton_to_csgraph
from skimage.morphology import skeletonize
from centerline_behavior_annotation.centerline.src.make_skeleton import make_skeleton
import pickle
import argparse
import sys
import os
import tables
import matplotlib.pyplot as plt

if skan.__version__ != '0.9':
    print('This code was written to work with skan version 0.9. You have skan version ', skan.__version__)


def load_bodypart_coords_from_DLC(dlc_df, bodypart, downsample_factor):
    scorer = dlc_df.columns.get_level_values(0)[0]
    bodypart_coords = ((dlc_df[scorer][bodypart]['x'].values) * downsample_factor,
                       (dlc_df[scorer][bodypart]['y'].values) * downsample_factor)
    return bodypart_coords


def calculate_distances(head_coords, tail_coords, candidate_coords):
    """Calculate distances with explicit float64 precision"""
    print(f"\nCalculating distances:")
    print(f"Head coords: {head_coords}")
    print(f"Tail coords: {tail_coords}")
    print(f"Number of candidate coords: {len(candidate_coords)}")

    # Create DataFrame with explicit float64 dtype
    df = pd.DataFrame(columns=[
        'edge_x_coords', 'edge_y_coords',
        'head_x', 'head_y', 'tail_x', 'tail_y',
        'dist_edge_to_head', 'dist_edge_to_tail'
    ]).astype({col: 'float64' for col in [
        'edge_x_coords', 'edge_y_coords',
        'head_x', 'head_y', 'tail_x', 'tail_y',
        'dist_edge_to_head', 'dist_edge_to_tail'
    ]})

    for i, (x, y) in enumerate(candidate_coords):
        # Convert all values to float64
        x = np.float64(x)
        y = np.float64(y)
        head_x = np.float64(head_coords[0])
        head_y = np.float64(head_coords[1])
        tail_x = np.float64(tail_coords[0])
        tail_y = np.float64(tail_coords[1])

        # Calculate distances with float64 precision
        dist_head = np.float64(math.hypot(x - head_x, y - head_y))
        dist_tail = np.float64(math.hypot(x - tail_x, y - tail_y))

        # Store in DataFrame
        df.loc[i] = [x, y, head_x, head_y, tail_x, tail_y, dist_head, dist_tail]

        print(f"\nEndpoint {i} ({x}, {y}):")
        print(f"Distance to head: {dist_head:.4f}")
        print(f"Distance to tail: {dist_tail:.4f}")

    print("\nDataFrame dtypes:")
    print(df.dtypes)
    return df


def cartesian_product_sum(list1, list2):
    """Calculate cartesian product with explicit float handling"""
    print("\nCalculating cartesian product:")

    # Convert input lists to float64 Series
    list1 = pd.Series(list1, dtype='float64')
    list2 = pd.Series(list2, dtype='float64')

    print("Head distances:", list1.values)
    print("Tail distances:", list2.values)

    df = pd.DataFrame(columns=['value1', 'value2', 'value_sum'], dtype='float64')

    for i, (value1, value2) in enumerate(itertools.product(list1, list2)):
        value1 = np.float64(value1)
        value2 = np.float64(value2)
        value_sum = np.float64(value1 + value2)

        df.loc[i] = [value1, value2, value_sum]
        print(f"\nCombination {i}:")
        print(f"Head dist: {value1:.4f}, Tail dist: {value2:.4f}, Sum: {value_sum:.4f}")

    return df


def get_skeleton_points(skel, number_of_neighbors):
    if skel.size == 0 or np.all(skel == 0):
        print("Skeleton is empty or has no foreground pixels")
        skel_points_coords = np.array([[np.nan, np.nan]])
    else:
        try:
            pixel_graph, coordinates, degrees = skeleton_to_csgraph(skel)
            print("Degrees calculated")
            skel_points_coords = list(zip(*np.where(degrees == number_of_neighbors)))
            if not skel_points_coords:
                skel_points_coords = np.array([[np.nan, np.nan]])
            print(f"Found {len(skel_points_coords)} skeleton points with {number_of_neighbors} neighbors")
            print(f"Coordinates: {skel_points_coords}")
        except ValueError as e:
            print(f"Error in skeleton_to_csgraph: {e}")
            skel_points_coords = np.array([[np.nan, np.nan]])
    return skel_points_coords


def assign_head_and_tail_to_coords(head_coords, tail_coords, candidate_coords):
    """Debug version with print statements"""
    print("\nAssigning head and tail coordinates:")
    print(f"Original head coords: {head_coords}")
    print(f"Original tail coords: {tail_coords}")
    print(f"Number of candidate coordinates: {len(candidate_coords)}")

    df_distance = calculate_distances(head_coords, tail_coords, candidate_coords)
    df_cartesian_product = cartesian_product_sum(
        df_distance.loc[:, 'dist_edge_to_head'].astype('float64'),
        df_distance.loc[:, 'dist_edge_to_tail'].astype('float64')
    )

    # Exclude overlapping distances
    number_of_edges = len(candidate_coords)
    index_to_exclude = np.arange(0, len(df_cartesian_product), number_of_edges + 1)
    df_cartesian_product.loc[index_to_exclude, 'value_sum'] = np.nan

    print("\nAfter excluding overlapping distances:")
    print(df_cartesian_product)

    min_of_cartesian_product = df_cartesian_product['value_sum'].min()
    print(f"\nMinimum sum found: {min_of_cartesian_product}")

    try:
        # Head Part
        optimal_distance_head = df_cartesian_product['value1'][
            df_cartesian_product['value_sum'] == min_of_cartesian_product]
        print(f"Optimal head distance: {optimal_distance_head.values[0]}")

        head_row = df_distance[df_distance['dist_edge_to_head'] == optimal_distance_head.values[0]]
        skel_head_coords = (int(head_row['edge_x_coords'].values[0]),
                            int(head_row['edge_y_coords'].values[0]))

        # Tail Part
        optimal_distance_tail = df_cartesian_product['value2'][
            df_cartesian_product['value_sum'] == min_of_cartesian_product]
        print(f"Optimal tail distance: {optimal_distance_tail.values[0]}")

        tail_row = df_distance[df_distance['dist_edge_to_tail'] == optimal_distance_tail.values[0]]
        skel_tail_coords = (int(tail_row['edge_x_coords'].values[0]),
                            int(tail_row['edge_y_coords'].values[0]))

        print(f"\nSelected coordinates:")
        print(f"Head: {skel_head_coords}")
        print(f"Tail: {skel_tail_coords}")

    except Exception as e:
        print(f"Error in coordinate assignment: {e}")
        skel_head_coords = (np.nan, np.nan)
        skel_tail_coords = (np.nan, np.nan)

    return skel_head_coords, skel_tail_coords


def head_and_tail_correction_from_img(img, number_of_neighbors, head_coords, tail_coords, fill_with_DLC: bool = True):
    """Debug version with print statements"""
    print("\nProcessing image for head/tail correction:")
    print(f"Original head coords: {head_coords}")
    print(f"Original tail coords: {tail_coords}")

    skel = skeletonize(img / 255)

    if not skel.any():
        print("No skeleton found")
        if fill_with_DLC:
            return head_coords, tail_coords
        return (np.nan, np.nan), (np.nan, np.nan)

    edge_coords = get_skeleton_points(skel, number_of_neighbors)

    if len(edge_coords) < 2:
        print(f"Not enough endpoints found: {len(edge_coords)}")
        if fill_with_DLC:
            return head_coords, tail_coords
        return (np.nan, np.nan), (np.nan, np.nan)

    skel_head, skel_tail = assign_head_and_tail_to_coords(head_coords, tail_coords, edge_coords)

    print("\nFinal coordinates:")
    print(f"Original head: {head_coords} -> New head: {skel_head}")
    print(f"Original tail: {tail_coords} -> New tail: {skel_tail}")

    return skel_head, skel_tail


def head_and_tail_wrapper(tiff_path: str, hdf5_dlc_path: str, output_path: str, nose, tail, num_splines=100,
                          number_of_neighbors=1,
                          fill_with_DLC=True, downsample_factor=1, min_worm_lenght=300):
    """
    wrapper to create corrected head and tail coordinates AND skeleton.
    # TODO Should be merged with the scripts make_skeleton.py files like make_skeleton_cluster_from_csv.py etc
    # TODO Add Spline number as input to the function
    Parameters:
    ------------
    :param tiff_path:
    :param hdf5_dlc_path:
    :param output_path:
    :param number_of_neighbors:
    :param fill_with_DLC:
    Returns:
    ------------
    :return:
    """
    # load DLC head and tail coordinates
    df = pd.read_hdf(hdf5_dlc_path)

    head_coords = load_bodypart_coords_from_DLC(df, nose, downsample_factor)  # TODO: bodyparts should not be hardcoded
    tail_coords = load_bodypart_coords_from_DLC(df, tail, downsample_factor)

    # create csv objects
    csvfile_corrected_head = open(output_path + 'skeleton_corrected_head_coords.csv', 'w', newline='')
    csv_writer_head = csv.writer(csvfile_corrected_head)

    csvfile_corrected_tail = open(output_path + 'skeleton_corrected_tail_coords.csv', 'w', newline='')
    csv_writer_tail = csv.writer(csvfile_corrected_tail)

    csvfilePathX = open(output_path + 'skeleton_skeleton_X_coords.csv', 'w', newline='')
    csv_writerPathX = csv.writer(csvfilePathX)

    csvfilePathY = open(output_path + 'skeleton_skeleton_Y_coords.csv', 'w', newline='')
    csv_writerPathY = csv.writer(csvfilePathY)

    csvfileX = open(output_path + 'skeleton_spline_X_coords.csv', 'w', newline='')
    csv_writerX = csv.writer(csvfileX)

    csvfileY = open(output_path + 'skeleton_spline_Y_coords.csv', 'w', newline='')
    csv_writerY = csv.writer(csvfileY)

    csvfileK = open(output_path + 'skeleton_spline_K.csv', 'w', newline='')
    csv_writerK = csv.writer(csvfileK)

    # iterate over pages of the tiff file
    reader_obj_binary = MicroscopeDataReader(tiff_path, as_raw_tiff=True, raw_tiff_num_slices=1)
    tif = da.squeeze(reader_obj_binary.dask_array)
    for idx, img in enumerate(tif):
        print(idx)
        img = np.array(img)
        # if idx%50==0:
        #     print(idx, 'ha')

        # access the head and tail coordinates of the frame
        head_coords_i = (int(head_coords[1][idx]), int(head_coords[0][idx]))
        tail_coords_i = (int(tail_coords[1][idx]), int(tail_coords[0][idx]))

        skel_head, skel_tail = head_and_tail_correction_from_img(img, number_of_neighbors, head_coords_i,
                                                                 tail_coords_i, fill_with_DLC)


        if np.isnan(skel_head[0]):  # if the skel_head or skel_tail are nan start
            K = np.full(num_splines, np.nan)
            x = np.full(num_splines, np.nan)
            y = np.full(num_splines, np.nan)
            x_new = np.full(num_splines, np.nan)
            y_new = np.full(num_splines, np.nan)
            u = np.nan
            skel_coord = (x, y)
            spline_coord = (x_new, y_new)
        else:
            u, skel_coord, spline_coord, K = make_skeleton(start_point=skel_head, end_point=skel_tail,
                                                           num_splines=num_splines,
                                                           img=img, min_worm_len=min_worm_lenght)

        # write csvs
        csv_writer_head.writerow(skel_head)
        csv_writer_tail.writerow(skel_tail)
        csv_writerPathX.writerow(skel_coord[0])
        csv_writerPathY.writerow(skel_coord[1])
        csv_writerX.writerow(spline_coord[0])
        csv_writerY.writerow(spline_coord[1])
        csv_writerK.writerow(K)

    csvfile_corrected_head.close()
    csvfile_corrected_tail.close()
    csvfilePathX.close()
    csvfilePathY.close()
    csvfileX.close()
    csvfileY.close()
    csvfileK.close()

    return


def load_downsample_factor_from_pickle(tiff_path):
    # Extract the directory path from the TIFF file path
    directory_path = os.path.dirname(tiff_path)

    # Construct the full path to the cfactor.pickle file
    cfactor_pickle_path = os.path.join(directory_path, 'cfactor.pickle')

    # Check if the cfactor.pickle file exists
    if os.path.exists(cfactor_pickle_path):
        print(f"Found cfactor.pickle file at {cfactor_pickle_path}")
        # Load the content of the pickle file
        with open(cfactor_pickle_path, 'rb') as file:
            downsample_factor = pickle.load(file)
            print(f"Loaded downsample factor: {downsample_factor}")
        return downsample_factor
    else:
        # Handle the case where the cfactor.pickle file is not found
        print("cfactor.pickle file not found in the directory.")
        return None  # You can return a specific value or raise an exception if needed


def main(arg_list=None):
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--input_tiff_path', help='input path', required=True)
    parser.add_argument('-h5', '--hdf5_dlc_path', help='hdf5_dlc_path', required=True)
    parser.add_argument('-o', '--output_path', help='output_path', required=True)
    parser.add_argument('-nose', '--nose', type=str, help='string for the nose e.g. nose or head', required=True)
    parser.add_argument('-tail', '--tail', type=str, help='string for the tail', required=True)
    parser.add_argument('-num_splines', '--num_splines', type=int, help='number of splines', required=True)
    parser.add_argument('-n', '--number_of_neighbors', type=int, help='number_of_neighbors', required=False)
    parser.add_argument('-dlc', '--fill_with_DLC', help='fill_with_DLC, 1 True, 0 False', required=False)
    parser.add_argument('-ds', '--downsample', help='downsample_for_DLC, 1 True, 0 False', required=False, default=0)
    parser.add_argument('-mw', '--min_worm_length', type=int, default=300, help='minimum worm length, leave default when not sure', required=False)

    # args = parser.parse_args()
    args = parser.parse_args(arg_list)
    tiff_path = args.input_tiff_path
    hdf5_dlc_path = args.hdf5_dlc_path
    output_path = args.output_path
    nose = args.nose
    tail = args.tail
    num_splines = args.num_splines
    number_of_neighbors = args.number_of_neighbors  # This can be None if not provided
    fill_with_DLC = args.fill_with_DLC == '1'  # Convert '1' or '0' to True or False
    downsample_for_DLC = args.downsample == '1'  # Convert '1' or '0' to True or False, can be none if not provided
    min_worm_lenght = args.min_worm_length

    print('Fill with DLC', fill_with_DLC)
    print('Downsample for DLC:', downsample_for_DLC)

    downsample_factor = 0

    if (downsample_for_DLC == True):
        try:
            downsample_factor = load_downsample_factor_from_pickle(tiff_path)
        except FileNotFoundError:  # Handle the specific exception if the file is not found
            downsample_factor = 1
            print("Pickle File containing downsample factor not found :(")

    print('Parser worked fine, entering function now')
    print("These are the arguments", args)
    head_and_tail_wrapper(tiff_path=tiff_path, hdf5_dlc_path=hdf5_dlc_path, output_path=output_path, nose=nose,
                          tail=tail, num_splines=num_splines, number_of_neighbors=number_of_neighbors,
                          fill_with_DLC=fill_with_DLC, downsample_factor=downsample_factor, min_worm_lenght=min_worm_lenght)
    print("head_and_tail_wrapper worked fine")


# run code locally
if __name__ == '__main__':
    main(sys.argv[1:])  # exclude the script name from the args when called from shell

# assembling:
#
# parser = argh.ArghParser()
# parser.add_commands([head_and_tail_wrapper])
#
# # dispatching:
#
# if __name__ == '__main__':
#     parser.dispatch()

