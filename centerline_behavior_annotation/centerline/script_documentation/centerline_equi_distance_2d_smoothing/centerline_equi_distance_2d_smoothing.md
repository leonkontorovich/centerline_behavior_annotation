# Skeleton Processing and Curvature Analysis Documentation

## Core Functionality Overview
This code processes skeleton coordinate data to create evenly-spaced points along a curve and calculate curvature values. The pipeline includes spline fitting, resampling, curvature calculation, and smoothing operations.

## Key Components

### 1. Spline Fitting
```python
def fit_spline(x_coords, y_coords, smoothing):
    tck, _ = splprep([x_coords, y_coords], s=smoothing)
    return tck
```
- Uses scipy's `splprep` to fit a B-spline to the skeleton coordinates
- The smoothing parameter controls the trade-off between smoothness and accuracy
- Returns the spline parameters (tck) used for subsequent interpolation

### 2. Arc Length Resampling
```python
def arc_length_resampling(tck, num_sampled_points, spacing):
    u_fine = np.linspace(0, 1, num_sampled_points)
    fine_x, fine_y = splev(u_fine, tck)
```
- Resamples the spline at equal arc-length intervals
- Process:
  1. Creates a fine sampling of points along the spline
  2. Calculates cumulative distances between points
  3. Interpolates to achieve desired spacing
- Ensures uniform point distribution along the curve

### 3. Curvature Calculation
```python
def calculate_curvature(skeleton_x, skeleton_y):
    # Calculate first derivatives
    x_der = np.gradient(x)
    y_der = np.gradient(y)
    
    # Calculate second derivatives
    x_der2 = np.gradient(x_der)
    y_der2 = np.gradient(y_der)
    
    # Curvature formula
    K = (x_der * y_der2 - y_der * x_der2) / (x_der ** 2 + y_der ** 2) ** 1.5
```
- Implements the mathematical formula for curvature
- Uses numerical derivatives via numpy's gradient function
- Handles edge cases and NaN values carefully

### 4. Data Smoothing
```python
def smooth_2d_data(data, time_sigma=2, spatial_sigma=1):
    # Apply 2D Gaussian smoothing while preserving NaN values
```
- Applies 2D Gaussian filtering to smooth the curvature data
- Parameters:
  - time_sigma: Controls smoothing along the temporal dimension
  - spatial_sigma: Controls smoothing along the spatial dimension
- Preserves NaN values and maintains boundary information

### 5. Dynamic Point Count Optimization
```python
def calculate_optimal_point_count(skel_x_df, skel_y_df, spacing):
    # Calculate median skeleton length
    median_length = np.median(path_lengths)
    optimal_points = int(median_length / spacing) + 1
```
- Automatically determines optimal number of points based on skeleton length
- Uses median length for robustness against outliers
- Calculates point count based on desired spacing

## Key Parameters

### Input Parameters
- `spacing`: Distance between points after resampling (default: 5)
- `num_sampled_points`: Number of initial sampling points (default: 10000)
- `smoothing`: Spline smoothing factor (default: 0.1)
- `time_sigma`: Temporal smoothing parameter (default: 2.0)
- `spatial_sigma`: Spatial smoothing parameter (default: 1.0)
- `max_columns`: Maximum number of points (0 for dynamic mode)

### Dynamic Column Optimization
```python
def find_optimal_column_crop(df, change_threshold=0.5):
```
- Automatically detects optimal number of columns based on data occupancy
- Uses rate of change detection to find significant drops in data presence
- Threshold of 0.5 represents a 50% drop in occupancy

## Mathematical Foundations

### Curvature Formula
The curvature (K) is calculated using the formula:
```
K = (x' * y'' - y' * x'') / (x'^2 + y'^2)^(3/2)
```
where x' and y' are first derivatives, and x'' and y'' are second derivatives.

## Output Files
1. Resampled X coordinates
2. Resampled Y coordinates
3. Raw curvature values
4. Smoothed curvature values

## Error Handling and Edge Cases
- Handles missing data (NaN values)
- Manages sequences with insufficient points
- Ensures consistent dimensions across all outputs

