import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
import tifffile as tiff
import csv

import argh

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
    Calculate the distances between head and tail coordinates and the candidate coords
    Parameters:
    -----------
    head_coords, tuple
    (x,y) coordinates of the head position
    tail_coords, tuple
    (x,y) coordinates of the tail position
    candidate_coords, list
    candidate coordinates from which the distance to head and tail will be calculated
    Returns:
    -----------
    dataframe with the distances
    """
    #create a dataframe which will contain all the info for every frame
    df=pd.DataFrame()
    
    #loop through every ending/edge
    for i, (x,y) in enumerate(candidate_coords):
        # store candidate coordinates as edge x and edge y
        # TODO: Candidate coordinates could not be 'edges' in the future, so change the label name in dataframe.
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
    Calculate the cartesian product of the numbers in the two lists.
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
    for i, (value1, value2) in enumerate(itertools.product(*somelists)):
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
    skel_points_coords, list
    list of tuples with the coordinates of the edges
    """

    #obtain the degrees of each skeleton coordinate
    pixel_graph, coordinates, degrees = skeleton_to_csgraph(skel)
    
    skel_points_coords=list(zip(*np.where(degrees==number_of_neighbors)))

    return skel_points_coords


def assign_head_and_tail_to_coords(head_coords, tail_coords, candidate_coords):
    """
    Returns the head and tail coordinates from a list of candidate coords based on the minimum sum of the cartesian product
    If no min is found, returns np.nan
    Parameters:
    -----------
    head_coords, tuple
    tail_coords, tuple
    list of tuples, (edge) candidate coordinates
    
    Returns:
    -----------
    skel_head_coordinates, tuple
    skel_tail_coordinates, tuple
    """
    #run calculate_distances function
    df=calculate_distances(head_coords, tail_coords,candidate_coords)
    
    #calculate the combinations of distances (cartesian product: cp)
    cp_df=cartesian_product_sum(df.loc[:,'dist_edge_to_head'],df.loc[:,'dist_edge_to_tail'])
    
    #exclude overlapping distances by writing nan on the impossible combinations
    number_of_edges=len(candidate_coords)
    values_to_exclude=np.arange(0, len(cp_df), number_of_edges+1)
    cp_df.loc[values_to_exclude,'value_sum']=np.nan
    
    #find the row where the distance sum is the minimum
    cp_df[cp_df['value_sum']==cp_df['value_sum'].min()]
    
    #print min sum value:
    #print(cp_df['value_sum'].min())
    
    try:

        #Head Part
        #optimal distance head
        optimal_distance_head=cp_df['value1'][cp_df['value_sum']==cp_df['value_sum'].min()]

        #find the edge coords that have dist_edge_to_head the dist1_good
        head_row=df[df['dist_edge_to_head']==optimal_distance_head.values[0]]
        skel_head_coords=(int(head_row['edge_x_coords'].values),int(head_row['edge_y_coords'].values))

        #optimal distance tail
        optimal_distance_tail=cp_df['value2'][cp_df['value_sum']==cp_df['value_sum'].min()]

        #find the edge coords that have dist_edge_to_head the dist1_good
        tail_row=df[df['dist_edge_to_tail']==optimal_distance_tail.values[0]]
        skel_tail_coords=(int(tail_row['edge_x_coords'].values),int(tail_row['edge_y_coords'].values))
    
    except:
        skel_head_coords=(np.nan, np.nan)
        skel_tail_coords=(np.nan, np.nan)
    return skel_head_coords, skel_tail_coords

def myfunc():
    """"
    Maybe there should be a function in between the assign_head_and_tail_to_coords() an the head_and_tail_wrapper()
    So that the wrapper is more like this
    with csv and tiff open:
        skel_head, skel_tail=myfunc(img, data_from_csv)
        ??
        But this is what assign_head_and_tail_to_coords() does...

    """


def head_and_tail_wrapper(hdf5_dlc_path, img_path, csv_output_filepath):
    """
    Wrapper of the head_and_tail functions
    This function writes the DLC coordinates if it can't find correct edges!
    Parameters:
    -----------
    hdf5_dlc_path, str
    img_path, str
    csv_output_filepath, str
    Returns:
    -----------
    Nothing, writes a csv file in csv_output_filepath
    """
    #DLC coords
    df=pd.read_hdf(hdf5_dlc_path)

    head_coords=load_bodypart_coords_from_DLC(df, 'Head')
    tail_coords=load_bodypart_coords_from_DLC(df, 'Tail')

    #image
    #tif=tiff.TiffFile(img_path)
    with tiff.TiffFile(img_path) as tif, open(csv_output_filepath, 'w', newline='') as csvfile:
    
        csv_writer_object = csv.writer(csvfile)
    
        csv_writer_object.writerow(('head coords x', 'head coords y','tail coords x', 'tail coords y'))

        #for loop for each row in the dataframe of DLC coordinates (should be the same as number of frames)
        for idx, row in df.iterrows():
            #print(idx)
    #         if idx%1000==0:
    #             print(idx)#continue
    #             elapsed = time.time() - t
    #             print(elapsed)
            #prepare image
            img=tif.pages[idx].asarray()

            skel=skeletonize(img/255)

            pixel_graph, coordinates, degrees = skeleton_to_csgraph(skel)
            #my function to get the edge_coords
            number_of_neighbours=1
            edge_coords=get_skeleton_points(skel, number_of_neighbours)

            if edge_coords: #if edge_coords is not empty
                #prepare head and tail coords
                #assign head and tail coordinates to tuples
                head_coords_i=(int(head_coords[1][idx]),int(head_coords[0][idx]))
                tail_coords_i=(int(tail_coords[1][idx]),int(tail_coords[0][idx]))

                skel_head, skel_tail=assign_head_and_tail_to_coords(head_coords_i, tail_coords_i, candidate_coords=edge_coords)

                if np.isnan(skel_head[0]):
                    skel_head, skel_tail=head_coords_i, tail_coords_i

            if not edge_coords:
                skel_head, skel_tail=head_coords_i, tail_coords_i

            csv_writer_object.writerow(skel_head+skel_tail)

        #csv_writer_path.close()


def head_and_tail_correction_from_img(img, number_of_neighbors, head_coords, tail_coords, fill_nan=True):

    """
    return head and tail skeleton coordinates from img, number of neighbors and head and tail coordinates predicted

    Parameters:
    -----------
    :param img:
    :param number_of_neighbors:
    :param head_coords:
    :param tail_coords:
    :param fill_nan:
    Return:
    ----------
    :return:

    """
    skel = skeletonize(img / 255)

    # my function to get the edge_coords
    edge_coords = get_skeleton_points(skel, number_of_neighbors)

    if edge_coords:  # if edge_coords is not empty
        skel_head, skel_tail = assign_head_and_tail_to_coords(head_coords, tail_coords, candidate_coords=edge_coords)

        if np.isnan(skel_head[0]):
            skel_head, skel_tail = head_coords_i, tail_coords_i

    if not edge_coords:
        skel_head, skel_tail = head_coords_i, tail_coords_i
    return skel_head, skel_tail
    
#assembling:

parser = argh.ArghParser()
parser.add_commands([head_and_tail_wrapper])

# dispatching:

if __name__ == '__main__':
    parser.dispatch()