"""
This is an uncomplete collection of functions that convert different shapes of manual behavior annotation files into one
another. Since people like to use their own version of annotation files for the sake of efficiency, it should be simple
to convert them to a different format as well as to a universaL format:


here are examples of different shapes that are currently in use
.......................................................................................................................

start_end: one behavior, Itamar uses it for rev. annotation (last frame unknown!!)

    | start              | end              |
    -------------------------------------------
    |(start frame: int)  | (end frame: int) |

.......................................................................................................................

endpoint: multiple mutually exclusive behaviors, Eva uses it for quiescence annotation

    | end                | behavior          |
    -------------------------------------------
    |(end frame: int)   | (behavior 1: str) |
    -------------------------------------------
    |(end frame: int)   | (behavior 2: str) |
    -------------------------------------------
    |(end frame: int)   | (behavior 3: str) |

.......................................................................................................................

framewise: multiple mutually exclusive behaviors, each row represents one frame, Eva uses it for quiescence annotation

                | manual_behavior     |
                -----------------------
      frame 0   | (behavior 1: str)   |
                -----------------------
      frame 1   | (behavior 2: str)   |
                -----------------------
      ...       | (behavior 2: str)   |


.......................................................................................................................

combined_binary: multiple behaviors, can be overlapping. Each column represents a behavior, each row a frame. 0 and 1
                indicate if a behavior is False (0) or True (1) at a specific frame


                | behavior 1   | behavior 2   | behavior 3   |
                ----------------------------------------------
      frame 0   | 0            | 1            | 0            |
                ----------------------------------------------
      frame 1   | 0            | 1            | 1            |
                ----------------------------------------------
      ...       | 0            | 0            | 0            |

.......................................................................................................................

"""
import numpy as np
import pandas as pd
import os


def convert_endpoint_to_framewise(input_path, delimiter=","):
    # Check if input file path exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path {input_path} does not exist.")

    # Read file
    if input_path.endswith('.xlsx') or input_path.endswith('.xls'):
        annotation_df = pd.read_excel(input_path)
    else:
        annotation_df = pd.read_csv(input_path, delimiter=delimiter)

    # Find the total number of frames
    last_frame = annotation_df['end'].max()

    # Initialize a NumPy array
    manual_behavior_array = np.empty(last_frame + 1, dtype=object)
    manual_behavior_array[:] = None  # start with None (or '' if you prefer)

    # Assign behaviors
    prev_index = 0
    ends = annotation_df['end'].to_numpy()
    behaviors = annotation_df['behavior'].to_numpy()

    for end_index, behavior in zip(ends, behaviors):
        manual_behavior_array[prev_index:end_index+1] = behavior
        prev_index = end_index + 1

    # Create DataFrame
    framewise_df = pd.DataFrame({'manual_behavior': manual_behavior_array})

    return framewise_df

def convert_framewise_to_combined_binary(input_path, delimiter=","):
    """
    Converts a framewise annotation (one behavior per frame) into combined binary format
    (one column per behavior, 1 = active, 0 = not active).
    """

    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path {input_path} does not exist.")


    framewise_df = pd.read_csv(input_path, delimiter=delimiter)

    if 'manual_behavior' not in framewise_df.columns:
        raise ValueError("Input file must contain a 'manual_behavior' column.")

    # Find unique behaviors (ignore NaN)
    unique_behaviors = framewise_df['manual_behavior'].dropna().unique()

    combined_binary_df = pd.DataFrame(0, index=framewise_df.index, columns=unique_behaviors)

    for behavior in unique_behaviors:
        combined_binary_df.loc[framewise_df['manual_behavior'] == behavior, behavior] = 1

    return combined_binary_df