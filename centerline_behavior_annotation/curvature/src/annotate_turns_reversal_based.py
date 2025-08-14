# This script was written so that it matches the current snakemake pipeline with files as inputs and outputs
# If you want to run it per folder there is the annotate_behaviour.py file

import argparse
import pandas as pd
import numpy as np
import os


def annotate_turns_from_reversal_ends(rev_ends: pd.DataFrame, y_curvature: pd.Series,
                                      min_event_length: int = 24) -> tuple:
    """
    a temporary function that uses the reversal ends and curvature to annotate turns in the following way:
    1. A turn starts at the end of the reversal
    2. A turn ends at the next zero crossing of the curvature
    3. If the curvature is positive at the end of the reversal, it is a ventral turn, otherwise dorsal
    Parameters
    ----------
    rev_ends
    y_curvature
    Returns
    -------
    """
    ventral_starts = []
    ventral_ends = []
    dorsal_starts = []
    dorsal_ends = []
    sign_flips = np.where(np.diff(np.sign(y_curvature)))[0]

    for idx, e in enumerate(rev_ends):
        if e == len(y_curvature):
            break
        next_e = rev_ends[idx + 1] if idx + 1 < len(rev_ends) else len(y_curvature)

        # Determines ventral or dorsal turn
        # check if e is within the bounds of y_curvature
        if e >= len(y_curvature):
            continue
        y_initial = y_curvature.iat[e]  # Should I change this if there is a collision?

        # Get the next approximate zero crossing
        next_flip_array = sign_flips[
            sign_flips > e]  # TODO: if there is not good curvature data, then multiple reversals will have the same flip point.
        if len(next_flip_array) == 0:
            break
        i_next_flip = next_flip_array[0] + 1

        # check events are long enough
        if i_next_flip - e < min_event_length and len(next_flip_array) > 1:
            i_next_flip = next_flip_array[1] + 1
            if i_next_flip - e < min_event_length:
                continue

        # check events are not too long
        if i_next_flip > next_e:
            continue

        if i_next_flip > 1:
            if np.sign(y_initial) > 0:
                ventral_starts.append(e)
                ventral_ends.append(i_next_flip)
            else:
                dorsal_starts.append(e)
                dorsal_ends.append(i_next_flip)

    ventral_turns = pd.DataFrame({'start': ventral_starts, 'end': ventral_ends})
    dorsal_turns = pd.DataFrame({'start': dorsal_starts, 'end': dorsal_ends})
    return ventral_turns, dorsal_turns


def get_contiguous_blocks_from_column(boolean_series, already_boolean=False):
    """
    Extract start and end indices of contiguous blocks of True values
    """
    if not already_boolean:
        boolean_series = boolean_series.astype(bool)

    # Find transitions
    diff = np.diff(np.concatenate(([False], boolean_series, [False])).astype(int))
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0] - 1

    return starts, ends


def extract_reversal_ends_from_behavioral_annotation(beh_annotation_df, reversal_state=-1):
    """
    Extract reversal end points from behavioral annotation dataframe using contiguous blocks
    Similar to get_starts_and_ends_of_behavior method
    """
    # Behavioral annotation is in the SECOND column (index 1), not the first
    beh_values = beh_annotation_df.iloc[:, 1] if hasattr(beh_annotation_df.iloc[:, 1],
                                                         'values') else beh_annotation_df.iloc[:, 1]

    # Create boolean series where behavior equals reversal state
    y_rev = (beh_values == reversal_state)

    # Get contiguous blocks
    rev_starts, rev_ends = get_contiguous_blocks_from_column(y_rev, already_boolean=True)

    return rev_starts, rev_ends


def calculate_curvature_from_spline(spline_data, initial_segment, final_segment, avg_window):
    """
    Calculate curvature from spline data following summed_curvature_from_kymograph logic
    """
    # Apply smoothing
    spline_smoothed = spline_data.rolling(avg_window, center=True).mean()

    # Extract features (body segments)
    features = np.arange(initial_segment, final_segment)
    data = spline_smoothed.loc[:, features].values

    # Mean across segments (not sum!) - this matches summed_curvature_from_kymograph
    y_curvature = data.mean(axis=1)

    # Fill any NaN values with 0
    y_curvature = pd.Series(y_curvature).fillna(0)

    return y_curvature


def main(arg_list):
    parser = argparse.ArgumentParser()
    parser.add_argument('-spline', '--spline_input', help='path to the spline K csv file', required=True)
    parser.add_argument('-beh_ann', '--beh_annotation', help='path to the behavioral annotation csv file',
                        required=True)
    parser.add_argument('-t', '--threshold', help='threshold on the curvature', type=float, required=True)
    parser.add_argument('-i_s', '--initial_segment', help='initial body segment for curvature calculation', type=int,
                        required=True)
    parser.add_argument('-f_s', '--final_segment', help='final body segment for curvature calculation', type=int,
                        required=True)
    parser.add_argument('-avg_window', '--averaging_window', help='smoothing window size', type=int, required=True)

    parser.add_argument('-min_event_length', '--min_event_length', help='minimum length for turn events', type=int,
                        default=24)
    parser.add_argument('-output', '--output', help='path to the turn annotation output', required=True)

    args = vars(parser.parse_args(arg_list))
    spline_path = args['spline_input']
    beh_annotation_path = args['beh_annotation']
    threshold = args['threshold']
    initial_segment, final_segment = args['initial_segment'], args['final_segment']
    avg_window = args['averaging_window']
    curvature_type = args.get('curvature_type', 'mean')  # Default to mean calculation
    min_event_length = args['min_event_length']
    output_path = args['output']

    print(f"Processing spline data from: {spline_path}")
    print(f"Processing behavioral annotation from: {beh_annotation_path}")
    print(f"Curvature calculation: segments {initial_segment}-{final_segment}, using mean across segments")
    print(f"Smoothing window: {avg_window}")
    print(f"Threshold: {threshold}")

    # Load spline data (skeleton curvature data)
    if not os.path.exists(spline_path):
        raise FileNotFoundError(f"Spline file not found: {spline_path}")

    spline_df = pd.read_csv(spline_path, header=None, encoding='utf-8')
    spline_df.fillna(0, inplace=True)
    print(f"Loaded spline data with shape: {spline_df.shape}")

    # Load behavioral annotation data
    if not os.path.exists(beh_annotation_path):
        raise FileNotFoundError(f"Behavioral annotation file not found: {beh_annotation_path}")

    beh_df = pd.read_csv(beh_annotation_path, header=None, encoding='utf-8')
    print(f"Loaded behavioral annotation with shape: {beh_df.shape}")

    # Calculate curvature from spline data using mean across segments
    y_curvature = calculate_curvature_from_spline(
        spline_df, initial_segment, final_segment, avg_window
    )
    print(f"Calculated curvature with {len(y_curvature)} timepoints")

    # Extract reversal ends from behavioral annotation
    rev_starts, rev_ends = extract_reversal_ends_from_behavioral_annotation(beh_df, reversal_state=-1)
    print(f"Found {len(rev_ends)} reversal episodes")
    print(f"Reversal start indices: {rev_starts[:5]}..." if len(rev_starts) > 0 else "No reversals found")
    print(f"Reversal end indices: {rev_ends[:5]}..." if len(rev_ends) > 0 else "No reversals found")

    if len(rev_ends) > 0:
        # Apply turn detection from reversal ends
        ventral_turns, dorsal_turns = annotate_turns_from_reversal_ends(
            rev_ends,
            y_curvature,
            min_event_length=min_event_length
        )

        print(f"Detected {len(ventral_turns)} ventral turns and {len(dorsal_turns)} dorsal turns")

        # Create output dataframe with detailed turn annotations
        turns_df = pd.DataFrame({'turn': np.zeros(len(y_curvature), dtype=int)})

        # Mark ventral turns as 1
        for _, row in ventral_turns.iterrows():
            start_idx, end_idx = int(row['start']), int(row['end'])
            if end_idx < len(turns_df):
                turns_df.loc[start_idx:end_idx, 'turn'] = 1

        # Mark dorsal turns as -1
        for _, row in dorsal_turns.iterrows():
            start_idx, end_idx = int(row['start']), int(row['end'])
            if end_idx < len(turns_df):
                turns_df.loc[start_idx:end_idx, 'turn'] = -1

        print(f"Turn annotation summary:")
        print(f"  Ventral turns (1): {(turns_df['turn'] == 1).sum()} timepoints")
        print(f"  Dorsal turns (-1): {(turns_df['turn'] == -1).sum()} timepoints")
        print(f"  No turns (0): {(turns_df['turn'] == 0).sum()} timepoints")

    else:
        print("No reversal ends found, creating empty turn annotations")
        turns_df = pd.DataFrame({'turn': np.zeros(len(y_curvature), dtype=int)})

    # Save turn annotations
    turns_df.to_csv(output_path, encoding='utf-8', index=True)
    print(f"Turn annotations saved to: {output_path}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])