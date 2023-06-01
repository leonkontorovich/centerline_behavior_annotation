# code to detect self touch

import numpy as np
import tifffile as tiff
import pandas as pd
import os
import matplotlib.pyplot as plt
from imutils.src.imfunctions import *
import glob

#THE idea is to generate a timeseries with 0 i f the worm is not self touching and 1 if the worm is self touching
# This should be based on the find contours function in imutils

def find_specific_contours_with_specific_children(img, external_contour_area, internal_contour_area):
    """
    Inspired by imutils.src.imfunctions.extract_contours_with_children()
    :return:
    """

    # important, findCountour() has different outputs depending on CV version! _, cnts, hierarchy or cnts, hierarchy
    _, cnts, hierarchy = cv2.findContours(img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    specific_contours_with_specific_children = []

    for cnt_idx, cnt in enumerate(cnts):
        # draw contours with children: last column in the array is -1 if an external contour, column 2 is different than -1 meaning it has children
        if hierarchy[0][cnt_idx][3] == -1 and hierarchy[0][cnt_idx][2] != -1:
            #contours_with_children.append(cnt)

            area = cv2.contourArea(cnt)

            # check if the contours with children have an area between the external_cnt_area
            if external_contour_area[0] < area < external_contour_area[1]:
                # find the rows of an array where the 3rd column is equal to cnt_idx
                new_array = np.where(hierarchy[0][:, 3] == cnt_idx)
                for child_cnt_idx in new_array:
                    child_cnt_area = cv2.contourArea(cnts[child_cnt_idx[0]])

                    if internal_contour_area[0] < child_cnt_area < internal_contour_area[1]:
                        specific_contours_with_specific_children.append(cnt)

    return specific_contours_with_specific_children

def stack_self_touch(binary_path, external_contour_area, internal_contour_area):
    """
    This function was written to detect self touch in worm, which will form a contour with children.
    :param binary_path: path to the binary stack image
    :param external_contour_area: area range of the external contour (min and max), e.g. [7000, 20000]
    :param internal_contour_area: area range the internal contour (min and max), e.g. [100, 2000]
    """
    df = pd.DataFrame(columns=['self_touch'])

    with tiff.TiffFile(binary_path) as tif_binary:
        for i, page in enumerate(tif_binary.pages):
            img = page.asarray()
            contours_with_children = find_specific_contours_with_specific_children(img, external_contour_area, internal_contour_area)
            if contours_with_children:
                print('self touch')
                df.append({'self_touch': 1}, ignore_index=True)
            else:
                print('no self touch')
                df.append({'self_touch': 0}, ignore_index=True)
    return df