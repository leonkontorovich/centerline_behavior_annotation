import pandas as pd
import numpy as np
import os


#read skeleton files
#write h5 file multiindex
# format:
# level 0: bodysegment 1, .. 100 or more
# level 1: x, y, k


main_path = '/Users/ulises.rey/local_data/centerline/worm3_skeleton/2021-03-04_16-17-30_worm3_'

df_splineX = pd.read_csv(main_path + 'spline_X_coords.csv', header=None)

df_splineY = pd.read_csv(main_path + 'spline_Y_coords.csv', header=None)

df_splineK = pd.read_csv(main_path + 'spline_K.csv', header=None)


l=[df_splineX,df_splineY,df_splineK]

new_df = pd.concat(l, keys= ['x', 'y', 'k'], names= ["coords", "segment"], axis=1)

new_df.swaplevel(0, 1, axis=1).sort_index(axis=1)

new_df.to_csv(main_path + 'skeleton_spline_merged.csv')


