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