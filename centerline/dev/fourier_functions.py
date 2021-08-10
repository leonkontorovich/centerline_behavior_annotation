import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.fftpack
import scipy.fft
#modification of ulises fourier function
##made it more modular and added option to average over segments
def fourier_transform(K,fps,segment):
    """
    returns a fourier transform of kurvature of different body segments
    Parameters:
    -------------------
    K: numpy array of curvature data
    segment: body segments to fourier transform
    fps=frames per second
    """
    N=K.shape[1]
    #sample spacing
    T=1.0/fps
    #x=np.linspace(0.0, N*T, N)
    xf=np.linspace(0.0, 1.0//(2.0*T), N//2)
    y=segment
    yf=scipy.fftpack.fft(y)
    #define axes
    #y_axis (see that it should start at 1 in yf[1:N//2])
    y_axis=2.0/N * np.abs(yf[1:N//2])
    #x_axis
    x_axis=xf[1:N//2]
    return x_axis, y_axis
            
            

def segment_averaging(K,win):
    """"
    returns the mean curvature over a defined number of segments.
    Parameters:
    -----------------
    Ks: array of curavture over multiple segments
    win: integer, number of segments to be averaged over
    """
    K = pd.DataFrame(K)
    K=K.T
    Kt_avg=K.groupby(np.arange(len(K))//win).mean()
    print('number of rows and columns:'+str(Kt_avg.shape))
    Kt_avg=Kt_avg.T
    Kt_avg=Kt_avg.to_numpy()
    return Kt_avg


def section_to_fourier_transform(K,start_frame,end_frame,fps):
    """
    defines part of the track to fourier transform
    Parameters:
    -----------------
    K: numpy array of curvature data
    start and end frame: section to transform
    fps:frames per second
    """
    K=K[start_frame:end_frame]
    print(('lenght of recording:'+str((end_frame-start_frame)/fps)+" secs"))
    print('new shape:'+str(K.shape))
    return K


def fourier_plot(x_axis,y_axis,start_frame,end_frame,start_freq,end_freq,win,fps,segment,idx,save):
    """
    plots the output of fourier_transform
    Parameters:
    -----------------
    x_ft: x axis of fourier transform
    y_ft: y axis of fourier transform
    start_frame
    end_frame
    start_freq, end_freq, frequncy range to be displayed
    win: window over which the segments where averaged
    fps:frames per second
    save: 1 for saving
    """
    plt.rcParams.update({'figure.max_open_warning': 0})
    plt.rcParams.update({'font.size': 16})
    y=segment
    x=np.arange(0, y[start_frame:end_frame].shape[0]/fps,1/fps)
    y=y[start_frame:end_frame]
    
    #plotting:
    #oscilations
    plt.figure(figsize=(20,3))
    plt.subplot(1,2,1)
    plt.plot(x,y)
    plt.title('Segment '+str((idx*win))+'-'+str(idx*win+win))
    if idx==0: plt.title('Segment '+str(idx)+'-'+str(win))
    plt.xlabel('Time (s)')
    plt.ylabel('Signal Amplitude (a.u)')
    
    #Frequency
    plt.subplot(1,2,2)
    plt.plot(x_axis,y_axis)
    plt.xticks(np.arange(start_freq, end_freq, step=1))
    plt.xlim(start_freq,end_freq)
    plt.title('Segment '+str((idx*win))+'-'+str(idx*win+win))
    if idx==0: plt.title('Segment '+str(idx)+'-'+str(win))
    plt.ylabel('Signal Amplitude (a.u)')
    plt.xlabel('Frequency (Hz)')
    if save!=0:    
        plt.savefig(str(idx)+'.png')
    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.5, hspace=0.3)
