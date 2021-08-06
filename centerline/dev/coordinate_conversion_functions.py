import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
##### calculating the distance of head or tail from the center of the frame
def corrected_absolute_coordinates(center_x,center_y,data_x,data_y, px_mm, width,lenght):
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
    return pd.DataFrame({'x_corrected': absolute_x,'y_corrected': absolute_y,})
    


##sigmoid function to determine the concentration in the data using the parameters 
#determined via fitting a curve to the gradient (got the function form the curve fitting script)
def sigmoid(x, L ,x0, k, b):
    """
    Parameters:
    ---------------------------
    x: data
    L: The Max value of the sigmoid fit
    x0: midpoint of the function
    k: slope
    b:intercept
    """
    y = L / (1 + np.exp(-k*(x-x0)))+b
    return (y)




 
