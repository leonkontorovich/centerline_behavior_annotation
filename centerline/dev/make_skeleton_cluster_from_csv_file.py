import cv2
import tifffile as tiff
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import csv

import os
from natsort import natsorted
import re
import argparse

from scipy.interpolate import splprep, splev

from skimage.morphology import medial_axis, skeletonize
from skimage import data
from skimage.util import invert
import skimage.graph

from centerline.src.make_skeleton import make_skeleton

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input_filename", required=True, help="path to input image")
ap.add_argument("-csv_i", "--csv_i", required=True, help="path to the csv input file with the coordinates")
ap.add_argument("-n_splines", "--n_splines", required=True, help="Number of splines to fit")
ap.add_argument("-len", "--min_worm_length", required=True, help="minimum worm length")
#ap.add_argument("-csv_o", "--csv_o", required=True, help="path to the csv output filepath")

#I am writing for the purpose of the course

args = vars(ap.parse_args())

input_filename=args['input_filename']
print(input_filename)
print('\n')
csv_path=args['csv_i']
print(csv_path)
print('\n')
num_splines=int(args['n_splines'])
print(f'number of splines is {num_splines}')

#
min_worm_len=int(args['min_worm_length'])


df = pd.read_csv(csv_path)

head_coords_x=df['head coords x'].values
head_coords_y=df['head coords x'].values
tail_coords_x=df['tail coords x'].values
tail_coords_y=df['tail coords y'].values


# #create csv objects
output_path=os.path.join('/groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/skeleton_after_head_and_tail_from_unet_test/',re.split('-channel',re.split('/',input_filename)[-1])[0])

print('\noutput:')
print(output_path)

csvfilePathX=open(output_path+'_skeleton_X_coords.csv','w', newline='')
csv_writerPathX=csv.writer(csvfilePathX)

csvfilePathY=open(output_path+'_skeleton_Y_coords.csv','w', newline='')
csv_writerPathY=csv.writer(csvfilePathY)

csvfileX=open(output_path+'_spline_X_coords.csv','w', newline='')
csv_writerX=csv.writer(csvfileX)

csvfileY=open(output_path+'_spline_Y_coords.csv','w', newline='')
csv_writerY=csv.writer(csvfileY)

csvfileK=open(output_path+'_spline_K.csv','w', newline='')
csv_writerK=csv.writer(csvfileK)




with tiff.TiffFile(input_filename, multifile=False) as tif:
    for i, page in enumerate(tif.pages):
        img=page.asarray()
        
        start_point=(head_coords_x[i], head_coords_y[i])
        end_point=(tail_coords_x[i], tail_coords_y[i])

        #make_skeleton function
        u, skel_coord, spline_coord, K=make_skeleton(start_point, end_point, num_splines, img, min_worm_len)

        
        #csv writer
        csv_writerPathX.writerow(skel_coord[0])
        csv_writerPathY.writerow(skel_coord[1])
        csv_writerX.writerow(spline_coord[0])
        csv_writerY.writerow(spline_coord[1])
        csv_writerK.writerow(K)
csvfilePathX.close()
csvfilePathY.close()
csvfileX.close()
csvfileY.close()
csvfileK.close()
print('end')