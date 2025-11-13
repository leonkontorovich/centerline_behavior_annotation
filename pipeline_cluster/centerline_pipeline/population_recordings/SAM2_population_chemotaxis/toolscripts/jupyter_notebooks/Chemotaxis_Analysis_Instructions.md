# Population Chemotaxis Analysis Guide

## Overview

This guide explains how to use the `Chemotaxis_population_grouped.ipynb` notebook. The notebook processes chemotaxis data from multiple experimental recordings.

## What This Analysis Does

The notebook provides:
- Data loading and processing
- Data visualization tools
- Statistical analysis functions
- Interactive widgets for data exploration
- Video export functionality
- Data saving capabilities

---

## Detailed Step-by-Step Instructions

### Step 1: Data Import and Preparation

**Purpose**: Load and process chemotaxis CSV files from experimental recordings.

**What happens**:
```python
def process_chemotaxis_files(source_path, target_filename="chemotaxis_params.csv", nan_threshold_percent=40)
```

This function:
1. Scans nested directories for CSV files
2. Reads CSV files with multi-level headers
3. Adds trackID column to each DataFrame
4. Filters out DataFrames with >40% NaN values in Spline_K columns
5. Groups data by subfolder names

**Key parameters**:
- `source_path`: Path to data directory
- `nan_threshold_percent`: Threshold for filtering (default: 40%)

**Output**: Dictionary with subfolder names as keys, DataFrames as values

### Step 2: Dataset Quality Assessment

**Purpose**: Create kymograph visualizations.

**Interactive features**:
- Dropdown to select dataset
- Progress bar for processing
- Color-coded track ID indicators

**Visualization**:
- Horizontal axis: Time (frames)
- Vertical axis: Body segments 
- Colors: Curvature values (seismic colormap, vmin=-0.06, vmax=0.06)
- Track bars: Show which track is active at each time point

### Step 3: Single Dataset Spatial Visualization

**Purpose**: Plot 2D coordinates.

**Interactive controls**:
- Dataset dropdown
- Density slider (1-100, default: 10) - sampling interval
- Reversal checkbox - show/hide reversal markers

**Plot elements**:
- Dark blue dots: X_rel_skel_pos_centroid, Y_rel_skel_pos_centroid
- Light blue dots: X_rel_skel_pos_0, Y_rel_skel_pos_0  
- Green star: odor_x, odor_y position
- Red X markers: reversal_onset = 1 (if enabled)
- Axis limits: 0 to 40.05

### Step 4: Population-Level Statistical Analysis

**Purpose**: Calculate statistics across all datasets.

**Function**: `analyze_chemotaxis_metrics(results_dict)`

**Metrics calculated**:
- turns_count: Sum where turn column = 1
- total_rows: DataFrame length
- minutes: total_rows / (10 * 60)
- nan_count: Rows where all Spline_K columns are NaN

**Outputs**:
1. Violin plots: Event distributions (turns %, NaN %)
2. Duration plot: Minutes distribution
3. Pie chart: Dataset size proportions
4. CSV files: Summary tables saved to output/

### Step 5: Interactive Time-Series Viewer

**Purpose**: View time-series data around specific frames.

**Controls**:
- Dataset dropdown
- Frame slider (300 to max_frames-300)

**9 subplot layout**:
1. Spline Kymogram: Spline_K data, seismic colormap
2. Binary Events: turn, behaviour_state 
3. Speed Centroid: speed_centroid (0-0.2 range)
4. Speed Center 24: speed_center_24 (0-0.2 range)
5. Navigation Index: NI (-1.2 to 1.2 range)
6. Curving Angle: curving_angle
7. Bearing Angle: abs(bearing_angle), capped at 182
8. Distance to Odor: distance_to_odor_centroid
9. Concentrations: conc_at_0, conc_at_centroid

**Window**: ±300 frames around selected frame
**Time axis**: Converted to seconds (frames/10)

### Step 6: Video Export Tool

**Purpose**: Create MP4 videos of time-series data.

**Controls**:
- Dataset dropdown  
- Track ID dropdown
- Export button

**Video settings**:
- Format: MP4
- FPS: 30
- Writer: FFMpegWriter
- Figure: 10x14 inches, 72 DPI
- Output: videos/ directory with timestamp

**Animation**: Shows 8-panel layout progressing through all frames of selected track

### Step 7: Data Archiving

**Purpose**: Save processed data.

**Saved files**:
- results_dict.pkl: Complete dictionary (pickle format)
- chemotaxis_metrics.csv: Summary statistics
- event_percentages.csv: Turn/NaN percentages  
- chemotaxis_metrics_plot.png: Summary plot

---

## Data Structure

**Main column groups**:
- chemotaxis_parameter: Behavioral measurements
- Spline_K: Body curvature data
- trackID: Track identification

**Assumptions**:
- Frame rate: 10 fps
- Each row: One time frame (0.1 seconds)

**Required libraries**: pandas, matplotlib, numpy, ipywidgets, seaborn, pathlib, tqdm, pickle