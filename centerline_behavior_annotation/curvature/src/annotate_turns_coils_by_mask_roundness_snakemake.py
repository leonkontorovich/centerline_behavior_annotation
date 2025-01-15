"""
This script analyzes particle roundness in microscopy images using a novel roundness parameter R
developed by Takashimizu & Iiyoshi (2016). The parameter R combines circularity with aspect ratio
correction to provide a more accurate measure of true roundness than circularity alone.

R = Circularity + (0.913 - CAR)
where:
- Circularity = 4π × Area/Perimeter²
- CAR = Circularity Aspect Ratio correction (6th degree polynomial)
- 0.913 = maximum circularity value for a perfect circle

References:
Takashimizu, Y., & Iiyoshi, M. (2016). New parameter of roundness R: circularity corrected by 
aspect ratio. Progress in Earth and Planetary Science, 3(2).
"""

import argparse
import pandas as pd
import numpy as np
import cv2
import dask.array as da
from imutils import MicroscopeDataReader


def calculate_CAR(aspect_ratio):
    AR = aspect_ratio
    return (0.826261 + 0.337479 * AR - 0.335455 * AR ** 2 +
            0.103642 * AR ** 3 - 0.0155562 * AR ** 4 +
            0.00114582 * AR ** 5 - 0.0000330834 * AR ** 6)


def calculate_roundness(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return 0, 0, area

    circularity = 4 * np.pi * (area / (perimeter * perimeter))
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w) / h if h > 0 else np.nan

    if np.isnan(aspect_ratio):
        return 0, 0, area

    CAR = calculate_CAR(aspect_ratio)
    roundness = circularity + (0.913 - CAR)
    return roundness, circularity, area


def annotate_behavior(mask, min_threshold, max_threshold, min_area=10, max_area=float('inf')):
    try:
        mask_cv = (mask * 255).astype(np.uint8)
        contours = cv2.findContours(mask_cv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[-2] if len(contours) == 3 else contours[0]

        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            hull = cv2.convexHull(largest_contour)
            roundness, _, area = calculate_roundness(hull)
            raw_area = cv2.contourArea(largest_contour)

            if not (min_area <= raw_area <= max_area):
                return {
                    'turn': 0,
                    'roundness_mask_convex_hull': 0,
                    'mask_area': raw_area,
                    'convex_hull_area': cv2.contourArea(hull)
                }

            behavior = 1 if min_threshold <= roundness <= max_threshold else 0
            return {
                'turn': behavior,
                'roundness_mask_convex_hull': roundness,
                'mask_area': raw_area,
                'convex_hull_area': cv2.contourArea(hull)
            }
        else:
            return {
                'turn': 0,
                'roundness_mask_convex_hull': 0,
                'mask_area': 0,
                'convex_hull_area': 0
            }

    except Exception as e:
        print(f"Error processing contours: {str(e)}")
        return {
            'turn': 0,
            'roundness_mask_convex_hull': 0,
            'mask_area': 0,
            'convex_hull_area': 0
        }


def binarize_turn_from_roundness(df, window_size, min_threshold, max_threshold):
    df_copy = df.copy()
    df_copy['roundness_mask_convex_hull'] = df_copy['roundness_mask_convex_hull'].rolling(
        window=window_size, center=True, min_periods=1
    ).mean()
    df_copy['turn'] = ((df_copy['roundness_mask_convex_hull'] >= min_threshold) &
                       (df_copy['roundness_mask_convex_hull'] <= max_threshold)).astype(int)
    return df_copy


def main(arg_list):
    parser = argparse.ArgumentParser()
    parser.add_argument('-input', '--input', help='path to the input_mask_stack', required=True)
    parser.add_argument('-min_t', '--min_round_threshold', help='min threshold of roundness for behavior', type=float,
                        required=True)
    parser.add_argument('-max_t', '--max_round_threshold', help='max threshold of roundness for behavior', type=float,
                        required=True)
    parser.add_argument('-window', '--smoothing_window', help='size of smoothing window', type=int, default=10)
    parser.add_argument('-output_file', '--beh', help='path to the behavioural output', required=True)
    parser.add_argument('-min_worm_area', '--min_area', help='minimum area threshold for raw mask', type=float,
                        required=True)
    parser.add_argument('-max_worm_area', '--max_area', help='maximum area threshold for raw mask', type=float,
                        required=True)

    args = parser.parse_args(arg_list)

    reader_obj = MicroscopeDataReader(args.input, as_raw_tiff=True, raw_tiff_num_slices=1)
    tif = da.squeeze(reader_obj.dask_array)

    annotations = []
    for i, page in enumerate(tif):
        img = np.array(page)
        result = annotate_behavior(img, args.min_round_threshold, args.max_round_threshold,
                                   args.min_area, args.max_area)
        annotations.append(result)

    df = pd.DataFrame(annotations)
    df = binarize_turn_from_roundness(df, args.smoothing_window, args.min_round_threshold, args.max_round_threshold)
    df.to_csv(args.beh, index=True)
    print(f"Saved behavior annotations to {args.beh}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
