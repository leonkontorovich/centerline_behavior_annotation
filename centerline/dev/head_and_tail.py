import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import tifffile as tiff

from skimage.morphology import skeletonize

import cv2

import itertools

from skan import skeleton_to_csgraph

def load_bodypart_coords_from_DLC(dlc_df, bodypart):
    """
    Returns the coordinates of the specified bodypart in an array format
    Parameters:
    -----------
    dlc_df, dataframe
    bodypart, str
    name of the bodypart (case sensitive!)
    Returns:
    -----------
    bodypart cooords, array
    
    """
    
    scorer=dlc_df.columns.get_level_values(0)[0]
    bodypart_coords = (dlc_df[scorer][bodypart]['x'].values, dlc_df[scorer][bodypart]['y'].values)
    
    return bodypart_coords


def calculate_distances(head_coords, tail_coords,candidate_coords):
    """
    Parameters:
    -----------
    Returns:
    -----------
    dataframe with the distances
    """
    #create a dataframe which will contain all the info for every frame
    df=pd.DataFrame()
    
    #loop through every ending/edge
    for i, (x,y) in enumerate(candidate_coords):

        df.loc[i, 'edge_x_coords']=x
        df.loc[i, 'edge_y_coords']=y
        #store head and tail position
        df.loc[i, 'head_x']=head_coords[0]
        df.loc[i, 'head_y']=head_coords[1]


        df.loc[i, 'tail_x']=tail_coords[0]
        df.loc[i, 'tail_y']=tail_coords[1]

        #calculate the distance from that ending to the body part
        df.loc[i, 'dist_edge_to_head'] = math.hypot(x - head_coords[0], y - head_coords[1])
        df.loc[i, 'dist_edge_to_tail'] = math.hypot(x - tail_coords[0], y - tail_coords[1])
    return df

def cartesian_product_sum(list1, list2):
    """
    Parameters:
    -----------
    list1, list of values
    list2, second list of values
    Returns:
    -----------
    df, pandas dataframe
    dataframe with the combinations of the values on list1 and list2, and the sum of the combinations
    """
    df=pd.DataFrame()
    somelists = [list1,
        list2]

    #with itertools we calculate the product of all the distance combinations (aka cartesian product)
    #and save them in the dataframe
    for i, (value1,value2) in enumerate(itertools.product(*somelists)):
        #print(i,dist1,dist2)
        df.loc[i,'value1']=value1
        df.loc[i,'value2']=value2
    
    #sum the two distances
    df['value_sum']=df['value1']+df['value2']
    
    return df

def get_skeleton_points(skel, number_of_neighbors):
    """
    Returns coordinates of points in the skeleton that have the specified number of neighbors.
    endpoints have 1 neighbor, junctions 2, branches have 3 or more, etc.
    Parameters:
    -----------
    skel, np.array
    skeleton obtain from skeletonize from scikit image
    neighbors, int
    number of neighbors that the points should have
    Returns:
    -----------
    edge_coordiantes, list
    list of tuples with the coordinates of the edges
    """

    #obtain the degrees of each skeleton coordinate
    pixel_graph, coordinates, degrees = skeleton_to_csgraph(skel)
    
    skel_points_coords=list(zip(*np.where(degrees==number_of_neighbors)))

    return skel_points_coords


def assign_head_and_tail_to_coords(head_coords, tail_coords, candidate_coords):
    """
    Returns the head and tail coordinates from 
    Parameters:
    -----------
    list of head and tail from DeepLabCut prediction coordinates
    list of (edge) candidate coordinates
    
    Returns:
    -----------
    skel head coordinates,
    skel tail coordinates
    """
    #run calculate_distances function
    df=calculate_distances(head_coords, tail_coords,candidate_coords)
    
    #calculate the combinations of distances
    cp_df=cartesian_product_sum(df.loc[:,'dist_edge_to_head'],df.loc[:,'dist_edge_to_tail'])
    
    #exclude overlapping distances by writing nan on the impossible combinations
    number_of_edges=len(candidate_coords)
    values_to_exclude=np.arange(0, len(cp_df), number_of_edges+1)
    cp_df.loc[values_to_exclude,'value_sum']=np.nan
    
    #find the row where the distance sum is the minimum
    cp_df[cp_df['value_sum']==cp_df['value_sum'].min()]

    #Head Part
    #optimal distance 1
    optimal_distance_1=cp_df['value1'][cp_df['value_sum']==cp_df['value_sum'].min()]
   
    #find the edge coords that have dist_edge_to_head the dist1_good
    head_row=df[df['dist_edge_to_head']==optimal_distance_1.values[0]]
    skel_head_coords=(int(head_row['edge_x_coords'].values),int(head_row['edge_y_coords'].values))
    
    #optimal distance 2
    optimal_distance_2=cp_df['value2'][cp_df['value_sum']==cp_df['value_sum'].min()]
    
    #find the edge coords that have dist_edge_to_head the dist1_good
    tail_row=df[df['dist_edge_to_tail']==optimal_distance_2.values[0]]
    skel_tail_coords=(int(tail_row['edge_x_coords'].values),int(tail_row['edge_y_coords'].values))
    
    return skel_head_coords, skel_tail_coords