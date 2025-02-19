import sys
import argparse
import numpy as np
import pandas as pd
from scipy.interpolate import splprep, splev
from scipy.spatial.distance import euclidean
from tqdm import tqdm
from scipy.ndimage import gaussian_filter


def fit_spline(x_coords, y_coords, smoothing):
    if len(x_coords) < 3:
        return None
    tck, _ = splprep([x_coords, y_coords], s=smoothing)
    return tck


def arc_length_resampling(tck, num_sampled_points, spacing):
    u_fine = np.linspace(0, 1, num_sampled_points)
    fine_x, fine_y = splev(u_fine, tck)

    distances = np.sqrt(np.diff(fine_x) ** 2 + np.diff(fine_y) ** 2)
    cumulative_dist = np.insert(np.cumsum(distances), 0, 0)

    target_distances = np.arange(0, cumulative_dist[-1], spacing)
    new_x = np.interp(target_distances, cumulative_dist, fine_x)
    new_y = np.interp(target_distances, cumulative_dist, fine_y)

    return list(new_x), list(new_y)


def resample_skeleton(x_coords, y_coords, spacing=10, num_sampled_points=10000, smoothing=0.1):
    if len(x_coords) < 3:
        return [np.nan], [np.nan]

    tck = fit_spline(x_coords, y_coords, smoothing)
    if tck is None:
        return [np.nan], [np.nan]

    new_x, new_y = arc_length_resampling(tck, num_sampled_points, spacing)
    return new_x, new_y


def refine_skeleton_spacing(skel_x_df, skel_y_df, spacing=10, num_sampled_points=10000, smoothing=0.1):
    print(f"Processing {len(skel_x_df)} frames...")
    print(f"Parameters: spacing={spacing}, sampling_points={num_sampled_points}, smoothing={smoothing}")

    all_new_x = []
    all_new_y = []
    max_points = 0

    for frame in tqdm(range(len(skel_x_df))):
        x_coords = skel_x_df.iloc[frame].dropna().values
        y_coords = skel_y_df.iloc[frame].dropna().values

        new_x, new_y = resample_skeleton(
            x_coords, y_coords,
            spacing=spacing,
            num_sampled_points=num_sampled_points,
            smoothing=smoothing
        )

        if isinstance(new_x, np.ndarray):
            new_x = new_x.tolist()
        if isinstance(new_y, np.ndarray):
            new_y = new_y.tolist()

        max_points = max(max_points, len(new_x))
        all_new_x.append(new_x)
        all_new_y.append(new_y)

    print("\nCreating final DataFrames...")
    padded_x = [x + [np.nan] * (max_points - len(x)) for x in all_new_x]
    padded_y = [y + [np.nan] * (max_points - len(y)) for y in all_new_y]

    new_cols = [f'point_{i + 1}' for i in range(max_points)]

    new_x_df = pd.DataFrame(padded_x, columns=new_cols)
    new_y_df = pd.DataFrame(padded_y, columns=new_cols)
    print(f"Done! Maximum points in any frame: {max_points}")
    return new_x_df, new_y_df


def truncate_columns(df_x, df_y, max_columns):
    """
    Truncate DataFrames to a specified number of columns.

    Parameters:
    -----------
    df_x : pandas.DataFrame
        DataFrame with x-coordinates
    df_y : pandas.DataFrame
        DataFrame with y-coordinates
    max_columns : int
        Maximum number of columns to keep

    Returns:
    --------
    truncated_x : pandas.DataFrame
        Truncated x-coordinates
    truncated_y : pandas.DataFrame
        Truncated y-coordinates
    """
    orig_cols = df_x.shape[1]

    if max_columns is None or orig_cols <= max_columns:
        return df_x, df_y

    print(f"Truncating from {orig_cols} columns to {max_columns} columns")

    # Keep only the first max_columns
    truncated_x = df_x.iloc[:, :max_columns].copy()
    truncated_y = df_y.iloc[:, :max_columns].copy()

    # Rename columns to maintain consistency
    new_columns = [f'point_{i + 1}' for i in range(max_columns)]
    truncated_x.columns = new_columns
    truncated_y.columns = new_columns

    return truncated_x, truncated_y


def calculate_curvature(skeleton_x, skeleton_y):
    """
    Calculates curvature K using first and second derivatives.
    """
    K_df = pd.DataFrame(index=range(len(skeleton_x)),
                        columns=skeleton_x.columns,
                        dtype=float)

    for idx in range(len(skeleton_x)):
        if skeleton_x.iloc[idx].isna().all() or skeleton_y.iloc[idx].isna().all():
            K_df.iloc[idx] = np.nan
            continue

        x = skeleton_x.iloc[idx].values
        y = skeleton_y.iloc[idx].values

        if len(x) < 3:
            K_df.iloc[idx] = np.nan
            continue

        x_der = np.gradient(x)
        y_der = np.gradient(y)

        x_der2 = np.gradient(x_der)
        y_der2 = np.gradient(y_der)

        denominator = (x_der ** 2 + y_der ** 2) ** 1.5
        denominator = np.where(denominator == 0, np.nan, denominator)
        K = (x_der * y_der2 - y_der * x_der2) / denominator

        K_df.iloc[idx] = K

    return K_df


def smooth_2d_data(data, time_sigma=2, spatial_sigma=1):
    """
    Smooth 2D data using Gaussian filtering
    """
    values = data.values
    smoothed = gaussian_filter(values, sigma=[time_sigma, spatial_sigma])
    return pd.DataFrame(smoothed, index=data.index, columns=data.columns)


def main(arg_list=None):
    parser = argparse.ArgumentParser(description='Process skeleton data with spline fitting')
    # Input files
    parser.add_argument('--skeleton_x', type=str, required=True, help='Path to skeleton X coordinates CSV')
    parser.add_argument('--skeleton_y', type=str, required=True, help='Path to skeleton Y coordinates CSV')
    # Parameters
    parser.add_argument('--spacing', type=float, default=5, help='Spacing between points (default: 5)')
    parser.add_argument('--num_sampled_points', type=int, default=10000,
                        help='Number of sampling points (default: 10000)')
    parser.add_argument('--smoothing', type=float, default=0.1, help='Smoothing factor (default: 0.1)')
    parser.add_argument('--time_sigma', type=float, default=2.0,
                        help='Time sigma for Gaussian smoothing (default: 2.0)')
    parser.add_argument('--spatial_sigma', type=float, default=1.0,
                        help='Spatial sigma for Gaussian smoothing (default: 1.0)')
    parser.add_argument('--max_columns', type=int, default=None,
                        help='Maximum number of points to keep (default: no limit)')
    # Output files
    parser.add_argument('--output_x', type=str, required=True, help='Path to save output X coordinates')
    parser.add_argument('--output_y', type=str, required=True, help='Path to save output Y coordinates')
    parser.add_argument('--output_curvature', type=str, required=True, help='Path to save output curvature values')
    parser.add_argument('--output_smoothed_curvature', type=str, required=True,
                        help='Path to save smoothed curvature values')

    args = parser.parse_args(arg_list)

    # Load input data
    print("Loading input data...")
    skeleton_x = pd.read_csv(args.skeleton_x, header=None)
    skeleton_y = pd.read_csv(args.skeleton_y, header=None)

    # Process skeleton
    new_x_df, new_y_df = refine_skeleton_spacing(
        skeleton_x,
        skeleton_y,
        spacing=args.spacing,
        num_sampled_points=args.num_sampled_points,
        smoothing=args.smoothing
    )

    # Apply column truncation if specified
    if args.max_columns is not None:
        print(f"\nApplying column truncation to {args.max_columns} points...")
        new_x_df, new_y_df = truncate_columns(new_x_df, new_y_df, args.max_columns)

    # Calculate curvature
    print("\nCalculating curvature...")
    curvature_df = calculate_curvature(new_x_df, new_y_df)

    # Apply smoothing to curvature
    print("\nApplying Gaussian smoothing...")
    smoothed_curvature = smooth_2d_data(
        curvature_df,
        time_sigma=args.time_sigma,
        spatial_sigma=args.spatial_sigma
    )

    # Save results
    print("\nSaving results...")
    new_x_df.to_csv(args.output_x, index=False, header=False)
    new_y_df.to_csv(args.output_y, index=False, header=False)
    curvature_df.to_csv(args.output_curvature, index=False, header=False)
    smoothed_curvature.to_csv(args.output_smoothed_curvature, index=False, header=False)
    print("All files saved successfully!")
    print(f"Output dimensions: {len(new_x_df)} frames × {len(new_x_df.columns)} points")


if __name__ == '__main__':
    main(sys.argv[1:])