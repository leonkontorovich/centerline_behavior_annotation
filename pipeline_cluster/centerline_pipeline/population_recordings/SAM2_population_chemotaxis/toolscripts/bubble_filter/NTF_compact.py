#!/usr/bin/env python3
"""
Bubble Filter - Command-line tool for filtering stationary tracks from nematode datasets
Uses SD-based auto-threshold clustering to identify and optionally remove bubble artifacts
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import shutil
from concurrent.futures import ThreadPoolExecutor
import plotly.express as px
import plotly.offline as po
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thread-safe file access
file_lock = Lock()


def find_track_folders(base_dir):
    """
    Recursively find all folders containing track.tif files and group them by repeat folder.
    
    Returns:
        dict: {repeat_folder_path: [list of track folder paths]}
    """
    logger.info(f"Searching for track folders in {base_dir}")
    track_folders = {}
    
    for root, dirs, files in os.walk(base_dir):
        if 'track.tif' in files:
            track_folder = root
            repeat_folder = os.path.dirname(track_folder)  # Parent folder is the repeat
            
            if repeat_folder not in track_folders:
                track_folders[repeat_folder] = []
            track_folders[repeat_folder].append(track_folder)
    
    logger.info(f"Found {len(track_folders)} repeat folders with tracks")
    for repeat, tracks in track_folders.items():
        logger.info(f"  {os.path.basename(repeat)}: {len(tracks)} tracks")
    
    return track_folders


def calculate_sd(track_folder):
    """
    Calculate standard deviation for X and Y coordinates from track.txt
    
    Returns:
        dict: {ID, SD(X), SD(Y), EuclideanNorm_SD(X,Y), Path} or None if error
    """
    try:
        track_file = os.path.join(track_folder, 'track.txt')
        
        with file_lock:
            if not os.path.isfile(track_file):
                logger.warning(f"Missing file: {track_file}")
                return None
            
            df = pd.read_csv(track_file)
        
        # Validate required columns
        if not {'X', 'Y'}.issubset(df.columns):
            logger.warning(f"Invalid format in {track_file} - missing X or Y columns")
            return None
        
        sd_x = df['X'].std()
        sd_y = df['Y'].std()
        euclidean_sd = np.sqrt(sd_x**2 + sd_y**2)
        
        identifier = os.path.basename(track_folder)
        
        return {
            'ID': identifier,
            'SD(X)': sd_x,
            'SD(Y)': sd_y,
            'EuclideanNorm_SD(X,Y)': euclidean_sd,
            'Path': track_folder
        }
    except Exception as e:
        logger.error(f"Error calculating SD for {track_folder}: {e}")
        return None


def auto_threshold(sd_values):
    """
    Calculate optimal threshold using first derivative method.
    Finds the point where SD values jump from stationary cluster to mobile cluster.
    
    Args:
        sd_values: array of SD values
    
    Returns:
        float: optimal threshold value
    """
    logger.info("Calculating auto-threshold using first derivative method...")
    
    # Sort the SD values
    sd_sorted = np.sort(sd_values)
    
    # Compute first derivative (differences between consecutive SD values)
    first_derivative = np.diff(sd_sorted)
    
    # Calculate relative increases
    relative_increases = first_derivative / sd_sorted[:-1]
    
    # Identify the index of the maximum relative increase
    max_increase_idx = np.argmax(relative_increases)
    
    # Set threshold at the SD value corresponding to this index
    threshold = sd_sorted[max_increase_idx]
    
    logger.info(f"Auto-threshold calculated: {threshold:.4f}")
    return threshold


def sd_threshold_clustering(sd_summary_df, threshold=None):
    """
    Classify tracks as Stationary or Non-Stationary based on SD threshold.
    
    Args:
        sd_summary_df: DataFrame with SD values
        threshold: Manual threshold value (if None, auto-calculate)
    
    Returns:
        DataFrame with Cluster column added
    """
    if threshold is None:
        # Auto-thresholding
        threshold = auto_threshold(sd_summary_df['EuclideanNorm_SD(X,Y)'].values)
    else:
        logger.info(f"Using manual threshold: {threshold:.4f}")
    
    # Classify based on threshold
    sd_summary_df['Cluster'] = sd_summary_df['EuclideanNorm_SD(X,Y)'].apply(
        lambda x: 'Stationary' if x <= threshold else 'Non-Stationary'
    )
    
    # Log statistics
    stationary_count = (sd_summary_df['Cluster'] == 'Stationary').sum()
    mobile_count = (sd_summary_df['Cluster'] == 'Non-Stationary').sum()
    logger.info(f"Classification results: {stationary_count} stationary, {mobile_count} mobile")
    
    return sd_summary_df, threshold


def visualize_clusters(sd_summary_df, output_dir, repeat_name):
    """
    Create interactive Plotly visualization of clustering results.
    
    Args:
        sd_summary_df: DataFrame with clustering results
        output_dir: Directory to save the plot
        repeat_name: Name of the repeat for plot title
    """
    try:
        logger.info("Creating visualization...")
        
        fig = px.scatter(
            sd_summary_df,
            x='SD(X)',
            y='SD(Y)',
            color='Cluster',
            hover_data=['ID', 'EuclideanNorm_SD(X,Y)'],
            title=f'SD-Based Clustering Results - {repeat_name}',
            labels={'SD(X)': 'Standard Deviation X', 'SD(Y)': 'Standard Deviation Y'},
            color_discrete_map={'Stationary': 'red', 'Non-Stationary': 'green'}
        )
        
        plot_file = os.path.join(output_dir, 'clustering_plot.html')
        po.plot(fig, filename=plot_file, auto_open=False)
        logger.info(f"Plot saved to {plot_file}")
        
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")


def process_repeat(repeat_folder, track_folders, threshold, dry_run, delete_mode):
    """
    Process a single repeat folder: calculate SD, cluster, and optionally delete.
    
    Args:
        repeat_folder: Path to repeat folder
        track_folders: List of track folder paths
        threshold: Manual threshold (None for auto)
        dry_run: If True, only simulate deletions
        delete_mode: If True, actually delete stationary tracks
    """
    repeat_name = os.path.basename(repeat_folder)
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing repeat: {repeat_name}")
    logger.info(f"{'='*60}")
    
    # Create output directory
    output_dir = os.path.join(repeat_folder, "Output_Bubble_Filter")
    os.makedirs(output_dir, exist_ok=True)
    
    # Calculate SD values for all tracks
    logger.info(f"Calculating SD for {len(track_folders)} tracks...")
    identifiers = []
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(calculate_sd, track) for track in track_folders]
        for future in futures:
            result = future.result()
            if result is not None:
                identifiers.append(result)
    
    if not identifiers:
        logger.error(f"No valid SD values calculated for {repeat_name}")
        return
    
    # Create DataFrame
    sd_summary_df = pd.DataFrame(identifiers)
    
    # Save SD Summary
    sd_summary_csv = os.path.join(output_dir, 'SD_Summary.csv')
    sd_summary_df.to_csv(sd_summary_csv, index=False)
    logger.info(f"SD Summary saved to {sd_summary_csv}")
    
    # Perform clustering
    sd_summary_df, used_threshold = sd_threshold_clustering(sd_summary_df, threshold)
    
    # Save clustering results
    clustering_csv = os.path.join(output_dir, 'Clustering_Results.csv')
    sd_summary_df.to_csv(clustering_csv, index=False)
    logger.info(f"Clustering Results saved to {clustering_csv}")
    
    # Create visualization
    visualize_clusters(sd_summary_df, output_dir, repeat_name)
    
    # Handle deletion/dry-run
    stationary_tracks = sd_summary_df[sd_summary_df['Cluster'] == 'Stationary']
    
    if len(stationary_tracks) == 0:
        logger.info("No stationary tracks to remove")
        return
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Stationary tracks identified: {len(stationary_tracks)}")
    logger.info(f"{'='*60}")
    
    if dry_run:
        logger.info("[DRY RUN MODE] The following tracks would be deleted:")
        for _, row in stationary_tracks.iterrows():
            logger.info(f"  - {row['ID']} (SD: {row['EuclideanNorm_SD(X,Y)']:.4f})")
    elif delete_mode:
        logger.warning("[DELETE MODE] Deleting stationary tracks...")
        deleted_count = 0
        for _, row in stationary_tracks.iterrows():
            track_path = row['Path']
            try:
                shutil.rmtree(track_path)
                logger.info(f"  ✓ Deleted: {row['ID']}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"  ✗ Failed to delete {row['ID']}: {e}")
        logger.info(f"Deleted {deleted_count}/{len(stationary_tracks)} stationary tracks")
    else:
        logger.info("[INFO] Stationary tracks identified (use --delete to remove):")
        for _, row in stationary_tracks.iterrows():
            logger.info(f"  - {row['ID']} (SD: {row['EuclideanNorm_SD(X,Y)']:.4f})")


def main():
    parser = argparse.ArgumentParser(
        description='Bubble Filter - Remove stationary tracks from nematode datasets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (default) - shows what would be deleted
  python bubble_filter.py --src elpiniki_data
  
  # Use current directory
  python bubble_filter.py --src .
  
  # Actually delete stationary tracks
  python bubble_filter.py --src . --delete
  
  # Use manual threshold instead of auto-detection
  python bubble_filter.py --src . --threshold 2.5
  
  # Combine manual threshold with deletion
  python bubble_filter.py --src . --threshold 2.5 --delete
        """
    )
    
    parser.add_argument(
        '--src',
        type=str,
        required=True,
        help='Path to the main dataset folder (e.g., elpiniki_data or . for current directory)'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=None,
        help='Manual SD threshold (default: auto-detect using first derivative method)'
    )
    
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Actually delete stationary tracks (default: dry-run mode)'
    )
    
    parser.add_argument(
        '--fps',
        type=float,
        default=10.0,
        help='Frame rate for video data (default: 10 fps)'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not os.path.isdir(args.src):
        logger.error(f"Error: Input directory does not exist: {args.src}")
        sys.exit(1)
    
    # Determine mode
    dry_run = not args.delete
    mode_str = "DRY RUN" if dry_run else "DELETE"
    threshold_str = f"{args.threshold:.4f}" if args.threshold else "AUTO"
    
    # Print configuration
    logger.info("="*60)
    logger.info("BUBBLE FILTER - Configuration")
    logger.info("="*60)
    logger.info(f"Input directory: {args.src}")
    logger.info(f"Mode: {mode_str}")
    logger.info(f"Threshold: {threshold_str}")
    logger.info(f"FPS: {args.fps}")
    logger.info("="*60)
    
    if dry_run:
        logger.info("Running in DRY RUN mode - no files will be deleted")
    else:
        logger.warning("Running in DELETE mode - stationary tracks will be permanently removed!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            sys.exit(0)
    
    # Find all track folders grouped by repeat
    track_folders = find_track_folders(args.src)
    
    if not track_folders:
        logger.error("No track folders found! Make sure folders contain track.tif files")
        sys.exit(1)
    
    # Process each repeat
    for repeat_folder, tracks in track_folders.items():
        try:
            process_repeat(repeat_folder, tracks, args.threshold, dry_run, args.delete)
        except Exception as e:
            logger.error(f"Error processing {repeat_folder}: {e}", exc_info=True)
            continue
    
    logger.info("\n" + "="*60)
    logger.info("Processing complete!")
    logger.info("="*60)


if __name__ == "__main__":
    main()
