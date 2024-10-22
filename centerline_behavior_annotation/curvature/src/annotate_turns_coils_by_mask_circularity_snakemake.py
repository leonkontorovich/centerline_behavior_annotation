import argparse
import pandas as pd
import numpy as np
import cv2
import dask.array as da
from imutils import MicroscopeDataReader

def calculate_circularity(contour):
    """
    Calculate circularity of a contour.

    Circularity = 4 * π * (area / perimeter^2)

    1.0 indicates a perfect circle, < 1.0 indicates irregular shapes.
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0
    return 4 * np.pi * (area / (perimeter * perimeter))


def annotate_behavior(mask, min_threshold, max_threshold):
    """
    Annotate behavior based on circularity threshold range for a single mask.

    Args:
    mask (numpy.ndarray): A single binary mask image
    min_threshold (float): Minimum circularity threshold for behavior annotation
    max_threshold (float): Maximum circularity threshold for behavior annotation

    Returns:
    dict: A dictionary containing circularity and behavior annotation
    """
    # Convert dask array to numpy array if necessary
    if isinstance(mask, da.Array):
        mask = mask.compute()

    # Ensure mask is a proper 2D numpy array
    mask = np.array(mask, dtype=np.uint8)

    # Remove single-dimensional entries if present
    mask = np.squeeze(mask)

    # Ensure proper shape and type
    if len(mask.shape) > 2:
        return {'behavior': 0, 'circularity': 0}  # Return default values for invalid masks

    # Convert to cv2 format
    mask_cv = cv2.UMat(mask)

    try:
        contours, _ = cv2.findContours(mask_cv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            circularity = calculate_circularity(largest_contour)
            behavior = 1 if min_threshold <= circularity <= max_threshold else 0
        else:
            circularity = 0
            behavior = 0

    except Exception as e:
        print(f"Error processing contours: {str(e)}")
        circularity = 0
        behavior = 0

    return {'behavior': behavior, 'circularity': circularity}

def save_as_csv(df, output_path):
    """Save the DataFrame as a CSV file."""
    df.to_csv(output_path, index=True)

def main(arg_list):
    parser = argparse.ArgumentParser()
    parser.add_argument('-input', '--input', help='path to the input_mask_stack', required=True)
    parser.add_argument('-min_t', '--min_circ_threshold', help='min threshold of the circularity for behavior', type=float, required=True)
    parser.add_argument('-max_t', '--max_circ_threshold', help='max threshold of the circularity for behavior', type=float, required=True)
    parser.add_argument('-output_file', '--beh', help='path to the behavioural output', required=True)

    args = parser.parse_args(arg_list)

    reader_obj = MicroscopeDataReader(args.input, as_raw_tiff=True, raw_tiff_num_slices=1)
    tif = da.squeeze(reader_obj.dask_array)

    annotations = []
    for i, page in enumerate(tif):
        result = annotate_behavior(page, args.min_circ_threshold, args.max_circ_threshold)
        annotations.append({'frame': i, **result})

    df = pd.DataFrame(annotations)
    save_as_csv(df, args.beh)

    print(f"Saved behavior annotations to {args.beh}")

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])