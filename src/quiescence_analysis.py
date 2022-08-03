# imports

import numpy as np
import tifffile as tiff
from skimage.measure import label, regionprops
from scipy.stats import zscore


def get_frame_diff(img_path, frame_shift: int = 3, norm_size_threshold: float = 0.4, centroid=None,
                   debug: bool = False):
    """
    Calculates difference in pixels between two time points
    it recieves a binarized image and outputs a numpy array of pixel_diffs

    Parameters:
    ----------
    img:nd.array
        8 bit binarized image series
    frame_shift:int
        shift in time to calculate pixel difference
    norm_size_threshold: float
        threshold to remove small object noise
    """

    # decide if frame cropping should be corrected
    # if centroid is given then correct frame croping
    if centroid is not None:
        fix_crop = True

    # get reference size
    ref_size = get_average_ref_area(img_path, fraction_frames=0.1)
    tiff_read_buffer = frame_shift + 1
    if debug: print("ref size is", ref_size)

    # read binarized image in a buffered manner
    with tiff.TiffFile(img_path) as tif:
        # get tiff stats
        frames_num = len(tif.pages)
        img_temp = tif.pages[0].asarray()
        img_shape = (tiff_read_buffer,) + (img_temp.shape)
        if debug: print("image shape", img_shape)
        if debug: print("frame num", frames_num)
        # initialize
        # -buffered img
        img = np.zeros(img_shape, dtype=np.int16)

        # -array to hold the results
        frame_diff_arr = np.zeros(frames_num)
        frame_diff_arr[:] = np.nan
        buffer_idxs = [''] * tiff_read_buffer

        # iterate over frames
        for idx, page in enumerate(tif.pages):
            if debug: print("idx", idx)
            # preload first batch of stacks
            if idx < tiff_read_buffer - 1:
                img[idx] = page.asarray()
                buffer_idxs[idx] = idx
                if debug: print("idx skip", idx)
                continue

            # get idx for two frames to compare
            # -stop if last frame
            if idx == frames_num:
                if debug: print("idx is", idx, "stopped")
                break

            jdx = idx + 1
            frame_assign_idx = idx % tiff_read_buffer
            frame_reference_idx = jdx % tiff_read_buffer
            next_frame_idx = (tiff_read_buffer + jdx - 1) % tiff_read_buffer

            # insert frame
            img[frame_assign_idx] = page.asarray()
            # keep the idx of the inserted frame
            buffer_idxs[frame_assign_idx] = idx

            if debug: print("frames set")
            # define frames to compare
            frame = img[frame_reference_idx]
            next_frame = img[next_frame_idx]
            # get original frame indexes
            abs_frame_idx = buffer_idxs[frame_reference_idx]
            abs_next_frame_idx = buffer_idxs[next_frame_idx]

            # fix frames based of centroid if needed
            if fix_crop:
                next_frame = get_fixed_crop_based_on_centroid(frame, next_frame, centroid[abs_frame_idx],
                                                              centroid[abs_next_frame_idx], debug=debug)
            # calculate pixel diff
            curr_pixel_diff = calculate_pixel_diff(frame, next_frame, ref_size, norm_size_threshold, debug=debug)

            if debug: print("current idx", idx, "pixel_diff", curr_pixel_diff)
            # save pixel diff into array
            frame_diff_arr[idx] = curr_pixel_diff

    # remove NaNs
    frame_diff_arr = frame_diff_arr[~np.isnan(frame_diff_arr)]

    return frame_diff_arr


def get_fixed_crop_based_on_centroid(frame, next_frame, centroid, next_centroid, debug: bool = False):
    """
    Fixes the cropping frames. For the times when the cropping function used int converted positions for its cropping

    :param frame: numpy array current frame
    :param next_frame:  numpy array next frame to be analyzed
    :param centroid: float, the centroid position of current frame
    :param next_centroid: float, the centroid position of the next frame
    :param debug: boolean, should print out debug?
    :return:
    fixed_next_frame: numpy array, corrected cropping of next frame based on current
    """

    # organize x,y diff
    shape_frame = frame.shape
    max_x = shape_frame[1]
    max_y = shape_frame[0]

    x = int(centroid[0])
    y = int(centroid[1])
    x2 = int(next_centroid[0])
    y2 = int(next_centroid[1])

    diff_x = x2 - x
    diff_y = y2 - y

    if debug: print("original diff_x", diff_x, "diff_y", diff_y)

    if diff_x == 0 and diff_y == 0:
        return next_frame

    # initialize ranges
    x_range_src = (0, max_x)
    y_range_src = (0, max_y)
    x_range_dst = (0, max_x)
    y_range_dst = (0, max_y)

    # calculate ranges based on sign of diff
    if diff_x > 0:
        x_range_src = (0, max_x - diff_x)
        x_range_dst = (diff_x, max_x)
        if debug: print("x range src", x_range_src, "x range dst", x_range_dst)
    if diff_x < 0:
        x_range_src = (0 - diff_x, max_x)
        x_range_dst = (0, max_x + diff_x)
        if debug: print("x range src", x_range_src, "x range dst", x_range_dst)
    if diff_y > 0:
        y_range_src = (0, max_y - diff_y)
        y_range_dst = (diff_y, max_y)
    if diff_y < 0:
        y_range_src = (0 - diff_y, max_y)
        y_range_dst = (0, max_y + diff_y)

    fixed_next_frame = np.zeros_like(frame)
    fixed_next_frame[y_range_dst[0]:y_range_dst[1], x_range_dst[0]:x_range_dst[1]] = next_frame[
                                                                                     y_range_src[0]:y_range_src[1],
                                                                                     x_range_src[0]:x_range_src[1]]

    return fixed_next_frame

from math import floor

def get_average_ref_area(img_path: str, fraction_frames: float = 0.1, debug: bool = False):
    """
    recieves an binarize image stack, make sure it has at least 3 dimentions.
    measures the average worm size (area in pixels),
    to save processing time takes only fraction of all frames defined in fraction_frames

    Parameters:
    -----------
    img_path:str
    fraction_frames: float
    debug:bool
    """

    with tiff.TiffFile(img_path) as tif:
        total_frames = len(tif.pages)

        # calculate which frames to take
        if fraction_frames < 0.01 or fraction_frames > 1:
            fraction_frames = 0.1
            if debug: print("fraction does not match >0.01<1, 0.1 was chosen as default")
        frames_interval = floor(total_frames / (total_frames * fraction_frames))
        frames_range = range(0, total_frames, frames_interval)
        total_frames_taken = len(frames_range)

        # -initialize numpy array to hold area data
        measured_area = np.empty(total_frames_taken)
        measured_area[:] = np.nan
        jdx=0

        # iterate over frames
        for idx, page in enumerate(tif.pages):
            # skip frame if not in range
            if idx not in frames_range:
                continue
            # take frame
            curr_frame = page.asarray().astype(np.int16)

            # get main segment
            labeles = label(curr_frame)
            segments = regionprops(labeles)

            # make sure there's only one segment..
            # COMMENT: we could implement take the biggest if there's more than one
            if len(segments) == 1:
                measured_area[jdx] = segments[0].area
            else:
                # skip if there's not one clear object
                continue
            jdx+=1

    average_ref_area = np.nanmean(measured_area)
    if np.isnan(average_ref_area):
        if debug: print("problem with getting worm average size")
        return None

    return average_ref_area

def get_segments_area(segments,debug:bool=False):
    """
    segments: skimage label object
    size_threshold: int
        threshold for area to take
    """

    # use skimage to get properties of segments
    segments_props = regionprops(segments)
    if debug:print(".......segment area",len(segments),"segments")
    # initialize
    segments_area = np.zeros(len(segments_props))
    # loop over segments to get sizes
    for idx, segment_prop in enumerate(segments_props):
        segments_area[idx] = segment_prop.area

    # filter sizes
    #     filtered_segments_area = segments_area[segments_area>threshold]
    #     I decided better to filter outside this function
    #     print(segments_area)
    return segments_area


def calculate_pixel_diff(frame, next_frame, ref_size, norm_size_threshold,debug:bool=False):
    """
    Calculates the difference in amount of pixels between two images
    ignores small changes set by norm_size_threshold
    takes into account a reference size to normalize data to fraction of reference size

    Parameters:
    -----------
    frame: nd.array
        2d image frame
    next_frame: nd.array
        2d image frame
    ref_size: float
        reference size to normalize pixel area to
    norm_size_threshold: float
        threshold for ignoring small differences, given as fraction of reference size

    """

    # calcualte the diff between frames, take absolute diff
    frames_diff = np.abs(next_frame - frame)
    if debug: print("...calc pixel diff - total diff",frames_diff.sum())
    # get segments
    segments = label(frames_diff)
    # get area
    segments_area = get_segments_area(segments,debug=debug)
    # normalize to reference size (worm size)
    norm_segments_area = (segments_area / ref_size) * 100
    # filter segments
    filtered_segments_area = norm_segments_area[norm_segments_area > norm_size_threshold]
    if debug:print("...calc pixel diff - filtered segments area",filtered_segments_area)
    # calculate pixel_diff
    pixel_diff = np.nansum(filtered_segments_area)

    return pixel_diff

### functions used only during development of this package ###

def load_tiff(input_filename: str):
    """
    this function uses tiffile package to load a tiff file to memory
    :param filepath: str, path to the binarized image file
    :return:
    loaded numpy img object
    """
    with tiff.TiffFile(input_filename) as tif:
        img = tif.pages[0].asarray()
        shape = (len(tif.pages),) + (img.shape)
        img = np.empty(shape, dtype=np.int16)
        for i, page in enumerate(tif.pages):
            img[i] = page.asarray()
    return img

def get_segment_area_stats(img,frame_shift:int=3):
    """
    A temporary function used just to accumualte data for later estimation of noise in this type of data
    recieves a binarized image stack and calculates the diff between frames
    returns an array with all the pixel diff events found
    """

    area_array = np.zeros(100)
    area_array[:] = np.nan
    segment_idx = 0

    for frame_idx in range(0, img.shape[0] - frame_shift):
        # get the two frames
        frame = img[frame_idx]
        next_frame = img[frame_idx + frame_shift]
        # calcualte the diff between frames, take absolute diff
        frames_diff = np.abs(next_frame - frame)
        # get segments
        segments = label(frames_diff)
        # measure all areas
        segments_props = regionprops(segments)

        for segment_prop in segments_props:
            area_array[segment_idx] = segment_prop.area
            segment_idx += 1
            if segment_idx == (area_array.shape[0]):
                add_array = np.zeros(100)
                add_array[:] = np.nan
                area_array = np.append(area_array, add_array)

    area_array = area_array[~np.isnan(area_array)]
    return area_array

def filter_with_zscore(arr:np.array,frame_diff_zscore_threshold:float):
    """
    simple function uses scipy stats zscore to filter numpy array
    :param input_arr: np.array
    :param frame_diff_zscore_threshold: float
    :return:
        filtered numpy array
    """

    arr[np.abs(zscore(arr) > frame_diff_zscore_threshold)] = np.nan

    return arr

def get_crop_positions_from_mat(mat,wormID:int):
    """
    gets a tracker als.mat file loaded using scipy, and a worm ID number
    and returns the centroid of the worm in a convinent format

    :param mat:
    :param wormID: int
    :return:
    """
    centroid = np.vstack((mat["Tracks"]["Path"][0, wormID][:, 0], mat["Tracks"]["Path"][0, wormID][:, 1])).T

    return centroid
