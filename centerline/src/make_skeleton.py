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


def make_skeleton(start_point, end_point, num_splines, img, min_worm_len=0):
    """
    Make an skeleton from binary image and start and end point
    Parameters:
    -----------
    start_point: tuple with x,y coordinates
    end_point: tuple with x,y coordinates
    min_worm_len: minimum worm length in pixels, if the found centerline is below it will be nan (default is 0)
    num_splines: number of splines you want to fit
    img: binary img from where the skeleton will be calculated
    min_worm_len: int, minimun length the worm should have. Default 0.
    """

    #this defines the costs for the shortest path
    costs=cv2.distanceTransform(img, cv2.DIST_L2,3)
    cv2.normalize(costs, costs, 0, 255, cv2.NORM_MINMAX)
    costs=costs.max()-costs

    #to increase the value a lot of the pixels outside the worm contour (np.inf will not work! sometimes head and tail outside work contour)
    costs=np.where(costs>254.9, 255*100, costs)
    #actual skeleton based on route through array from skimage
    try:
        path, cost = skimage.graph.route_through_array(costs, start=start_point, end=end_point, fully_connected=False)
        x, y = np.asarray(list(zip(*path)), dtype=int)
        # pts=np.asarray(path, dtype=np.int)
        value_error = False

    except ValueError:
        print("ValueError detected")
        value_error = True

    #if coordinates from route_through_array are smaller than min_worm_len or num_splines, it is not a good centerline
    if len(x)<min_worm_len or len(x)<num_splines or value_error == True:
        #print('Knots are Nans in: '+str(i))
        K=np.full(num_splines, np.nan)
        x=np.full(num_splines, np.nan)
        y=np.full(num_splines, np.nan)
        x_new=np.full(num_splines, np.nan)
        y_new=np.full(num_splines, np.nan)
        u=np.nan
    #else, the path was good, fit a spline and find curvature
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

def make_skeleton_from_DLC(input_stack, h5_filename, num_splines, min_worm_len=0):
    """
    will incorporate the hdf5 file form the corresponding network to produce the skeleton when without, it fails
    Potentially it could use a list as input (wrong_centerlines list for example)
    """
    #creates numberic regular expression
    regex_num=re.compile(r'\d+')
    #read the hdf5
    df = pd.read_hdf(h5_filename)#it could be improved to only read the selected rows (as long as hdf5 is in table format): https://stackoverflow.com/questions/33451926/read-hdf5-file-to-pandas-dataframe-with-conditions
    scorer=df.columns.get_level_values(0)[0]


    with tiff.TiffFile(input_stack, multifile=True) as tif:
        files = tif.imagej_metadata['Info'].split('\n')
        for idx, page in enumerate(tif.pages):
            img=page.asarray()
            file=files[idx]
            print('This is the description:', file,'\n')
            #get the number from the description! (It should have!)
            i=int(regex_num.search(file).group(0))
            print(i)
            #load the X,Y coordinates of the hdf5 file for that timepoint (number)
            #probably x and y need to be swaped
            head_y = int(df.loc[i][scorer,'Head','x'])
            head_x = int(df.loc[i][scorer,'Head','y'])
            start=(head_y, head_x)

            tail_y = int(df.loc[i][scorer,'Tail','x'])
            tail_x = int(df.loc[i][scorer,'Tail','y'])
            end=(tail_y, tail_x)

            annotated_img=img.copy()

            cv2.circle(annotated_img,(head_y, head_x),10, (150,150,150), 2)
            cv2.circle(annotated_img,(tail_y, tail_x),10, (150,150,150), 2)
            plt.imshow(annotated_img)
            plt.show()

            print(start, end)

            #make_skeleton function itself
            u, (x,y), (x_new, y_new), K = make_skeleton(start, end, num_splines, img, min_worm_len)
    return u, (x,y), (x_new, y_new), K




def find_nan_centerlines(centerline_csv):
    """
    Should work on the make_skeleton output or on the image (make_skeleton input?)
    Should use the extract frames function

    Parameters
    -----------
    centerline: centerline csv file

    Returns:
    ----------
    wrong centerlines,
    correct_centerlines
    """
    # declare wrong_centerlines and correct_centerlines empty list

    wrong_centerlines=[]
    correct_centerlines=[]

    # open file in read mode
    with open(centerline_csv, 'r') as read_obj:
    # pass the file object to reader() to get the reader object
        csv_reader = csv.reader(read_obj)
        # Iterate over each row in the csv using reader object
        for idx, row in enumerate(csv_reader):
            # row variable is a list that represents a row in csv
            row_array=np.asarray(row, dtype=np.float64)
            if True in np.isnan(row_array):
                wrong_centerlines.append(idx)
            else: correct_centerlines.append(idx)


    return wrong_centerlines, correct_centerlines

#def draw_centerline(x_coords_csv, y_coords_csv):

def skelatonize_image_series(input_image,path_to_h5,anotation_names:list,output_filename,num_splines:int=100,outside_contour_cost_handicap:int = 2, save_skel_image:bool=False,print_log:bool=False):
    """
    Make an skeleton from binary image and start and end point
    The function receives image file, locations of head and tail,
    and returns a spline fit that include x and y positions and curvature data per spline
    as csv files

    Parameters:
    -----------
    input_image: str
        path to input array
    path_to_h5: pandas dataFrame
        h5 file with anotation of head and tail
    anotation_names:list
        names of anotation of head and then the tail.
    output_filename:str
        the full path of the output
    num_splines:int
        the number of spline parts for output
        default is 100.
    outside_contour_cost_handicap: int
        fold multiplication of the highest cost for the spline fit.
        This prevents from skelaton doing bad shortcuts not through contour
        default value is 2
    save_skel_image:bool
        should a skelaton image series be produced for quality control
        default is False

    """
    #define the output path
    recording_name = os.path.splitext(os.path.basename(input_image))[0]
    folder_path = os.path.dirname(input_image) ## directory of file

    if output_filename is None:
        if print_log == True: print("no output path defined, using default")
        input_folder_path = os.path.dirname(input_filename) ## directory of file
        output_path = input_folder_path + "/skelaton/"
        output_filename = output_path + os.path.splitext(os.path.basename(input_filename))[0] +"_skelaton.tiff"
    else:
        output_path = os.path.dirname(output_filename)+'/' ## directory of file


    #make sure the output folder path exists
    try:
        os.mkdir(output_path)
        if print_log == True: print("output  dir created: "+output_folder_path)
    except:
        if print_log == True: print('output dir exists')

    #load head and tail tracking data
    try:
        hd5_df=pd.read_hdf(path_to_h5)
    except:
        print("could not find h5 file in path: "+path_to_h5)
        return None

    DLC_run_name = hd5_df.columns[0][0]

    #get name of head and tail anotations
    head_anotation = anotation_names[0]
    tail_anotation = anotation_names[1]

    #prepare to save data
    csvfilePathX=open(output_path+recording_name+'_skeleton_X_coords.csv','w', newline='')
    csvfilePathY=open(output_path+recording_name+'_skeleton_Y_coords.csv','w', newline='')
    csvfileX=open(output_path+recording_name+'_spline_X_coords.csv','w', newline='')
    csvfileY=open(output_path+recording_name+'_spline_Y_coords.csv','w', newline='')
    csvfileK=open(output_path+recording_name+'_spline_K.csv','w', newline='')

    csv_writerPathX=csv.writer(csvfilePathX)
    csv_writerPathY=csv.writer(csvfilePathY)
    csv_writerX=csv.writer(csvfileX)
    csv_writerY=csv.writer(csvfileY)
    csv_writerK=csv.writer(csvfileK)

    #iterate over time and extract skelaton
    with tiff.TiffWriter(output_path + recording_name +'_skelaton.tif', bigtiff=False) as tif_writer:
        with tiff.TiffFile(input_image, multifile=True) as tif:
#             tif = tif.asarray()

            skelaton_result = np.zeros(tif.pages[0].shape)
#             print("tif shape",tif.shape)
            for timepoint, page in enumerate(tif.pages):
                frame=page.asarray()
#             for timepoint in np.arange(0,tif.shape[0]):
#                 print("timepoint",timepoint)
#                 frame=tif[timepoint,:,:]

                #get locations
                head_x=hd5_df.loc[timepoint,:][DLC_run_name][head_anotation]['x']
                head_y=hd5_df.loc[timepoint,:][DLC_run_name][head_anotation]['y']
                tail_x=hd5_df.loc[timepoint,:][DLC_run_name][tail_anotation]['x']
                tail_y=hd5_df.loc[timepoint,:][DLC_run_name][tail_anotation]['y']
                start_point =  (int(head_y), int(head_x))
                end_point = (int(tail_y), int(tail_x))

                #this defines the costs for the shortest path
                costs=cv2.distanceTransform(frame.astype('uint8'), cv2.DIST_L2,3) #important that img type would be uint8 for stability

                #normalize costs
                norm_costs = np.zeros(frame.shape)
                norm_costs = cv2.normalize(costs, norm_costs, 0, 255, cv2.NORM_MINMAX)

                #does an inversion, background now is 255, worm is below 255
                inv_costs=norm_costs.max()-norm_costs

                #to increase the value a lot of the pixels outside the worm contour
                #(np.inf will not work! sometimes head and tail outside work contour)
                final_costs=np.where(inv_costs==255, 255**2, inv_costs)

                #get centerline
                path, cent_cost=shortest_path2(start_point, end_point, frame, final_costs)

                #mark centerline
                x,y=np.asarray(list(zip(*path)), dtype=int)

                #make skelaton
                _, (x,y), (x_new, y_new), K = make_skeleton(start_point, end_point, num_splines, frame.astype('uint8'))

                #save data for this frame
                csv_writerPathX.writerow([x])
                csv_writerPathY.writerow([y])
                csv_writerX.writerow(x_new)
                csv_writerY.writerow(y_new)
                csv_writerK.writerow(K)

                #make an output result image
                if save_skel_image == True:
                    for x,y in path:
                        frame[x][y]=20
                    tif_writer.save(frame)


    csvfilePathX.close()
    csvfilePathY.close()
    csvfileX.close()
    csvfileY.close()
    csvfileK.close()

    if print_log == True: print("finished processing file: "+os.path.basename(input_image))
    return None

def batch_skeletonize_files(bin_file_list:list,h5_folder_path:str,sufix_len:int,DLC_run_name:str,spline_number:int,head_anotation:str='head',tail_anotation:str='tail',save_skel_image:bool=True,print_log:bool=False):
    """
    This function binarizes a batch of images.
    The recieves a list of image files to binarize, together with the path to the matching folder that holds the h5 files with the head and tail coordinates.
    In addition the spline number and names of anotation of head and tail are given.

    Parameters:
    ----------
    bin_file_list:list
    A list of paths to all the images to binarize
    h5_folder_path:str
    path to h5 folder holding the matching h5 files with head and tail coordinates
    sufix_len:int
    the length of suffix of image name used to find the matching h5 file
    DLC_run_name:str
    the name of the DLC model used to anotate head and tail
    spline_number:int
    number of splines to extract
    head_anotation:str='head'
    name of head anotation
    tail_anotation:str='tail'
    name of tail anotation
    save_skel_image:bool=True
    should a skeleton image be saved for proofing?
    print_log:bool=False
    should a log of success/fail be printed for debuging?
    """

    print("Starting to skelatonize binary images...")
    unsuccesful_files_list = []

    for i,bin_image in enumerate(tqdm(bin_file_list)):
        #get recording name
        recording_name = os.path.splitext(os.path.basename(bin_image))[0]
        #get h5_path
        h5_path = h5_folder_path+recording_name[:-sufix_len]+DLC_run_name+'.h5'
        #get root_folder_path
        root_folder_path = os.path.dirname(os.path.dirname(bin_image))
        #define output filename
        skeleton_file_path = root_folder_path+'/skeleton/'+recording_name+'_skeleton.tiff'

        try:
            skelatonize_image_series(bin_image,h5_path,[head_anotation,tail_anotation],skeleton_file_path,spline_number,2,save_skel_image,print_log=print_log)
        except:
            unsuccesful_files_list.append(bin_image)
            if print_log:print("faild to bin",bin_image)
            continue
    if len(unsuccesful_files_list)>0: print("in total ",len(unsuccesful_files_list),"files failed to be binned.")
    print("Finished skeletonization!!!")
    return None

# To import tqdm correctly
#TODO move to another module
def isnotebook():
    # from: https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except NameError:
        return False      # Probably standard python interpreter


def import_correct_tqdm():
    if isnotebook():
        from tqdm.notebook import tqdm
    else:
        from tqdm import tqdm
    return tqdm

#To correctly import tqdm
import_correct_tqdm()


#Itamar 0202021 added this function to fix shortest path error of having end/start point on the edge of the image
#It was called inside the make_skeleton() after calculating the costs.
#Since It is not known if it is really required it's now left commented.

# def corr_extreme_pos(pos,shape):
#     """
#     makes sure the x,y positions are not on the border of the image
#     parameters:
#     ----------
#     pos: tuple
#     array of y,x positions
#     shape: nd.array
#     array of y,x positions    
#     """
#     new_pos = list(pos)
#     if pos[0] >= shape[0]: new_pos[0] = shape[0]-1
#     if pos[1] >= shape[1]: new_pos[1] = shape[1]-1
#     return tuple(new_pos)
