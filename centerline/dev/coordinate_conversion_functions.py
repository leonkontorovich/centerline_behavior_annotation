import numpy as np
##### calculating the distance of head or tail from the center of the frame
def corrected_absolute_coordinates(center,data, px_mm, frame):
    """
    convert head and tail position in the frame
    to absolute coordinates on the plate
    Parameters:
    -------------
    center,  absolute coordinates of the frame center
    data, pandas dataframe, head or tail position to convert
    px_mm, float,integer, value tells how much mm are 1 pixel
    frame, float,integer, x or y lenght of the frame
    Returns:
    -------------
    """
    return(center-(data*px_mm-frame*px_mm/2))


##sigmoid function to determine the concentration in the data using the parameters 
#determined via fitting a curve to the gradient
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