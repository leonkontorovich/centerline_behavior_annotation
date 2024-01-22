#import pckgs
import cv2
import tifffile as tiff
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import os
import shutil
from natsort import natsorted
import sys
import re

from scipy.interpolate import splprep, splev

from skimage.morphology import medial_axis, skeletonize
from skimage import data
from skimage.util import invert
import skimage.graph


#define functions

#define shortest_path function
def shortest_path(start,end,binary):
    costs=np.where(binary,1,1000)
    path, cost = skimage.graph.route_through_array(costs, start=start, end=end, fully_connected=False)
    return path,cost,costs


#load path
path='/groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/20200609/2020-06-09_15-53-33_chemotaxis_worm5-channel-0-/'
file='2020-06-09_15-53-33_chemotaxis_worm5-channel-0-_MMStack_1.ome.tif'
file_path=path+file

retval, mats=cv2.imreadmulti(file_path)
video=np.asarray(mats)
video.shape


#background image, obtained from fiji
#develop further to get a z-projection in here, or use a bg image generated in fiji
bg_path='/groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/20200609/2020-06-09_16-15-10_chemotaxis_worm5_bg-channel-0-/'
bg_file='MED_2020-06-09_16-15-10_chemotaxis_worm5_bg-channel-0-_MMStack.ome-1.tif'
bg_file_path=bg_path+bg_file
bg_img=cv2.imread(bg_file_path,0)
bg_img=cv2.bitwise_not(bg_img)
#show background
plt.subplot(1,2,1)
plt.imshow(bg_img,cmap='gray')
plt.title('(inv) background')