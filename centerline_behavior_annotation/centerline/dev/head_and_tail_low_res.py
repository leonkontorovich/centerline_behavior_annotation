import argparse
from imutils import MicroscopeDataReader
import dask.array as da
import pandas as pd
from skimage.morphology import skeletonize
import numpy as np
import numpy as np
from skimage.morphology import skeletonize
import networkx as nx
from scipy.interpolate import splprep, splev
from scipy.ndimage import distance_transform_edt
import os

def extract_dlc_coordinates(df_DLC):
    """
    Extract head and tail coordinates from a DeepLabCut DataFrame.

    Parameters:
    -----------
    df_DLC : pandas.DataFrame
        DeepLabCut DataFrame containing tracking data

    Returns:
    --------
    tuple(pandas.DataFrame, pandas.DataFrame)
        Two DataFrames containing the x,y coordinates for head and tail respectively
    """
    scorer = df_DLC.columns.get_level_values(0)[0]

    # Extract head coordinates
    head_dlc = pd.DataFrame({
        'x': df_DLC[scorer]['head']['x'].values,
        'y': df_DLC[scorer]['head']['y'].values
    })

    # Extract tail coordinates
    tail_dlc = pd.DataFrame({
        'x': df_DLC[scorer]['tail']['x'].values,
        'y': df_DLC[scorer]['tail']['y'].values
    })

    return head_dlc, tail_dlc


def skeletonize_frame(frame):
    """
    Process a single binary image frame using skimage's skeletonize.

    Parameters:
        frame: 2D numpy array representing a binary image (height, width)

    Returns:
        2D numpy array of skeletonized image
    """
    # Ensure input is binary and process frame
    binary_frame = (frame > 0).astype(np.bool_)
    return skeletonize(binary_frame).astype(np.uint8) * 255

def find_nearest_skeleton_pixel(skeleton, point):
    """
    Find the nearest skeleton endpoint pixel to the given point.
    Endpoint is defined as a skeleton pixel (True) with exactly 1 neighbor.

    Parameters:
    - skeleton (np.ndarray): Binary skeleton image (True for skeleton, False for background)
    - point (tuple): (y, x) coordinates

    Returns:
    - nearest_endpoint (tuple or None): (y, x) coordinates of the nearest endpoint or None if not found
    """
    y, x = point

    # Check if the point is within the image bounds
    if y < 0 or y >= skeleton.shape[0] or x < 0 or x >= skeleton.shape[1]:
        print("Point is outside the skeleton image bounds.")
        return None

    # If the point is already an endpoint, return it
    if skeleton[y, x]:
        neighbors = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                ny, nx_ = y + dy, x + dx
                if (0 <= ny < skeleton.shape[0] and
                        0 <= nx_ < skeleton.shape[1] and
                        skeleton[ny, nx_]):
                    neighbors += 1
        if neighbors == 1:
            return point

    # Find all endpoints
    endpoints = []
    for y_idx in range(skeleton.shape[0]):
        for x_idx in range(skeleton.shape[1]):
            if not skeleton[y_idx, x_idx]:
                continue
            # Count neighbors
            neighbors = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    ny, nx_ = y_idx + dy, x_idx + dx
                    if (0 <= ny < skeleton.shape[0] and
                            0 <= nx_ < skeleton.shape[1] and
                            skeleton[ny, nx_]):
                        neighbors += 1
            if neighbors == 1:
                endpoints.append((y_idx, x_idx))

    if not endpoints:
        print("No endpoints found in the skeleton.")
        return None

    # Find the nearest endpoint using Euclidean distance
    min_dist = float('inf')
    nearest_endpoint = None

    for endpoint in endpoints:
        dist = np.sqrt((endpoint[0] - y) ** 2 + (endpoint[1] - x) ** 2)
        if dist < min_dist:
            min_dist = dist
            nearest_endpoint = endpoint

    return nearest_endpoint


def compute_shortest_path(mask, start, end, num_splines=100, min_worm_len=0):
    """
    Compute the shortest path between start and end points within the skeletonized mask
    and calculate the curvature along the path.

    Parameters:
    ----------
    mask : np.ndarray
        Binary mask of the structure.
    start : tuple
        Coordinates of the start point (row, col).
    end : tuple
        Coordinates of the end point (row, col).
    num_splines : int
        Number of points to sample along the spline.
    min_worm_len : int
        Minimum length the worm should have. Default is 0.

    Returns:
    -------
    path_coords : np.ndarray
        Array of coordinates along the path with shape (N, 2), where N is the number of points.
    K : np.ndarray
        Curvature values at the sampled spline points with shape (num_splines,).
    """
    # Skeletonize the mask
    skeleton = skeletonize(mask)
    if not np.any(skeleton):
        # Skeleton is empty
        print("Skeleton is empty, no path to compute.")
        return np.array([]), np.array([])

    G = nx.Graph()

    # Add nodes and edges to the graph
    coords = np.column_stack(np.nonzero(skeleton))
    for y, x in coords:
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue  # Skip the center pixel
                ny, nx_ = y + dy, x + dx
                if (0 <= ny < mask.shape[0]) and (0 <= nx_ < mask.shape[1]):
                    if skeleton[ny, nx_]:
                        G.add_edge((y, x), (ny, nx_))

    # Ensure start and end are integers
    start = (int(round(start[0])), int(round(start[1])))
    end = (int(round(end[0])), int(round(end[1])))

    # Check if start and end nodes are in G; if not, find the nearest skeleton pixel
    if start not in G:
        start = find_nearest_skeleton_pixel(skeleton, start)
        if start is None:
            print("Start point is not on the skeleton and no nearby skeleton pixel found.")
            return np.array([]), np.array([])
    if end not in G:
        end = find_nearest_skeleton_pixel(skeleton, end)
        if end is None:
            print("End point is not on the skeleton and no nearby skeleton pixel found.")
            return np.array([]), np.array([])

    # Compute shortest path
    try:
        path = nx.shortest_path(G, source=start, target=end)
        path_coords = np.array(path)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        print("No path found between start and end points.")
        return np.array([]), np.array([])

    # Check if the path length meets the minimum requirements
    if len(path_coords) < max(min_worm_len, 3):
        print("Path too short or insufficient points for curvature calculation.")
        return np.array([]), np.array([])

    # Extract y and x coordinates
    y, x = path_coords[:, 0], path_coords[:, 1]

    # Fit a spline to the path
    try:
        # Parameterize the spline based on the cumulative distance along the path
        distance = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2)
        u = np.concatenate(([0], np.cumsum(distance)))
        if u[-1] == 0:
            print("Total distance is zero, cannot parameterize spline.")
            return np.array([]), np.array([])
        u /= u[-1]  # Normalize to [0, 1]

        # Handle cases where the number of unique points is less than the spline order
        unique_u, unique_indices = np.unique(u, return_index=True)
        x_unique = x[unique_indices]
        y_unique = y[unique_indices]
        if len(unique_u) < 4:
            print("Not enough unique points to fit a cubic spline.")
            return np.array([]), np.array([])

        # Fit spline with smoothing factor s
        tck, _ = splprep([x_unique, y_unique], u=unique_u, s=len(x_unique) / 2, k=3)  # Cubic spline

        # Generate new parameter values for sampling
        u_new = np.linspace(0, 1, num_splines)

        # Evaluate spline at new parameter values
        x_new, y_new = splev(u_new, tck, der=0)

        # Compute first derivatives
        x_der, y_der = splev(u_new, tck, der=1)

        # Compute second derivatives
        x_der2, y_der2 = splev(u_new, tck, der=2)

        # Calculate curvature K
        denominator = (x_der ** 2 + y_der ** 2) ** 1.5
        denominator = np.where(denominator == 0, np.nan, denominator)
        K = (x_der * y_der2 - y_der * x_der2) / denominator

    except Exception as e:
        print(f"Error during spline fitting or curvature calculation: {e}")
        K = np.full(num_splines, np.nan)

    return path_coords, K


def place_skeleton_points_with_endpoints(mask, start_point, end_point, num_points=20):
    """
    Place points along the shortest path between two endpoints within a mask.

    Parameters:
    - mask (np.ndarray): Binary mask of the structure.
    - start_point (tuple): Coordinates of the start point (row, col).
    - end_point (tuple): Coordinates of the end point (row, col).
    - num_points (int): Number of points to place along the path.

    Returns:
    - points (np.ndarray): Array of point coordinates (num_points, 2) in (x, y) order.
    - interp_K (np.ndarray): Interpolated curvature values at the sampled spline points.
    """
    # Ensure the image is binary
    mask = mask > 0

    # Compute the shortest path
    path_coords, K = compute_shortest_path(mask, start_point, end_point)

    # Check if path was found
    if len(path_coords) == 0:
        return np.array([]), np.array([])

    # Extract x and y coordinates
    y_coords, x_coords = path_coords[:, 0], path_coords[:, 1]

    # Compute cumulative distances
    distances = np.sqrt(np.diff(x_coords) ** 2 + np.diff(y_coords) ** 2)
    cumulative_distances = np.insert(np.cumsum(distances), 0, 0)

    # Normalize distances
    total_length = cumulative_distances[-1]
    if total_length == 0:
        print("Total path length is zero, returning the start point repeated.")
        return np.array([path_coords[0]] * num_points), np.full(num_points, np.nan)
    normalized_distances = cumulative_distances / total_length

    # Interpolate points at regular intervals
    desired_distances = np.linspace(0, 1, num_points)
    interp_x = np.interp(desired_distances, normalized_distances, x_coords)
    interp_y = np.interp(desired_distances, normalized_distances, y_coords)

    # Combine interpolated coordinates
    points = np.vstack((interp_x, interp_y)).T  # Shape (num_points, 2)

    # Interpolate curvature values
    if len(K) == 0 or np.all(np.isnan(K)):
        interp_K = np.full(num_points, np.nan)
    else:
        # Since K is sampled at num_splines points uniformly in [0, 1], interpolate based on desired_distances
        interp_K = np.interp(desired_distances, np.linspace(0, 1, len(K)), K)

    return points, interp_K


def assign_skeleton_to_head_tail(skeleton_points, head_coord, tail_coord):
    """
    Assign skeleton points to head and tail by ordering them from head to tail.

    Parameters:
    skeleton_points (np.ndarray): Array of skeleton points (num_points, 2).
    head_coord (tuple): (x, y) coordinate of the head.
    tail_coord (tuple): (x, y) coordinate of the tail.

    Returns:
    np.ndarray: Ordered skeleton points from head to tail.
    """
    if len(skeleton_points) == 0:
        return np.array([])

    first_point = skeleton_points[0]
    last_point = skeleton_points[-1]

    # Compute distances from skeleton endpoints to head and tail
    dist_head_to_first = np.linalg.norm(first_point - head_coord)
    dist_head_to_last = np.linalg.norm(last_point - head_coord)

    # Decide whether to reverse the order
    if dist_head_to_first <= dist_head_to_last:
        ordered_points = skeleton_points
    else:
        ordered_points = skeleton_points[::-1]  # Reverse the order

    return ordered_points


def create_skeleton_dataframes(skeleton_ordered, all_K, num_spline_points):
    """
    Convert ordered skeleton points and curvature data into DataFrames.

    Parameters:
    -----------
    skeleton_ordered : list
        List of numpy arrays containing ordered skeleton points for each frame
    all_K : list
        List of curvature measurements for each frame, can contain None values
    num_spline_points : int
        Number of points along the skeleton spline

    Returns:
    --------
    tuple(pd.DataFrame, pd.DataFrame, pd.DataFrame)
        Three DataFrames containing:
        - x coordinates with columns 'point_1' through 'point_n'
        - y coordinates with columns 'point_1' through 'point_n'
        - curvature values with columns 'point1_angle' through 'pointn_angle'
    """
    # Convert skeleton points to x, y DataFrames
    skeleton_data = np.array(skeleton_ordered)
    x_coords = skeleton_data[:, :, 0]  # Shape: (num_frames, num_points)
    y_coords = skeleton_data[:, :, 1]  # Shape: (num_frames, num_points)

    # Create column names for coordinates
    coord_columns = [f'point_{i + 1}' for i in range(num_spline_points)]

    # Create DataFrames for x and y coordinates
    skeleton_x = pd.DataFrame(x_coords, columns=coord_columns)
    skeleton_y = pd.DataFrame(y_coords, columns=coord_columns)

    # Convert curvature measurements to DataFrame
    angle_columns = [f'point{i + 1}_angle' for i in range(num_spline_points)]

    # Convert each curvature measurement to a list of values or NaNs
    curvature_rows = []
    for k in all_K:
        if k is None:
            curvature_rows.append([np.nan] * num_spline_points)
        else:
            curvature_rows.append(k)

    skeleton_K = pd.DataFrame(curvature_rows, columns=angle_columns)

    return skeleton_x, skeleton_y, skeleton_K


import numpy as np
import pandas as pd


def refine_skeleton_and_curvature_data(skeleton_x, skeleton_y, spline_K, threshold):
    """
    Refines both skeleton and curvature data by:
    1. Removing rows where total skeleton path length is below threshold
    2. Matching NaN patterns between skeleton and curvature data

    Args:
        skeleton_x (pd.DataFrame): DataFrame containing x coordinates
        skeleton_y (pd.DataFrame): DataFrame containing y coordinates
        spline_K (pd.DataFrame): DataFrame containing curvature values
        threshold (float): Minimum total path length threshold

    Returns:
        tuple: (refined_x, refined_y, refined_K) DataFrames with filtered data
    """
    # Create copies to avoid modifying original data
    refined_x = skeleton_x.copy()
    refined_y = skeleton_y.copy()
    refined_K = spline_K.copy()

    # Get the column names dynamically
    point_columns = skeleton_x.columns

    # Loop through each row
    for idx in range(len(refined_x)):
        # Skip if row is already all NaN
        if refined_x.iloc[idx].isna().all() or refined_y.iloc[idx].isna().all():
            refined_x.iloc[idx] = np.nan
            refined_y.iloc[idx] = np.nan
            refined_K.iloc[idx] = np.nan
            continue

        # Calculate total path length for this skeleton
        total_distance = 0

        # Loop through consecutive points
        for i in range(len(point_columns) - 1):
            point1_x = refined_x.iloc[idx][point_columns[i]]
            point1_y = refined_y.iloc[idx][point_columns[i]]
            point2_x = refined_x.iloc[idx][point_columns[i + 1]]
            point2_y = refined_y.iloc[idx][point_columns[i + 1]]

            # Skip if any point is NaN
            if pd.isna(point1_x) or pd.isna(point1_y) or pd.isna(point2_x) or pd.isna(point2_y):
                continue

            # Add distance between these points to total
            distance = np.sqrt((point2_x - point1_x) ** 2 + (point2_y - point1_y) ** 2)
            total_distance += distance

        # If total path length is less than threshold, set row to NaN in all DataFrames
        if total_distance < threshold:
            refined_x.iloc[idx] = np.nan
            refined_y.iloc[idx] = np.nan
            refined_K.iloc[idx] = np.nan

    return refined_x, refined_y, refined_K

def main(arg_list=None):
    parser = argparse.ArgumentParser(description='Process microscope data with DeepLabCut tracking')
    parser.add_argument('--input_binary_mask', type=str, required=True, help='Path to the binary mask input file')
    parser.add_argument('--input_dlc_h5', type=str, required=True, help='Path to the DeepLabCut H5 input file')
    parser.add_argument('--head_annotation', type=str, required=True, help='Name of the head column in DLC data')
    parser.add_argument('--tail_annotation', type=str, required=True, help='Name of the tail column in DLC data')
    parser.add_argument('--number_of_spline', type=int, default=20, help='Number of skeleton elements to fit (default: 20)')
    parser.add_argument('--min_worm_length', type=float, default=60, help='Threshold for skeleton length (default: 60)')
    args = parser.parse_args(arg_list)


    df_DLC = pd.read_hdf(args.input_dlc_h5)
    head_dlc, tail_dlc = extract_dlc_coordinates(df_DLC)



    reader_obj = MicroscopeDataReader(args.input_binary_mask, as_raw_tiff=True, raw_tiff_num_slices=1)
    tif = da.squeeze(reader_obj.dask_array)

    # Initialize lists to store results
    all_skeleton_points = []
    all_K = []

    for i, image in enumerate(tif):

        skeleton_image = skeletonize_frame(image)

        head_x = head_dlc['x'].iloc[i]
        head_y = head_dlc['y'].iloc[i]
        tail_x = tail_dlc['x'].iloc[i]
        tail_y = tail_dlc['y'].iloc[i]

        #round int to pixel values
        head = (int(round(head_y)), int(round(head_x)))
        tail = (int(round(tail_y)), int(round(tail_x)))

        skel_points, K = place_skeleton_points_with_endpoints(skeleton_image, args.head_annotation, args.tail_annotation, num_points=args.number_of_spline)

        if skel_points.size == 0:
            all_skeleton_points.append(None)
            all_K.append(None)
        else:
            all_skeleton_points.append(skel_points)
            all_K.append(K)

    #asign head and tail using dlc
    skeleton_ordered = []

    for i, points in enumerate(all_skeleton_points):
        # Get head and tail positions for this frame
        head = (head_dlc['x'].iloc[i], head_dlc['y'].iloc[i])
        tail = (tail_dlc['x'].iloc[i], tail_dlc['y'].iloc[i])

        if points is None or len(points) == 0:
            # If no points found, fill with NaN
            frame_points = np.full((args.number_of_spline, 2), np.nan)
        else:
            # Order points from head to tail
            frame_points = assign_skeleton_to_head_tail(points, head, tail)

        skeleton_ordered.append(frame_points)

    # Create coordinate and curvature DataFrames
    skeleton_x, skeleton_y, spline_K = create_skeleton_dataframes(skeleton_ordered, all_K, args.number_of_spline)

    refined_x, refined_y, refined_K = refine_skeleton_and_curvature_data(skeleton_x, skeleton_y, spline_K, args.min_worm_length)

    # Get the directory from input_binary_mask path
    output_dir = os.path.dirname(args.input_binary_mask)

    # Save files in the same directory
    refined_x.to_csv(os.path.join(output_dir, "refined_x.csv"), index=False, header=False)
    refined_y.to_csv(os.path.join(output_dir, "refined_y.csv"), index=False, header=False)
    refined_K.to_csv(os.path.join(output_dir, "refined_k.csv"), index=False, header=False)


if __name__ == '__main__':
    main(sys.argv[1:])  # exclude the script name from the args when called from shell


