import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.fftpack
import scipy.fft


def fourier_transform(segment, sampling_frequency):
    """
    returns a fourier transform of curvature of different body segments
    Parameters:
    -------------------
    segment:numpy array, body segments to fourier transform
    fps:int,frames per second
    """
    N = segment.shape[0]
    # sample spacing
    T = 1.0 / sampling_frequency
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

def fourier_transform_for_kymo(df, sampling_frequency):
    """

    :param df:
    :param fps:
    :return:
    """
    N = df.shape[0]
    # sample spacing
    T = 1.0 / sampling_frequency
    # ??? x = np.linspace(0.0, N * T, N)

    # y is your data
    y = df.values
    yf = scipy.fftpack.fft(y, axis=-1)
    # It gives the real and the imaginary values, so we use the (abs) to get the real ones
    y_axis = 2.0 / N * np.abs(yf[:N // 2])

    xf = np.linspace(0.0, 1.0 // (2.0 * T), N // 2)

    # This is what actually displays the FT
    fig, axes = plt.subplots(nrows=3, figsize=(4, 2), dpi=150)
    axes[0].plot(y)
    axes[0].set_ylabel('Amplitude')
    axes[0].set_xlabel('Time (#samples)')

    #axes[1].plot(y_axis)
    axes[1].plot(xf, y_axis)
    axes[1].set_ylabel('Amplitude')
    axes[1].set_xlabel('Frequency (Hz)')

    #axes[1].plot(y_axis)
    axes[2].plot((1/xf), y_axis)
    axes[2].set_ylabel('Amplitude')
    axes[2].set_xlabel('Period (s) (Not frames!)')
    return fig, axes

if __name__ == '__main__':

    print("Use the notebook to learn how to do it")

    sampling_frequency=83
    kymo_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BHbigtiff_skeleton_spline_K_signed.csv"
    df = pd.read_csv(kymo_path)
    df = df.rolling(window=83, center=True, min_periods=1).mean()
    #print(df)
    # segment = df.iloc[21000:28000, 30]
    # print(segment)
    # x_axis, y_axis = fourier_transform(segment, fps)
    #
    # plt.plot(x_axis, y_axis)
    # plt.show()

    df = df.iloc[:, 50]
    fig, ax = fourier_transform_for_kymo(df, sampling_frequency)
    #ax.plot()
    plt.show()
