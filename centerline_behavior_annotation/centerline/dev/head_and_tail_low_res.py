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


def load_bodypart_coords_from_DLC(dlc_df, bodypart, downsample_factor):
    """
    Returns the coordinates of the specified bodypart in an array format
    """
    scorer = dlc_df.columns.get_level_values(0)[0]
    bodypart_coords = ((dlc_df[scorer][bodypart]['x'].values) * downsample_factor,
                       (dlc_df[scorer][bodypart]['y'].values) * downsample_factor)
    return bodypart_coords


def calculate_distances(head_coords, tail_coords, candidate_coords):
    """
    Calculate the distances between head and tail coordinates and the candidate coords
    """
    df = pd.DataFrame()
    for i, (x, y) in enumerate(candidate_coords):
        df.loc[i, 'edge_x_coords'] = x
        df.loc[i, 'edge_y_coords'] = y
        df.loc[i, 'head_x'] = head_coords[0]
        df.loc[i, 'head_y'] = head_coords[1]
        df.loc[i, 'tail_x'] = tail_coords[0]
        df.loc[i, 'tail_y'] = tail_coords[1]
        df.loc[i, 'dist_edge_to_head'] = math.hypot(x - head_coords[0], y - head_coords[1])
        df.loc[i, 'dist_edge_to_tail'] = math.hypot(x - tail_coords[0], y - tail_coords[1])
    return df


def get_skeleton_points(skel, number_of_neighbors):
    """
    Returns coordinates of points in the skeleton that have the specified number of neighbors.
    """
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
            print(f"Skeleton points with {number_of_neighbors} neighbors: {skel_points_coords}")
        except ValueError as e:
            print(f"Error in skeleton_to_csgraph: {e}")
            skel_points_coords = np.array([[np.nan, np.nan]])
    return skel_points_coords


def head_and_tail_correction_from_img(img, number_of_neighbors, head_coords, tail_coords, fill_with_DLC: bool = True):
    """
    Adjust head and tail coordinates to nearest skeleton endpoints while maintaining identity
    """
    # Create skeleton
    skel = skeletonize(img / 255)

    # If no skeleton, return based on fill_with_DLC
    if not skel.any():
        if fill_with_DLC:
            return head_coords, tail_coords
        return (np.nan, np.nan), (np.nan, np.nan)

    # Get only endpoint coordinates (points with exactly 1 neighbor)
    endpoint_coords = get_skeleton_points(skel, number_of_neighbors=1)

    # If we don't have at least 2 endpoints, return based on fill_with_DLC
    if len(endpoint_coords) < 2:
        if fill_with_DLC:
            return head_coords, tail_coords
        return (np.nan, np.nan), (np.nan, np.nan)

    try:
        # Calculate distances for all endpoints
        df_distance = calculate_distances(head_coords, tail_coords, endpoint_coords)

        # Find closest endpoint to head
        head_distances = df_distance['dist_edge_to_head']
        closest_to_head_idx = head_distances.idxmin()
        skel_head_coords = (
            int(df_distance.loc[closest_to_head_idx, 'edge_x_coords']),
            int(df_distance.loc[closest_to_head_idx, 'edge_y_coords'])
        )

        # Find closest endpoint to tail
        tail_distances = df_distance['dist_edge_to_tail']
        closest_to_tail_idx = tail_distances.idxmin()
        skel_tail_coords = (
            int(df_distance.loc[closest_to_tail_idx, 'edge_x_coords']),
            int(df_distance.loc[closest_to_tail_idx, 'edge_y_coords'])
        )

        # Optional: Add distance threshold check
        max_adjustment_distance = 50  # adjust this threshold as needed
        if (head_distances[closest_to_head_idx] > max_adjustment_distance or
                tail_distances[closest_to_tail_idx] > max_adjustment_distance):
            if fill_with_DLC:
                return head_coords, tail_coords
            return (np.nan, np.nan), (np.nan, np.nan)

        return skel_head_coords, skel_tail_coords

    except:
        if fill_with_DLC:
            return head_coords, tail_coords
        return (np.nan, np.nan), (np.nan, np.nan)


def head_and_tail_wrapper(tiff_path: str, hdf5_dlc_path: str, output_path: str, nose, tail, num_splines=100,
                          number_of_neighbors=1, fill_with_DLC=True, downsample_factor=1, min_worm_lenght=300):
    """
    Wrapper to create corrected head and tail coordinates AND skeleton.
    """
    # load DLC head and tail coordinates
    df = pd.read_hdf(hdf5_dlc_path)
    head_coords = load_bodypart_coords_from_DLC(df, nose, downsample_factor)
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

        head_coords_i = (int(head_coords[1][idx]), int(head_coords[0][idx]))
        tail_coords_i = (int(tail_coords[1][idx]), int(tail_coords[0][idx]))

        skel_head, skel_tail = head_and_tail_correction_from_img(img, number_of_neighbors, head_coords_i,
                                                                 tail_coords_i, fill_with_DLC)

        if np.isnan(skel_head[0]):
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


def load_downsample_factor_from_pickle(tiff_path):
    directory_path = os.path.dirname(tiff_path)
    cfactor_pickle_path = os.path.join(directory_path, 'cfactor.pickle')

    if os.path.exists(cfactor_pickle_path):
        print(f"Found cfactor.pickle file at {cfactor_pickle_path}")
        with open(cfactor_pickle_path, 'rb') as file:
            downsample_factor = pickle.load(file)
            print(f"Loaded downsample factor: {downsample_factor}")
        return downsample_factor
    else:
        print("cfactor.pickle file not found in the directory.")
        return None


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
    parser.add_argument('-mw', '--min_worm_length', type=int, default=300,
                        help='minimum worm length, leave default when not sure', required=False)

    args = parser.parse_args(arg_list)
    tiff_path = args.input_tiff_path
    hdf5_dlc_path = args.hdf5_dlc_path
    output_path = args.output_path
    nose = args.nose
    tail = args.tail
    num_splines = args.num_splines
    number_of_neighbors = args.number_of_neighbors
    fill_with_DLC = args.fill_with_DLC == '1'
    downsample_for_DLC = args.downsample == '1'
    min_worm_lenght = args.min_worm_length

    print('Fill with DLC', fill_with_DLC)
    print('Downsample for DLC:', downsample_for_DLC)

    downsample_factor = 0
    if (downsample_for_DLC == True):
        try:
            downsample_factor = load_downsample_factor_from_pickle(tiff_path)
        except FileNotFoundError:
            downsample_factor = 1
            print("Pickle File containing downsample factor not found :(")

    print('Parser worked fine, entering function now')
    print("These are the arguments", args)
    head_and_tail_wrapper(tiff_path=tiff_path, hdf5_dlc_path=hdf5_dlc_path, output_path=output_path, nose=nose,
                          tail=tail, num_splines=num_splines, number_of_neighbors=number_of_neighbors,
                          fill_with_DLC=fill_with_DLC, downsample_factor=downsample_factor,
                          min_worm_lenght=min_worm_lenght)
    print("head_and_tail_wrapper worked fine")


if __name__ == '__main__':
    main(sys.argv[1:])