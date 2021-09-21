import numpy as np
# function to fit a linear curve
def linear_fit(x, a, b):
    """
    Parameters:
    ---------------------------
    x: data
    a: slope
    b:intercept
    """
    return a * (x + b)

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

#function for changing pixels to mm
def pixelmm(dist_mm, dist_px, data_px):
    """
    calculates how much pixels are within 1 mm and then mulitplies it with 
    the distance in pixels wihtin the data to convert it to distance in mm
    
    Parameters:
    -----------------------
    dist_mm: measured distance in mm
    dist_px: measured distance in px
    data_px: data
    ------------------------
    """
    
    return ((dist_mm / dist_px) * data_px)
    

#function for narmalizing data
def NormalizeData(data):
    """
    normalizes data from 0 to 1
    """
    return (data - np.min(data)) / (np.max(data) - np.min(data))

#function for smoothing the data
def smooth(data,avg_win):
    """
    Parameters:
    ----------------------------------------
    smooth the data by calculating sperate means of a defined range of data
    avg_win: range over which the mean is calculated
    """
    return (data.rolling(window=avg_win).mean())
