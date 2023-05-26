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

def stack_extract_contours_with_children(binary_input_filepath):

    """
    Based on imutils.stack_extract_and_save_contours_with_children()
    :param binary_input_filepath: image from where the contours will be extracted
    :return: df
    """

    df = pd.DataFrame()

    with tiff.TiffFile(binary_input_filepath) as tif_binary:
        for i, page in enumerate(tif_binary.pages):
            img = page.asarray()

            big_contours_with_children = []
            # extract contours with children
            contours_with_children = extract_contours_with_children(img)

            # from contours_with_children list, remove the ones that have an area smaller than 100



            #for cnt in contours_with_children:
                #find the area of the contour
                # TODO: Should find the area of inner contour, not of the contour with children!
                # area = cv2.contourArea(cnt)
                # if area < 50:
                #     big_contours_with_children = big_contours_with_children + 1
            #print(len(contours_with_children))
            #append the length of the contours to the dataframe
            df = df.append({'contours': big_contours_with_children}, ignore_index=True)

    return df



if __name__ == "__main__":
    import argparse # comment
    import pandas as pd
    import numpy as np

    parser = argparse.ArgumentParser()
    parser.add_argument('-path', '--p', help='path to binary mask', required=True)
    parser.add_argument('-s', '--size', help='size threshold for inner contours', type=float, required=True)



    args = vars(parser.parse_args())
    path = args['path']
    size = args['size']

    df = stack_extract_contours_with_children(binary_input_filepath)
