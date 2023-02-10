import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.fftpack
import scipy.fft


def fourier_transform(segment, fps):
    """
    returns a fourier transform of curvature of different body segments
    Parameters:
    -------------------
    segment:numpy array, body segments to fourier transform
    fps:int,frames per second
    """
    N = segment.shape[0]
    # sample spacing
    T = 1.0 / fps
    # x=np.linspace(0.0, N*T, N)
    xf = np.linspace(0.0, 1.0 // (2.0 * T), N // 2)
    y = segment
    yf = scipy.fftpack.fft(y)
    # define axes
    # y_axis (see that it should start at 1 in yf[1:N//2])
    y_axis = 2.0 / N * np.abs(yf[1:N // 2])
    # x_axis
    x_axis = xf[1:N // 2]

    return x_axis, y_axis

def fourier_transform_for_kymo(df, fps):
    """

    :param df:
    :param fps:
    :return:
    """
    N = df.shape[0]
    # sample spacing
    T = 1.0 / fps
    x = np.linspace(0.0, N * T, N)

    # y is your data
    y = df.values
    yf = scipy.fftpack.fft(y, axis=-1)
    # It gives the real and the imaginary values, so we use the (abs) to get the real ones
    xf = np.linspace(0.0, 1.0 // (2.0 * T), N // 2)
    y_axis = 2.0 / N * np.abs(yf[:N // 2])

    # This is what actually displayes the FT
    fig, ax = plt.subplots(figsize=(7, 2), dpi=150)
    # ax.plot(xf, 2.0 / N * np.abs(yf[:N // 2]))
    print(y_axis)
    ax.plot(y_axis)

    return fig, ax


def fourier_plot(x_axis, y_axis, start_freq, end_freq, fps, segment, fourier=0):
    """
    returns figures of curvature and fourier transform(optional)
    Parameters:
    -----------------
    x_ft: x axis of fourier transform
    y_ft: y axis of fourier transform
    
    start_freq, end_freq: frequency range to be displayed i the fourier transform 
    """

    plt.rcParams.update({'figure.max_open_warning': 0})
    plt.rcParams.update({'font.size': 16})

    y = segment

    x = np.arange(0, y.shape[0] / fps, 1 / fps)

    if fourier == 0:
        fig, ax = plt.subplots(figsize=(20, 3), dpi=600, ncols=1, nrows=1)

        # oscilations
        ax.plot(x, y)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Signal Amplitude (a.u)')

    if fourier == 1:
        fig, ax = plt.subplots(figsize=(20, 3), dpi=600, ncols=2, nrows=1)
        # oscilations
        ax[0].plot(x, y)
        ax[0].set_xlabel('Time (s)')
        ax[0].set_ylabel('Signal Amplitude (a.u)')

        # fourier transform
        ax[1].plot(x_axis, y_axis)
        ax[1].set_xlim(start_freq, end_freq)
        ax[1].set_ylabel('Signal Amplitude (a.u)')
        ax[1].set_xlabel('Frequency (Hz)')
        plt.xticks(np.arange(start_freq, end_freq, step=1))

    plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=0.5, hspace=0.3)

    return ax


def segment_averaging(K, win):
    """"
    returns the mean curvature over a defined number of segments.
    Parameters:
    -----------------
    K: array of curavture over multiple segments
    win: integer, number of segments to be averaged over
    """
    K = pd.DataFrame(K)
    K = K.T
    Kt_avg = K.groupby(np.arange(len(K)) // win).mean()
    print('number of rows and columns:' + str(Kt_avg.shape))
    Kt_avg = Kt_avg.T
    Kt_avg = Kt_avg.to_numpy()

    return Kt_avg


if __name__ == '__main__':

    print("Use the notebook to learn how to do it")

    fps=1
    kymo_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BHbigtiff_skeleton_spline_K_signed.csv"
    df = pd.read_csv(kymo_path)
    df.rolling(window=83, center=True, min_periods=1).mean()
    print(df)
    # segment = df.iloc[21000:28000, 30]
    # print(segment)
    # x_axis, y_axis = fourier_transform(segment, fps)
    #
    # plt.plot(x_axis, y_axis)
    # plt.show()

    df = df.iloc[21000:28000, 30]
    fig , ax = fourier_transform_for_kymo(df, fps)
    ax.plot()
    plt.show()
