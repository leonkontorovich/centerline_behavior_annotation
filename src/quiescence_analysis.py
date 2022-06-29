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


from math import floor
def get_average_worm_area(img, fraction_frames: float = 0.3, debug: bool = False):
    """
    recieves an binarize image stack, make sure it has at least 3 dimentions.
    measures the average worm size (area in pixels),
    to save processing time takes only fraction of all frames defined in fraction_frames
    """

    # make sure image is shape is usable
    if len(img.shape) < 3:
        if debug: print("image file currupt, less than 3 dimentions")
        return None

    # calculate which frames to take
    total_frames = img.shape[2]
    if fraction_frames < 0.01 or fraction_frames > 1:
        fraction_frames = 0.3
    frames_interval = floor(total_frames / (total_frames * fraction_frames))
    frames_range = range(0, total_frames, frames_interval)
    total_frames_taken = len(frames_range)
    # initialize numpy array to hold area data
    measured_area = np.empty(total_frames_taken)
    measured_area[:] = np.nan

    # loop over frames and get area
    for idx, i in enumerate(frames_range):
        curr_frame = img[:, :, idx]
        # -get main segment
        labeles = label(curr_frame)
        segments = regionprops(labeles)
        # make sure there's only one segment..
        # Itamar we could implement take the biggest if there's more than one
        if len(segments) == 1:
            measured_area[idx] = segments[0].area
        else:
            # skip if there's not one clear object
            continue

    average_worm_area = np.nanmean(measured_area)

    if np.isnan(average_worm_area):
        if debug: print("problem with getting worm average size")
        return None

    return average_worm_area

