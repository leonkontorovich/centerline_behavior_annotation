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


def make_skeleton(start_point, end_point, num_splines, img):
	"""
    Make an skeleton from binary image and start and end point
    Parameters:
    -----------
	start_point: tuple with x,y coordinates
	end_point: tuple with x,y coordinates
	num_splines: number of splines you want to fit
	img: binary img from where the skeleton will be calculated
	"""

	#this defines the costs for the shortest path
	costs=cv2.distanceTransform(img, cv2.DIST_L2,3)
	cv2.normalize(costs, costs, 0, 255, cv2.NORM_MINMAX)
	costs=costs.max()-costs


	#to increase the value a lot of the pixels outside the worm contour (np.inf will not work! sometimes head and tail outside work contour)
	costs=np.where(costs>254.9, 255*100, costs)
	#actual skeleton based on shortest_path of skimage
	#actual skeleton based on route through array from skimage
	path, cost = skimage.graph.route_through_array(costs, start=start_point, end=end_point, fully_connected=False)



	x,y=np.asarray(list(zip(*path)), dtype=int)
	#pts=np.asarray(path, dtype=np.int)

	if len(pts)<num_splines:
		#print('Knots are Nans in: '+str(i))
		K=np.full(num_splines, np.nan)
		x=np.full(num_splines, np.nan)
		y=np.full(num_splines, np.nan)
		x_new=np.full(num_splines, np.nan)
		y_new=np.full(num_splines, np.nan)
		u=np.nan
	else:
		####
        ##SHOULD THIS PART HERE BE CONVERTED TO A FUNCTION?? (or some of it)
		#s is the smoothing condition should have around the size of points/2 (keep it low)
		#k is the degree of freedom for the polynom it fits, 5 is good
		#splprep calculates automatically the number of knots. One can see how many in tck.shape[1].
		#everytime splprep is run the number may differ
		tck, u = splprep([x,y], u=None, s=x.shape[0]/2, per=0, k=5) 
		u_new = np.linspace(u.min(), u.max(), num_splines)#1000)

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


	return u, (x,y), (x_new, y_new), K