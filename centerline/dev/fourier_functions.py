import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.fftpack
import scipy.fft
#modification of ulises fourier function
##made it more modular and added option to average over segments
def fourier_transform(Kts,fps,frequency_map,start_freq,end_freq):
    plt.rcParams.update({'figure.max_open_warning': 0})
    plt.rcParams.update({'font.size': 16})
    N=Kts.shape[1]
    #sample spacing
    T=1.0/fps
    #x=np.linspace(0.0, N*T, N)
    xf=np.linspace(0.0, 1.0//(2.0*T), N//2)


    for idx, segment in enumerate(Kts):
        #skip some segments
        #if idx%10!=5:continue
        #if idx >20:continue
    
        y=segment
        yf=scipy.fftpack.fft(y)
        #define axes
        #y_axis (see that it should start at 1 in yf[1:N//2])
        y_axis=2.0/N * np.abs(yf[1:N//2])
        #x_axis
        x_axis=xf[1:N//2]

        #define x and y
        x=np.arange(0, y[start_frame:end_frame].shape[0]/167,1/167)
        y=y[start_frame:end_frame]
    
        #plotting:
        plt.rcParams.update({'figure.max_open_warning': 0})
        plt.rcParams.update({'font.size': 16})
        #oscilations
        plt.figure(figsize=(20,3))
        plt.subplot(1,3,1)
        plt.plot(x,y)
        plt.title('Segment '+str((idx*win))+'-'+str(idx*win+win))
        if idx==0: plt.title('Segment '+str(idx)+'-'+str(win))
        plt.xlabel('Time (s)')
        plt.ylabel('Signal Amplitude (a.u)')
    
        #Frequency
        plt.subplot(1,3,2)
        plt.plot(x_axis, y_axis)
        plt.xticks(np.arange(start_freq, end_freq, step=1))
        plt.xlim(start_freq,end_freq)
        plt.title('Segment '+str((idx*win))+'-'+str(idx*win+win))
        if idx==0: plt.title('Segment '+str(idx)+'-'+str(win))
        plt.ylabel('Signal Amplitude (a.u)')
        plt.xlabel('Frequency (Hz)')
        
        #period
        if frequency_map==1:
            plt.subplot(1,3,3)
            plt.plot(1/x_axis, y_axis)
            plt.title('Signal Period at segment '+str((idx*win))+'-'+str(idx*win+win))
            if idx==0: plt.title('Signal Period at Segment '+str(idx)+'-'+str(win))
            plt.xlabel('Period (s)')
            plt.ylabel('Signal Amplitude (a.u)')
        else:
            #frequecy map
            plt.subplot(1,3,3)
            y_img=np.tile(y_axis, (500, 1))
            plt.imshow(y_img[1:100,0:100], extent=[0.5,xf[300],500,0], vmin=0, vmax=0.025, aspect=0.0015)
            #plt. yticks(y," ")
            plt.xlabel('Frequency (Hz)')
            plt.title('Segment '+str((idx*win))+'-'+str(idx*win+win))
            if idx==0: plt.title('Segment '+str(idx)+'-'+str(win))
            plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.25, hspace=0.25)