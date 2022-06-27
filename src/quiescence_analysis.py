#imports

import os
import numpy as np
import cv2
import tifffile as tiff

def load_tiff(input_filename:str):
    """
    this function uses tiffile package to load a tiff file to memory
    :param filepath: str, path to the binarized image file
    :return:
    loaded numpy img object
    """
    with tiff.TiffFile(input_filename) as tif:
        for i, page in enumerate(tif.pages):
            if i == 0:
                img_shape = page.asarray().shape
                img = np.empty((img_shape[0], img_shape[1], 1))
            img = np.dstack((page.asarray(), img))
    return img

def get_frame_diff(img,frame_shift:int=3,contour_size_thresh:float=1.5):
    ### 1. get binarized frame and frame +3
    ### 2. make diff between the two binarized frames
    ### 3. find contours in the diff image
    ### 4. filter contours based on size/ area (make histogram of contour sizes, decide on threshold)
    ### 5. calculate the sum of area(#pixels) all relevent (i.e., big enough) contours
    ### 6. divide pixel_change by time (input fps.. to know)
    ### ------
    ### 7. save information in some format

    #intialize array to hold the data
    frame_diff_arr = np.empty(img.shape[3])

    #iterate over frames
    for idx in range(0, img.shape[3] - frame_shift):
        #get the two frames
        frame = img[:, :, idx]
        next_frame = img[:, :, idx + frame_shift]
        #calcualte the diff between frames, take absolute diff
        frames_diff = np.abs(next_frame - frame)
        #get contours
        contours, hierarchy = cv2.findContours(frames_diff, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        #filter contours
        filtered_contours = filter_contours(contours,contour_size_thresh)
        #calculate pixel_diff
        curr_pixel_diff = calculate_pixel_diff(filtered_contours)
        frame_diff_arr[idx] = curr_pixel_diff

    return frame_diff_arr

