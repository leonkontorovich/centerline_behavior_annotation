import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict




#function for sigmoid curve
def sigmoid_fit(x, L ,x0, k, b):
    """
    Parameters:
    ---------------------------
    x: data
    k:steepness
    b:shift along y axis
    L:upper limit
    x0:Inflection point
    """
    y = L / (1 + np.exp(-k*(x-x0)))+b
    return (y)

#function for quadratic curve
def quadratic_fit(x, a, b, c):
    """
    Parameters:
    ------------------------------
    x:data
    a:quadratic coificient (steepness)
    b: linear coificient (moves the parabola along a parabolic path, given by y=−ax2+c)
    c:move along y axis (y intercept)
    """
    return a*np.power(x,2)+b*x+c



#exp_fit_2
def exponential_fit(x, y0, plateau, K):
    """
    Equation after this:
    https://www.graphpad.com/guides/prism/latest/curve-fitting/reg_exponential_decay_1phase.htm
    y0:y value when X (time) is zero.
    plateau value at infinite x
    K: steepness (rate constant)
    """
    return (y0-plateau) * np.exp(-K*x) + plateau




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


def calculate_concentration_for_bodyparts(df,type_of_fit, *parameters_of_fit):
    """
    returns pandas dataframe containing concentration of position x of different bodyparts
    
    Parameters:
    ----------------------
    df: pandas dataframe containing x coordinates of differnt bodyparts
    type_of_fit: str,model to calculate the concentration (sigmoid,quadratic,exponential)
    parameters: of the model (determined with the curve fit script)
        
    #sigmoid (L,x0,k,b)
    based on function y = L / (1 + np.exp(-k*(x-x0)))+b
    L:upper limit
    x0:Inflection point
    k:steepness
    b:shift along y axis
    
    #quadratic (a,b,c)
    based on function: y=a*np.power(x,2)+b*x+c
    a:steepness
    b: moves the  parabola along a parabolic path, given by y=−ax2+c
    c:move along y axis

    #exponential (x0,plateau,K)
    based on function: y=(y0-plateau) * np.exp(-K*x) + plateau
    https://www.graphpad.com/guides/prism/latest/curve-fitting/reg_exponential_decay_1phase.htm
    y0:y value when X (time) is zero.
    plateau: value at infinite x
    K: steepness (rate constant)
    """
#grab values for which the concentration should be calculated (in the stripe assay this only depends on x position)
    bodypart_coordinates=df[df.columns[pd.Series(df.columns).str.contains('x_')]]
    
    

    #empty dataframe to collect the concentraiton for each bodypart as a column
    concentration_all_bodyparts=pd.DataFrame()

    number_of_bodyparts=len(bodypart_coordinates.columns)

    # loop calculates concentration for each bodypart and appends it to concentration_all_bodyparts
    for bodypart in range(number_of_bodyparts):
    
        #grab bodypart
        current_bodypart=bodypart_coordinates.iloc[:,bodypart]
        
        if type_of_fit=='exponential':
            #unpack parameters
            y0,plateau,K=parameters_of_fit
            #calculate concentration
            concentration_current_bodypart=exponential_fit(current_bodypart,y0,plateau,K)
        
        #apply specified fit
        if type_of_fit=='sigmoid':
            #unpack parameters
            L, x0, k, b=parameters_of_fit
        #calculate concentration
            concentration_current_bodypart=sigmoid_fit(current_bodypart, L, x0, k, b)
            
        if type_of_fit=='quadratic':
            #unpack parameters
            a,b,c=parameters_of_fit
            #calculate concentration
            concentration_current_bodypart=quadratic_fit(current_bodypart,a,b,c)
            
        
    
        #append to dataframe
        concentration_all_bodyparts=pd.concat([concentration_all_bodyparts, concentration_current_bodypart],axis=1)
    
        #rename column
        concentration_all_bodyparts.rename(columns = {current_bodypart.name: f'concentration_{current_bodypart.name}'},inplace=True)
    

    #append to original dataframe
    df=pd.concat([df,concentration_all_bodyparts],axis=1)
    
    return df





def adjust_for_food_position(df,x_ref,y_ref=0):
    """
    returns pandas df with coordinates adjusted for food position
    
    Parameters:
    ---------------------
    df:dataframe containing x and y coordinates
    x_ref: coordinates of the food patch (measured manually after recording)
    y_ref: optional, only needed if not a stripe assay
    """
    
    
    #index all x_coordinate columns and substract food position
    x_ref_substracted=df[df.columns[pd.Series(df.columns).str.contains('x_')]]-x_ref
    #replace old x_coordinates with the new ones
    df.update(x_ref_substracted)
    
    if y_ref!=0:
        #index all y_coordinate columns and substract food position
        y_ref_subtracted=df[df.columns[pd.Series(df.columns).str.contains('y_')]]-y_ref
        #replace old x_coordinates with the new ones
        df.update(y_ref_subtracted)
    return df