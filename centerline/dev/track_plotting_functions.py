import pandas as pd
from pathlib import Path
import numpy as np
import os
import matplotlib.pyplot as plt
import tifffile as tiff
from natsort import natsorted

#plot tracks without reference 
def plot_tracks(df):
    """
    Returns the axes of the figure given a dataframe with X and Y coordinates
    Parameters:
    --------------
    dataframe, pandas dataframe
        dataframe containing at least x and y coordinates

    Check whether dataframe has X Y written in capital in the filename!
    """
    
    #df=pd.read_csv(filename)
    # change column name x,y to X, Y (the old version had x and y instead of X and Y)
    df = df.rename(columns={"x":"X"})
    df = df.rename(columns={"y":"Y"})
    print(df.tail(1))
    ax=df.plot(x='X', y='Y', linewidth=2, figsize=(10,10))
    ax.plot(df['X'].head(1),df['Y'].head(1), 'go', markersize=5)
    ax.plot(df['X'].tail(1),df['Y'].tail(1), 'ro', markersize=5)
    ax.set_xlabel('mm')
    ax.set_ylabel('mm')
    ax.set_aspect('equal', 'box')
    ax.legend_.remove()
#     ax.set_xlim(-3,8)#(0, 45)
#     ax.set_ylim(-3,8)#(0, 45)
    return ax

    #plt.savefig('example_trace.pdf')
#this works, the problem for this is that I don't know how to zoom in


def plot_tracks_with_ref(df, x_ref):
    """
    Returns the axes of the figure given a dataframe with X and Y coordinates, and an X_ref
    Parameters:
    --------------
    dataframe, pandas dataframe
        dataframe containing at least x and y coordinates
    x_ref, int or float
        number on the X coordinate that will be substracted from the coordinates
    Check whether dataframe has X Y written in capital in the filename!
    Returns:
        -----------
        ax, axes of the figure
    """

    #df=pd.read_csv(filename)
    # change column name x,y to X, Y (the old version had x and y instead of X and Y)
    df = df.rename(columns={"x":"X"})
    df = df.rename(columns={"y":"Y"})
    #substract the x_ref
    df['X']=df['X']-x_ref
    #figure parameters
    font = {'size'   : 16}
    plt.rc('font', **font)
    plt.rcParams['axes.linewidth'] = 2
    ax=df.plot(x='X', y='Y', figsize=(10,8))
    ax.plot(df['X'].head(1),df['Y'].head(1), 'go', markersize=5)
    ax.plot(df['X'].tail(1),df['Y'].tail(1), 'ro')
    ax.set_xlabel('mm')
    ax.set_ylabel('mm')
    ax.legend_.remove()
    ax.set_xlim(-10, 40)
    ax.set_ylim(0, 40)
    ax.axvline(x=0, ymin=0, ymax=1, lw=10, alpha=.5, color='y')
    #plt.savefig('example_trace.pdf')
    #this works, the problem for this is that I don't know how to zoom in
    return ax

def calculate_speeds(positions_over_time):
    """
    Return a Speed dataframe from a Dataframe containing X and Y coordinates (only)
    source: https://codereview.stackexchange.com/questions/158688/calculating-speed-from-a-pandas-dataframe-with-time-x-and-y-columns
    """
    #Filter the dataframe so that it only has the input it needs
    positions_over_time=positions_over_time.filter(['X', 'Y', 'Time Elapsed'])
    time = 'Time Elapsed'

    movements_over_timesteps = (
        np.roll(positions_over_time, -1, axis=0)
        - positions_over_time)[:-1]

    speeds = np.sqrt(
        movements_over_timesteps.X ** 2 +
        movements_over_timesteps.Y ** 2
    ) / movements_over_timesteps[time]

    return pd.DataFrame({
        time: positions_over_time[time][:-1],
        'Speed': speeds,
    })


def plot_bodypart_coordinates(bodypart_coordinates,*bodyparts_to_plot,resolution=300,figsize_x=10,figsize_y=5,line_width=0.5):
    
    """
    returns figure of centroid coordinates and the coordinates of any number of bodyparts
    annotated with DeepLabCut
    
    Parameters:
    --------------------------
    bodypart_coordinates: pandas dataframe containing centroid coordinates from micromanager of coordinates of differnt bodyparts form DLC
    
    
    Optional Parameters:
    ------------------------------------
    bodyparts_to_plot: str, bodyparts to be displayed in the figure (eg. 'Head')
    resolution:int,optional, default:300
    figsize_x:int, optional, default:10
    figsize_y:int, optional, default:5
    line_width:int,float,optional, default:0.5
    """
    #draw figure
    fig, ax = plt.subplots(1,1, figsize = (figsize_x,figsize_y), dpi=resolution)
    
    #grab all bodypart coordinates
    bodypart_coordinates=bodypart_coordinates[bodypart_coordinates.columns[pd.Series(bodypart_coordinates.columns).str.contains('concentration')==False]]
    
    #if no bodyparts specified as arguments plot all
    if len(bodyparts_to_plot)==0:
       
        #empty list collecting bodyparts
        bodyparts_to_plot=[]
    
        #get column names
        all_bodyparts=list(bodypart_coordinates.columns)
    
        #put name of bodyparts in list
        for i in range(len(all_bodyparts)):
            before, sep, after = all_bodyparts[i].partition('x_') 
            bodyparts_to_plot.append(after)

        #remove empty strings
        while '' in bodyparts_to_plot: bodyparts_to_plot.remove('')
    
    
    #plot bodyparts in the list
    for i in range(len(bodyparts_to_plot)):
        current_bodypart=bodyparts_to_plot[i]
        current_bodypart_coordinates=bodypart_coordinates[bodypart_coordinates.columns[pd.Series(bodypart_coordinates.columns).str.contains(current_bodypart)]]
    
        # grab x coordinate from current bodypart
        x_coords_current_bodypart=current_bodypart_coordinates[current_bodypart_coordinates.columns[pd.Series(current_bodypart_coordinates.columns).str.contains('x')]]
   
        #grab y coordinates from current bodypart
        y_coords_current_bodypart=current_bodypart_coordinates[current_bodypart_coordinates.columns[pd.Series(current_bodypart_coordinates.columns).str.contains('y')]]
    
        #plot
        ax.plot(x_coords_current_bodypart,y_coords_current_bodypart,label=current_bodypart,linewidth=line_width)
    
    ax.legend()
    ax.set_aspect(0.8)
    
    #plot food lawn
    ax.axvline(x=0, ymin=0, ymax=1, lw=5, alpha=.5, color='y')

    return ax



def make_track_subsection(bodypart_coordinates,bodypart,x_section=(),y_section=()):
    """
    
    returns: dataframe with the range of frames in which a specific part of the track occurs
             index of the first frame
             index of the last frame
    
    Parameters
    -------------
    bodypart_coordinates: pandas dataframe containing centroid coordinates from micromanager of coordinates of differnt bodyparts form DLC
    bodypart:str,bodypart on whose coordinates the subsection will be based
    x_section:int,float, cut of value for x coordinates (lower limit,upperlimit)
    y_section:int,float, cut of value for y coordinates (lower limit,upperlimit)
    
    """
    

    #get all bodypart coordinates
    all_bodypart_coordinates=bodypart_coordinates[bodypart_coordinates.columns[pd.Series(bodypart_coordinates.columns).str.contains('concentration')==False]]
    
    #get coordinates specified in argument of the function
    specified_bodypart=bodypart_coordinates[all_bodypart_coordinates.columns[pd.Series(all_bodypart_coordinates.columns).str.contains(bodypart)]]
    
    #get x and y coordinates of specified bodypart
    x_coordinates_specified_bodypart=specified_bodypart[specified_bodypart.columns[pd.Series(specified_bodypart.columns).str.contains('x')]]
    y_coordinates_specified_bodypart=specified_bodypart[specified_bodypart.columns[pd.Series(specified_bodypart.columns).str.contains('y')]]
    
    #get column name of specified bodypart
    specified_bodypart_name_x=x_coordinates_specified_bodypart.columns[0]
    specified_bodypart_name_y=y_coordinates_specified_bodypart.columns[0]
    
    #unpack x and y limits
    begin_x,end_x=x_section
    begin_y,end_y=y_section
    
    #make the subsection
    subsection=bodypart_coordinates[(bodypart_coordinates[specified_bodypart_name_x].between(begin_x,end_x))
    & (bodypart_coordinates[specified_bodypart_name_y].between(begin_y, end_y))]
    
    #get first and last frame of the subsection
    first_frame=subsection.index.min()
    last_frame=subsection.index.max()
    
    
    return (subsection,first_frame,last_frame)



def plot_bodypart_concentration(bodypart_coordinates_concentration,*bodyparts_to_plot,resolution=300,figsize_x=10,figsize_y=5,line_width=1):
    
    """
    returns figure showing concentration of any number of bodyparts as a function of time
    
    Parameters:
    -----------------------
    bodypart_coordinates_concentration: pandas dataframe containing concentration of differnt bodyparts
    
    
    Optional Parameters:
    -------------------------------
    bodyparts_to_plot: str, bodyparts to be displayed in the figure (eg. 'Head')
    resolution:int,optional, default:300
    figsize_x:int, optional, default:10
    figsize_y:int, optional, default:5
    line_width:int,float,optional, default:0.5
    
    
    """


    #create figure
    fig, ax = plt.subplots(1,1, figsize = (figsize_x,figsize_y), dpi=resolution)

    #grab time passed for x axis
    time=bodypart_coordinates_concentration['seconds']

    #grab concentration of all bodyparts
    bodypart_concentration=bodypart_coordinates_concentration[(bodypart_coordinates_concentration.columns[pd.Series(bodypart_coordinates_concentration.columns).str.contains('concentration')])
        & (bodypart_coordinates_concentration.columns[pd.Series(bodypart_coordinates_concentration.columns).str.contains('change')==False])]

    
    
    #if no bodyparts specified as arguments plot all
    if len(bodyparts_to_plot)==0:
       
        #empty list collecting bodyparts
        bodyparts_to_plot=[]
    
        #get column names
        all_bodyparts=list(bodypart_concentration.columns)
    
        #put name of bodyparts in list
        for i in range(len(all_bodyparts)):
            before, sep, after = all_bodyparts[i].partition('x_') 
            bodyparts_to_plot.append(after)

        #remove empty strings and duplicates
        while '' in bodyparts_to_plot: bodyparts_to_plot.remove('') 
        
    
    
    
    #grab concentration of specific bodypart
    for i in range(len(bodyparts_to_plot)):
        current_bodypart=bodyparts_to_plot[i]
        current_bodypart_concentration=bodypart_concentration[bodypart_concentration.columns[pd.Series(bodypart_concentration.columns).str.contains(current_bodypart)]]
    
    
        #plot
        ax.plot(time,current_bodypart_concentration,label=current_bodypart,linewidth=line_width)
    
        ax.set_aspect(500)
        ax.legend()
        
    return ax