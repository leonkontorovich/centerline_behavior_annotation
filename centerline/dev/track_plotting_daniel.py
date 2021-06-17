
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

#plots all tracks for center head and tail
def plot_tracks_center_head_tail(filename,figsize_x,figsize_y,line_width):
    concentration_change=pd.read_csv(filename)
    x_head_corrected=concentration_change['x_head_corrected']
    y_head_corrected=concentration_change['y_head_corrected']
    x_tail_corrected=concentration_change['x_tail_corrected']
    y_tail_corrected=concentration_change['y_tail_corrected']
    x_center_pos=concentration_change['x_center']
    y_center_pos=concentration_change['y_center']
    fig3, ax3 = plt.subplots(1,1, figsize = (figsize_x,figsize_y), dpi=600)
    ax3.plot(x_head_corrected,y_head_corrected,label="head",linewidth=line_width)
    ax3.plot(x_tail_corrected,y_tail_corrected,label="tail",linewidth=line_width)
    ax3.plot(x_center_pos,y_center_pos,label="center",linewidth=line_width)
    ax3.axvline(x=0, ymin=0, ymax=1, lw=10, alpha=.5, color='y')
    ax3.plot(concentration_change['x_center'][0],concentration_change['y_center'][0], 'go', markersize=5)
    ax3.plot(concentration_change['x_center'].tail(1),concentration_change['y_center'].tail(1), 'ro', markersize=5)
    ax3.legend()
    return ax3



#determines the range of frames in which a specific part of the track occures
def position_to_time(concentration_change,begin_x,end_x,begin_y,end_y):
    """
    determines the range of frames in which a specific part of the track occures
    Parameters
    -------------
    concentration_change: dataframe with coordinate and concentration
    begin_x,end_x,begin_y,end_y : float,integer coordinates to determine begin and end of the track section.
    
    """

    position=concentration_change[(concentration_change['x_head_corrected'].between(begin_x,end_x))
    & (concentration_change['y_head_corrected'].between(begin_y, end_y))]
    return(position)


def plot_track_section(concentration_change,position):
    
    """
    plots specific part of the track
    Parameters:
    ---------------
    concentration_change: dataframe with coordinate and concentration
    position: output from position_to_time function. specific part of the track
    
    """
    figsize_x=10
    figsize_y=10
    line_width=0.2
    fontsize=5

    #plot track
    head_pos_x=concentration_change['x_head_corrected']
    tail_pos_x=concentration_change['x_tail_corrected']
    center_pos_x=concentration_change['x_center']

    head_pos_y=concentration_change['y_head_corrected']
    tail_pos_y=concentration_change['y_tail_corrected']
    center_pos_y=concentration_change['y_center']
    print('lenght of section: '+str(position['seconds'].max()-position['seconds'].min())+' secs')
    fig, ax = plt.subplots(figsize = (figsize_x,figsize_y), dpi=600,ncols=1,nrows=2)
    for axis in ax:
        axis.set_ylabel('Y (mm)')
        axis.set_xlabel('X (mm)')
        axis.set_yticks(np.arange(round(min(head_pos_y)), max(head_pos_y), 0.5))
        axis.tick_params(axis="y", labelsize=fontsize)
        axis.set_xticks(np.arange(round(min(tail_pos_x)), max(tail_pos_x), 0.5))
        axis.tick_params(axis="x", labelsize=fontsize)
    ax[0].plot(head_pos_x,head_pos_y,linewidth=line_width)
    ax[0].plot(tail_pos_x,tail_pos_y,linewidth=line_width)
    ax[0].plot(center_pos_x,center_pos_y,linewidth=line_width)
    ax[0].axvline(x=0, ymin=0, ymax=1, lw=10, alpha=.5, color='y')
    rect = patches.Rectangle((position['x_head_corrected'].min(), position['y_head_corrected'].min()),
    abs(position['x_head_corrected'].min()-position['x_head_corrected'].max()), abs(position['y_head_corrected'].min()-position['y_head_corrected'].max()), linewidth=1, edgecolor='k', facecolor='none')
    ax[0].add_patch(rect)
    #determining part for zoom
    ax[1].plot(head_pos_x,head_pos_y,linewidth=line_width)
    ax[1].plot(tail_pos_x,tail_pos_y,linewidth=line_width)
    ax[1].plot(center_pos_x,center_pos_y,linewidth=line_width)
    ax[1].set_xlim(position['x_head_corrected'].min(),position['x_head_corrected'].max())
    ax[1].set_ylim(position['y_head_corrected'].min(),position['y_head_corrected'].max())
    plt.axvline(x=0, ymin=0, ymax=1, lw=10, alpha=.5, color='y')
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.5, hspace=0.3)

    
    
    
    
    
def plot_concentration_section(concentration_change,position):
    
    """"
    plots concentration of speciific part of the track
    Parameters:
    --------------------
    concentration_change: dataframe with coordinate and concentration
    position: output from position_to_time function. specific part of the track
    """
    
    line_width=0.5
    figsize_x=10
    figsize_y=10
    line_width=0.2
    fontsize=5

    x=concentration_change['seconds']
    head_conc=concentration_change['concentration_head']
    tail_conc=concentration_change['concentration_tail']
    center_conc=concentration_change['concentration_center']
    fig, ax = plt.subplots(figsize = (figsize_x,figsize_y), dpi=600,ncols=1,nrows=2)
    for axis in ax:
        axis.set_ylabel('Concentration')
        axis.set_xlabel('time (seconds)')
        axis.tick_params(axis="y", labelsize=fontsize)
        axis.tick_params(axis="x", labelsize=fontsize)
        
    ax[0].plot(x,head_conc,label="head",linewidth=line_width)
    ax[0].plot(x,tail_conc,label="tail",linewidth=line_width)
    ax[0].plot(x,center_conc,label="center",linewidth=line_width)
    rect = patches.Rectangle((position['seconds'].min(), position['concentration_head'].iloc[0]),position['seconds'].max()-position['seconds'].min(),
    abs(position['concentration_head'].iloc[0]-position['concentration_head'].iloc[-1]), linewidth=1, edgecolor='k', facecolor='none')
    ax[0].add_patch(rect)
    ax[0].set_yticks(np.arange(0, 1.1, 0.1))
    ax[0].set_xticks(np.arange(round(min(x)), max(x), 50))
    ax[1].plot(x,head_conc,label="head",linewidth=line_width)
    ax[1].plot(x,tail_conc,label="tail",linewidth=line_width)
    ax[1].plot(x,center_conc,label="center",linewidth=line_width)
    ax[1].set_ylim(position['concentration_head'].iloc[0],position['concentration_head'].iloc[-1])
    ax[1].set_xlim(position['seconds'].min(),position['seconds'].max())
    
    
       
def curv_section(K,fps,start_frame,end_frame):
    Ks=K[start_frame:end_frame]
    print(('lenght of recording:'+str((end_frame-start_frame)/fps)+" secs")) #defines the part of the track i want to fourier transform
    print('rows and columns: '+str(Ks.shape))
    return(Ks.copy())


def segment_averaging(Ks,win):
    """"
    returns the mean curvature over a defined number of segments.
    Parameters:
    -----------------
    Ks: array of curavture over multiple segments
    win: integer, number of segments to be averaged over
    """
    K_avg = pd.DataFrame(Ks) #convert to df to perform the groupy function
    Kt_avg=K_avg.T
    Kt_avg=Kt_avg.groupby(Kt_avg.index // win).mean() #takes the average of 5 segments resulting in 20 rows
    print('number of rows and columns:'+str(Kt_avg.shape))
    Kt_avg=Kt_avg.to_numpy()
    return (Kt_avg)