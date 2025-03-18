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


def calculate_skeleton_length_statistics(skel_x_df, skel_y_df):
    """
    Calculate skeleton length statistics across all frames and return a representative length.
    Uses the 60th percentile as the representative length, which is slightly above average.

    Parameters:
    -----------
    skel_x_df : pandas.DataFrame
        DataFrame with x coordinates
    skel_y_df : pandas.DataFrame
        DataFrame with y coordinates

    Returns:
    --------
    tuple : (representative_length, length_statistics_dict)
    """
    # Calculate path lengths for each frame
    path_lengths = []

    for idx in range(len(skel_x_df)):
        # Skip if row contains all NaN
        if skel_x_df.iloc[idx].isna().all() or skel_y_df.iloc[idx].isna().all():
            continue

        # Get non-NaN coordinates
        mask = ~(skel_x_df.iloc[idx].isna() | skel_y_df.iloc[idx].isna())
        if mask.sum() < 2:
            continue

        x = skel_x_df.iloc[idx][mask].values
        y = skel_y_df.iloc[idx][mask].values

        # Calculate path length
        total_length = 0
        for i in range(len(x) - 1):
            segment_length = np.sqrt((x[i + 1] - x[i]) ** 2 + (y[i + 1] - y[i]) ** 2)
            total_length += segment_length

        if total_length > 0:
            path_lengths.append(total_length)

    if not path_lengths:
        print("Warning: Could not calculate any valid path lengths. Using default length of 100.")
        return 100, {"min": 0, "mean": 100, "median": 100, "percentile_60": 100, "max": 100}

    # Calculate statistics
    percentile_60 = np.percentile(path_lengths, 60)
    stats = {
        "min": np.min(path_lengths),
        "mean": np.mean(path_lengths),
        "median": np.median(path_lengths),
        "percentile_60": percentile_60,
        "max": np.max(path_lengths)
    }

    representative_length = percentile_60

    print(f"Skeleton length statistics:")
    print(f"  Minimum length: {stats['min']:.2f} pixels")
    print(f"  Mean length: {stats['mean']:.2f} pixels")
    print(f"  Median length: {stats['median']:.2f} pixels")
    print(f"  60th percentile: {stats['percentile_60']:.2f} pixels")
    print(f"  Maximum length: {stats['max']:.2f} pixels")
    print(f"  Using 60th percentile ({representative_length:.2f} pixels) as reference length")

    return representative_length, stats


def refine_skeleton_spacing(skel_x_df, skel_y_df, spacing=10, num_sampled_points=10000, smoothing=0.1):
    print(f"Processing {len(skel_x_df)} frames...")
    print(f"Parameters: spacing={spacing}, sampling_points={num_sampled_points}, smoothing={smoothing}")

    all_new_x = []
    all_new_y = []
    max_points = 0
    point_counts = []

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

        num_points = len(new_x)
        point_counts.append(num_points)
        max_points = max(max_points, num_points)
        all_new_x.append(new_x)
        all_new_y.append(new_y)

    # Calculate statistics
    min_points = min(point_counts) if point_counts else 0
    avg_points = sum(point_counts) / len(point_counts) if point_counts else 0

    print("\nCreating final DataFrames...")
    padded_x = [x + [np.nan] * (max_points - len(x)) for x in all_new_x]
    padded_y = [y + [np.nan] * (max_points - len(y)) for y in all_new_y]

    new_cols = [f'point_{i + 1}' for i in range(max_points)]

    # Modified lines to preserve the original indices:
    new_x_df = pd.DataFrame(padded_x, columns=new_cols, index=skel_x_df.index)
    new_y_df = pd.DataFrame(padded_y, columns=new_cols, index=skel_y_df.index)

    print(f"Points statistics:")
    print(f"  Minimum points in any frame: {min_points}")
    print(f"  Average points per frame: {avg_points:.2f}")
    print(f"  Maximum points in any frame: {max_points}")

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


def calculate_optimal_point_count(skel_x_df, skel_y_df, spacing):
    """
    Calculate the optimal number of points based on average skeleton length.

    Parameters:
    -----------
    skel_x_df : pandas.DataFrame
        DataFrame with x coordinates
    skel_y_df : pandas.DataFrame
        DataFrame with y coordinates
    spacing : float
        Desired spacing between points in pixels

    Returns:
    --------
    optimal_points : int
        Optimal number of points to represent the skeleton
    """
    # Calculate path lengths for each frame
    path_lengths = []

    for idx in range(len(skel_x_df)):
        # Skip if row contains all NaN
        if skel_x_df.iloc[idx].isna().all() or skel_y_df.iloc[idx].isna().all():
            continue

        # Get non-NaN coordinates
        mask = ~(skel_x_df.iloc[idx].isna() | skel_y_df.iloc[idx].isna())
        if mask.sum() < 2:
            continue

        x = skel_x_df.iloc[idx][mask].values
        y = skel_y_df.iloc[idx][mask].values

        # Calculate path length
        total_length = 0
        for i in range(len(x) - 1):
            segment_length = np.sqrt((x[i + 1] - x[i]) ** 2 + (y[i + 1] - y[i]) ** 2)
            total_length += segment_length

        if total_length > 0:
            path_lengths.append(total_length)

    if not path_lengths:
        print("Warning: Could not calculate any valid path lengths. Using default count of 20.")
        return 20

    # Use median for robustness against outliers
    median_length = np.median(path_lengths)
    optimal_points = int(median_length / spacing) + 1

    print(f"Dynamic point calculation:")
    print(f"  Median skeleton length: {median_length:.2f} pixels")
    print(f"  With spacing of {spacing:.2f} pixels")
    print(f"  Optimal point count: {optimal_points}")

    return optimal_points


def find_optimal_column_crop(df, change_threshold=0.5):
    """
    Find optimal column crop point to remove mostly-empty columns
    using rate of change detection.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame to analyze
    change_threshold : float
        Rate of change threshold to identify significant drops (0-1)

    Returns:
    --------
    list : Columns to keep
    """
    # Calculate column occupancy (non-NaN percentage)
    col_occupancy = df.notna().mean(axis=0) * 100

    # Calculate rate of change between adjacent columns
    occupancy_changes = np.zeros(len(col_occupancy))
    for i in range(1, len(col_occupancy)):
        if col_occupancy.iloc[i - 1] > 0:  # Avoid division by zero
            relative_change = (col_occupancy.iloc[i] - col_occupancy.iloc[i - 1]) / col_occupancy.iloc[i - 1]
            occupancy_changes[i] = relative_change

    # Find points with significant negative changes (drops)
    col_drops = []
    for i in range(1, len(occupancy_changes)):
        if occupancy_changes[i] < -change_threshold:
            col_drops.append(i)

    # If no clear drop found, keep all columns
    if not col_drops:
        cols_to_keep = df.columns
    else:
        # Keep columns up to first significant drop
        cols_to_keep = df.columns[:col_drops[0]]

    print(f"Column occupancy analysis:")
    print(f"  Original columns: {len(df.columns)}")
    print(f"  Columns to keep: {len(cols_to_keep)}")

    # Print occupancy at cutoff point if applicable
    if col_drops:
        cutoff_idx = col_drops[0]
        print(
            f"  Occupancy at cutoff: {col_occupancy.iloc[cutoff_idx - 1]:.1f}% → {col_occupancy.iloc[cutoff_idx]:.1f}%")
        print(f"  Rate of change at cutoff: {occupancy_changes[cutoff_idx]:.1%}")

    return cols_to_keep


def calculate_curvature(skeleton_x, skeleton_y):
    """
    Calculates curvature K using first and second derivatives with improved handling of valid points.
    """
    K_df = pd.DataFrame(index=range(len(skeleton_x)),
                        columns=skeleton_x.columns,
                        dtype=float)

    for idx in range(len(skeleton_x)):
        # Skip if row contains all NaN
        if skeleton_x.iloc[idx].isna().all() or skeleton_y.iloc[idx].isna().all():
            K_df.iloc[idx] = np.nan
            continue

        # Get non-NaN coordinates
        valid_mask = ~(skeleton_x.iloc[idx].isna() | skeleton_y.iloc[idx].isna())
        x = skeleton_x.iloc[idx][valid_mask].values
        y = skeleton_y.iloc[idx][valid_mask].values
        valid_cols = skeleton_x.columns[valid_mask]

        # Need at least 3 points for derivatives
        if len(x) < 3:
            K_df.iloc[idx] = np.nan
            continue

        # Calculate first derivatives using central differences
        x_der = np.gradient(x)
        y_der = np.gradient(y)

        # Calculate second derivatives
        x_der2 = np.gradient(x_der)
        y_der2 = np.gradient(y_der)

        # Calculate curvature K
        denominator = (x_der ** 2 + y_der ** 2) ** 1.5
        denominator = np.where(denominator < 1e-10, np.nan, denominator)
        K = (x_der * y_der2 - y_der * x_der2) / denominator

        # Assign values only to valid columns
        for i, col in enumerate(valid_cols):
            if i < len(K):
                K_df.loc[idx, col] = K[i]

    return K_df


def smooth_2d_data(data, time_sigma=2, spatial_sigma=1):
    """
    Smooth 2D data using Gaussian filtering while preserving NaN values
    and maintaining boundary information
    """
    # Convert to numpy array for smoothing
    values = data.values

    # Create a mask for NaN values
    nan_mask = np.isnan(values)

    # Replace NaNs with zeros for filtering
    filled_values = np.nan_to_num(values, nan=0.0)

    # Apply 2D Gaussian smoothing
    smoothed = gaussian_filter(filled_values, sigma=[time_sigma, spatial_sigma], mode='nearest')

    # Create a weight array (1 for data, 0 for NaN)
    weights = ~nan_mask
    weight_smoothed = gaussian_filter(weights.astype(float), sigma=[time_sigma, spatial_sigma], mode='nearest')

    # Avoid division by zero
    weight_smoothed[weight_smoothed < 1e-10] = 1

    # Normalize the result
    result = smoothed / weight_smoothed

    # Restore NaN values where they were before
    result[nan_mask] = np.nan

    # Convert back to DataFrame with same structure
    return pd.DataFrame(result, index=data.index, columns=data.columns)


def main(arg_list=None):
    parser = argparse.ArgumentParser(description='Process skeleton data with spline fitting')
    # Input files
    parser.add_argument('--skeleton_x', type=str, required=True, help='Path to skeleton X coordinates CSV')
    parser.add_argument('--skeleton_y', type=str, required=True, help='Path to skeleton Y coordinates CSV')

    # Spacing parameters - users can provide either absolute or relative spacing
    parser.add_argument('--spacing', type=float, default=None,
                        help='Absolute spacing between points in pixels (if provided, overrides relative_spacing)')
    parser.add_argument('--relative_spacing', type=float, default=2.0,
                        help='Spacing between points as percentage of skeleton length (default: 2.0, ignored if --spacing is provided)')

    # Other parameters
    parser.add_argument('--num_sampled_points', type=int, default=10000,
                        help='Number of sampling points (default: 10000)')
    parser.add_argument('--smoothing', type=float, default=0.1, help='Smoothing factor (default: 0.1)')
    parser.add_argument('--time_sigma', type=float, default=2.0,
                        help='Time sigma for Gaussian smoothing (default: 2.0)')
    parser.add_argument('--spatial_sigma', type=float, default=1.0,
                        help='Spatial sigma for Gaussian smoothing (default: 1.0)')
    parser.add_argument('--max_columns', type=int, default=0,
                        help='Maximum number of points to keep (default: auto-detect). Set to 0 for dynamic mode.')
    parser.add_argument('--change_threshold', type=float, default=0.5,
                        help='Rate of change threshold for column cropping (default: 0.5)')
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

    # Calculate skeleton length statistics if using relative spacing
    if args.spacing is None:
        print("\nAnalyzing skeleton length across all frames...")
        representative_length, length_stats = calculate_skeleton_length_statistics(
            skeleton_x, skeleton_y
        )

        # Calculate absolute spacing from relative spacing
        spacing = (args.relative_spacing / 100.0) * representative_length
        print(f"\nConverting relative spacing {args.relative_spacing}% to absolute: {spacing:.2f} pixels")
    else:
        # Use absolute spacing if provided
        spacing = args.spacing
        print(f"\nUsing provided absolute spacing: {spacing} pixels")

    # Process skeleton with the calculated spacing
    new_x_df, new_y_df = refine_skeleton_spacing(
        skeleton_x,
        skeleton_y,
        spacing=spacing,
        num_sampled_points=args.num_sampled_points,
        smoothing=args.smoothing
    )

    # Add this check after loading the data
    original_frame_count = len(skeleton_x)

    # Add this check after processing
    if len(new_x_df) != original_frame_count:
        print(f"WARNING: Frame count mismatch! Original: {original_frame_count}, New: {len(new_x_df)}")

    # Determine final column count for all outputs
    final_columns = None

    # Dynamic mode: calculate optimal number of points based on average length
    if args.max_columns == 0:
        print("\nUsing dynamic mode to determine optimal point count...")
        optimal_points = calculate_optimal_point_count(new_x_df, new_y_df, spacing)

        # Find optimal column crop point using rate of change detection
        print("\nAnalyzing column occupancy using rate of change detection...")
        cols_to_keep = find_optimal_column_crop(new_x_df, change_threshold=args.change_threshold)

        # Use the smaller of the two values (optimal or occupancy-based)
        final_columns = min(optimal_points, len(cols_to_keep))
        print(f"\nFinal column count: {final_columns}")
    # Fixed mode: use specified column count
    elif args.max_columns is not None:
        print(f"\nApplying fixed column truncation to {args.max_columns} points...")
        final_columns = args.max_columns

    # Apply column truncation to coordinate data
    new_x_df, new_y_df = truncate_columns(new_x_df, new_y_df, final_columns)

    # Calculate curvature with truncated coordinates
    print("\nCalculating curvature...")
    curvature_df = calculate_curvature(new_x_df, new_y_df)

    # Apply smoothing to curvature
    print("\nApplying Gaussian smoothing...")
    smoothed_curvature = smooth_2d_data(
        curvature_df,
        time_sigma=args.time_sigma,
        spatial_sigma=args.spatial_sigma
    )

    # Ensure all outputs have the same column count
    print(f"\nEnsuring all output files have {new_x_df.shape[1]} columns...")

    # Verify column counts match
    if (new_x_df.shape[1] != new_y_df.shape[1] or
            new_x_df.shape[1] != curvature_df.shape[1] or
            new_x_df.shape[1] != smoothed_curvature.shape[1]):
        print("Warning: Column counts don't match, enforcing consistency...")

        # Ensure all DataFrames have the same columns
        column_count = new_x_df.shape[1]

        new_x_df = new_x_df.iloc[:, :column_count]
        new_y_df = new_y_df.iloc[:, :column_count]
        curvature_df = curvature_df.iloc[:, :column_count]
        smoothed_curvature = smoothed_curvature.iloc[:, :column_count]

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

'''
rule process_skeleton_curvature:
    input:
        spline_X = "{datasets_output}skeleton_spline_X_coords.csv",
        spline_Y = "{datasets_output}skeleton_spline_Y_coords.csv"
    params:
        relative_spacing = config['relative_spacing'],
        num_sampled_points = config['num_sampled_points'],
        smoothing = config['smoothing'],
        time_sigma = config['time_sigma'],
        spatial_sigma = config['spatial_sigma'],
        max_columns = config['max_columns']
    output:
        spline_X_new = "{datasets_output}skeleton_spline_X_coords_new.csv",
        spline_Y_new = "{datasets_output}skeleton_spline_Y_coords_new.csv",
        spline_K_new = "{datasets_output}skeleton_spline_K_new.csv",
        spline_K_new_smooth = "{datasets_output}skeleton_spline_K_new_smoothed.csv"
    run:
        from centerline_behavior_annotation.centerline.dev import centerline_equi_distance_2d_smoothing

        centerline_equi_distance_2d_smoothing.main([
            '--skeleton_x', str(input.spline_X),
            '--skeleton_y', str(input.spline_Y),
            '--relative_spacing', str(params.relative_spacing),
            '--num_sampled_points', str(params.num_sampled_points),
            '--smoothing', str(params.smoothing),
            '--time_sigma', str(params.time_sigma),
            '--spatial_sigma', str(params.spatial_sigma),
            '--max_columns', str(params.max_columns), 
            '--output_x', str(output.spline_X_new),
            '--output_y', str(output.spline_Y_new),
            '--output_curvature', str(output.spline_K_new),
            '--output_smoothed_curvature', str(output.spline_K_new_smooth)
        ])

#preprocess spline
relative_spacing: 2.0  # 2% of skeleton length
num_sampled_points: 10000
smoothing: 0.1
time_sigma: 2.0
spatial_sigma: 1.0
max_columns: 0 #dynamic mode - cuts skelleton where nan content increases 50%+
'''