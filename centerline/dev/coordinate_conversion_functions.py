import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict


def get_absolute_bodypart_coordinates(center_coords,bodypart_coords,px_mm,y_width_frame,x_lenght_frame):
    """
    returns pandas dataframe containing:centroid coordinates and absolute x and y coordinates of any number of bodyparts
    annotated with DeepLabcut
    
    Parameters:
    --------------------------
    center_coords: pandas containing centroid coordinates from micromanager
    bodypart_coords: pandas containing Deeplabcut Annotations
    px_mm: ratio of lenght of the Agarplate in millimeter divided by lenght of the agarplat in pixel
    y_width_frame: width the behavioral recording
    x_lenght_frame: lenght of the behavioral recording
    """
    
    
    #rename and get the center coordinates for x and y
    center_coords=center_coords.rename(columns = {'x': 'x_center',
                'y': 'y_center'}, inplace = False)
    x_center=center_coords['x_center'] #absolute coordinates of center position x
    y_center=center_coords['y_center'] #absolute coordinates of center position y

    #set scorer
    scorer=bodypart_coords.columns.get_level_values(0)[0]
    bodypart_coords=bodypart_coords[scorer]
    
    #determine number of bodyparts
    all_body_parts=bodypart_coords.columns.get_level_values(0)[:]
    
    #to remove duplicates
    all_body_parts=list(OrderedDict.fromkeys(all_body_parts))
    number_of_bodyparts=len(list(OrderedDict.fromkeys(all_body_parts)))
    
    #create empty dataframe to store absolute coordinates of differnt bodyparts
    absolute_coordinates_all_bodyparts=pd.DataFrame()

    for bodypart in range(number_of_bodyparts):
        current_bodypart=all_body_parts[bodypart]
        #grab x and y coordinates of the current bodypart
        bodypart_x_coords=bodypart_coords[current_bodypart]['x']
        bodypart_y_coords=bodypart_coords[current_bodypart]['y']
        
        #apply the conversion function
        absolute_coordinates_current_body_part=relative2absolute_coordinates(x_center,y_center,bodypart_x_coords,bodypart_y_coords,px_mm,y_width_frame,x_lenght_frame)
    
        #renaming columns according to the bodypart
        absolute_coordinates_current_body_part.rename(columns = {'x': f'absolute_x_{current_bodypart}','y': f'absolute_y_{current_bodypart}'}, inplace = True)
        
        #append to dataframe
        absolute_coordinates_all_bodyparts=pd.concat([absolute_coordinates_all_bodyparts, absolute_coordinates_current_body_part],axis=1)
        
    #append center coordinates
    absolute_coordinates_all_bodyparts=pd.concat([absolute_coordinates_all_bodyparts, x_center,y_center],axis=1)
        
    return absolute_coordinates_all_bodyparts



##### calculating the distance of head or tail from the center of the frame
def relative2absolute_coordinates(center_x,center_y,data_x,data_y, px_mm, width,lenght):
    """
    convert head and tail position in the frame
    to absolute coordinates on the plate
    Parameters:
    -------------
    center_x,  absolute coordinates of the frame center x
    center_y, absolute coordinates of the frame center x
    data_x, pandas dataframe, head or tail position to convert x
    data_y, pandas dataframe, head or tail position to convert y
    px_mm, float,integer, value tells how much mm are 1 pixel
    width, float,integer, y size of the frame
    lenght, float, integer x size of the frame
    Returns:dataframe with corrected x and y values
    -------------
    """
    x_pos_mm=data_x*px_mm #converting x data in pixels
    y_pos_mm=data_y*px_mm #converting y data in pixels
    
    midpoint_lenght=lenght*px_mm/2 #determining center x in px
    midpoint_width=width*px_mm/2 # dermining center y in px
    
    distance_center_dlc_x=midpoint_lenght-x_pos_mm #distance between midpoint and dlc x axis
    distance_center_dlc_y=midpoint_width-y_pos_mm#distance between midpoint and dlc y axis
    
    absolute_x=center_x+distance_center_dlc_x
    absolute_y=center_y-distance_center_dlc_y
    
    return pd.DataFrame({'x': absolute_x,'y': absolute_y,})