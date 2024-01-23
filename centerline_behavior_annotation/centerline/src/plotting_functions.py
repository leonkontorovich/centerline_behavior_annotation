# import pckgs
# Baed on Draw_centerline_with_colormap.ipynb in centerline/dev/

import cv2
import tifffile as tiff
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
from natsort import natsorted
import re
import csv
import seaborn as sns

from matplotlib import cm

import matplotlib.colors

from sklearn import preprocessing

import argh

def draw_centerline_wrapper(input_filename, skel_folder, output_filename, min_val, max_val, cmap_name):
    """"
    return a btf with a colored skeleton on top
    TODO: It is taking too many inputs, make it more modular
    """
    cmap = plt.get_cmap(cmap_name)

    # from skel_folder, load dataframes
    csv_path = skel_folder
    X_df = pd.read_csv(csv_path + '_spline_X_coords.csv', header=None)
    Y_df = pd.read_csv(csv_path + '_spline_Y_coords.csv', header=None)
    K_df = pd.read_csv(csv_path + '_spline_K.csv', header=None)

    # normalize Df_K (should be done outside this function?)
    # I am not sure if I should do this step
    scaler = preprocessing.MinMaxScaler()
    x_sample = [min_val, max_val]
    scaler.fit(np.array(x_sample)[:, np.newaxis])  # reshape data to satisfy fit() method requirements
    K_df_norm = scaler.transform(K_df)

    # loop
    with tiff.TiffWriter(output_filename, bigtiff=True) as tif_writer:
        with tiff.TiffFile(input_filename, multifile=False) as tif:
            for i, page in enumerate(tif.pages):  # [105600:114000]):
                # if i < 105600: continue  # print(i)
                img = page.asarray()
                # convert to BRG (3 channels)
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                # for every spline value
                for K_idx, K_value in enumerate(K_df_norm[i]):
                    # if there are nans (centerline does not exist, continue)
                    if np.isnan(X_df.iloc[i][K_idx]) == True: continue
                    x = int(X_df.iloc[i][K_idx])
                    y = int(Y_df.iloc[i][K_idx])

                    # normalize k value to 255, important to do it. 0.03 is close to the max value
                    K_color = cm.bwr(K_value)  # , bytes=True)
                    K_color = tuple([255 * x for x in K_color])  # if bytes=False

                    cv2.circle(img, (y, x), 3, K_color[:3], -1)
                    # plt.imshow(img)
                    # plt.show()
                tif_writer.write(img, contiguous=True)
                
                
# assembling:

parser = argh.ArghParser()
parser.add_commands([draw_centerline_wrapper])

# dispatching:

if __name__ == '__main__':
    parser.dispatch()