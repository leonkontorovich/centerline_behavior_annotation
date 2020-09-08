#read and write tiff video for binary

#import pckgs
#import pckgs
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

#import functions
def shortest_path2(start,end,binary,costs):
    path, cost = skimage.graph.route_through_array(costs, start=start, end=end, fully_connected=True)
    return path,cost


ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input_filename", required=True, help="path to input file")
ap.add_argument("-h5", "--h5", required=True, help="path to the DLC hdf5 file")

args = vars(ap.parse_args())

input_filename=args['input_filename']
print(input_filename)
print('\n')
h5_path=args['h5']
print(h5_path)
print('\n')

df = pd.read_hdf(h5_path)

scorer=df.columns.get_level_values(0)[0]
head_x=df[scorer]['Head']['x'].values
head_y=df[scorer]['Head']['y'].values
tail_x=df[scorer]['Tail']['x'].values
tail_y=df[scorer]['Tail']['y'].values


# #create csv objects
output_path=os.path.join('/groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/all_good_skeleton/',re.split('-channel',re.split('/',input_filename)[-1])[0])
print('\noutput:')
print(output_path)
print('\noutput2:')
print(output_path+'_spline_Y_coords.csv')
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

knots=100

with tiff.TiffFile(input_filename, multifile=False) as tif:
    for i, page in enumerate(tif.pages):
        img=page.asarray()
        #Skeleton approach
        #skeleton = skeletonize(img/255)
        #skeleton=np.asarray(skeleton, dtype="uint8")

        #Scikit graph approach - Shortest Path
        start_point =  (int(head_y[i]), int(head_x[i]))#(286, 124)#
        end_point = (int(tail_y[i]), int(tail_x[i]))#(332,480)#

        #Shortest Path default:
        #path, cost, costs=shortest_path(start_point, end_point, skeleton)

        #Shortest Path 2:
        #I modified the original shortest_path function, now costs are defined outside
        #it works on the img instead of the skeleton, which is then in fact not used

        #this defines the costs for the shortest path
        costs=cv2.distanceTransform(img, cv2.DIST_L2,3)
        cv2.normalize(costs, costs, 0, 255, cv2.NORM_MINMAX)
        costs=costs.max()-costs  
        costs=costs**2

        path, cost=shortest_path2(start_point, end_point, img, costs)

        x,y=np.asarray(list(zip(*path)), dtype=int)

#         for x,y in path:
#             img[x][y]=0

        pts=np.asarray(path, dtype=np.int)
        #fill K with NaNs if the skeleton is not good
        if len(pts)<knots:
            #print('Knots are Nans in: '+str(i))
            K=np.full(knots, np.nan)
            x=np.full(knots, np.nan)
            y=np.full(knots, np.nan)
            x_new=np.full(knots, np.nan)
            y_new=np.full(knots, np.nan)
        else:
            ####
            #s is the smoothing condition should have around the size of points/2 (keep it low)
            #k is the degree of freedom for the polynom it fits, 5 is good
            #splprep calculates automatically the number of knots. One can see how many in tck.shape[1].
            #everytime splprep is run the number by differ
            tck, u = splprep(pts.T, u=None, s=pts.shape[0]/2, per=0, k=5) 
            u_new = np.linspace(u.min(), u.max(), knots)#1000)

            x_new, y_new = splev(u_new, tck, der=0)

            #this returns x'(s), y'(s)
            x_der, y_der = splev(u_new, tck, der=1)
            #to have y'(x):
            der=y_der/x_der

            #this returns x''(s), y''(s)
            x_der2, y_der2 = splev(u_new, tck, der=2)
            #to have y''(x), also called K for Curvature:
            #we need the following equation:
            #ref in: https://en.wikipedia.org/wiki/Curvature#In_terms_of_a_general_parametrization (1st equation)
            K=(x_der*y_der2-y_der*x_der2)/np.sqrt(x_der**2+y_der**2)**3

        #csv writer
        csv_writerPathX.writerow(x)
        csv_writerPathY.writerow(y)
        csv_writerX.writerow(x_new)
        csv_writerY.writerow(y_new)
        csv_writerK.writerow(K)

        #if i==00:
        #    break
csvfilePathX.close()
csvfilePathY.close()
csvfileX.close()
csvfileY.close()
csvfileK.close()
print('end')