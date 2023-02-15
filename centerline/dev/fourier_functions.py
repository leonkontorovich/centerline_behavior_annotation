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


def fourier_transform_for_kymo_plot(df, sampling_frequency):
    """
    This function plots fourier transform per segment
    :param df:
    :param fps:
    :return:
    """
    N = df.shape[0]
    # sample spacing
    T = 1.0 / sampling_frequency

    # y is your data
    y = df.values
    yf = scipy.fftpack.fft(y, axis=0)  # not sure which axis should be used. For Hilbert Transform I use 0.
    # It gives the real and the imaginary values, so we use the (abs) to get the real ones
    y_axis = 2.0 / N * np.abs(yf[:N // 2])

    xf = np.linspace(0.0, 1.0 // (2.0 * T), N // 2)

    # This is what actually displays the FT
    fig, axes = plt.subplots(nrows=3, figsize=(4, 2), dpi=150)
    axes[0].plot(y)
    axes[0].set_ylabel('Amplitude')
    axes[0].set_xlabel('Time (#samples)')

    axes[1].plot(xf, y_axis)
    axes[1].set_ylabel('Amplitude')
    axes[1].set_xlabel('Frequency (Hz)')

    axes[2].plot((1 / xf), y_axis)
    axes[2].set_ylabel('Amplitude')
    axes[2].set_xlabel('Period (s) (Not frames!)')
    return fig, axes


def fourier_transform_for_kymo(df, sampling_frequency):
    """

    :param df:
    :param fps:
    :return:
    """
    N = df.shape[0]
    # sample spacing
    T = 1.0 / sampling_frequency

    # y is your data
    y = df.values
    yf = scipy.fftpack.fft(y, axis=0)  # not sure which axis should be used. For Hilbert Transform I use 0.
    # It gives the real and the imaginary values, so we use the (abs) to get the real ones
    y_axis = 2.0 / N * np.abs(yf[:N // 2])

    xf = np.linspace(0.0, 1.0 // (2.0 * T), N // 2)

    return y_axis, xf

def plot_fft(y_axis, xf, axes):


    axes.imshow(y_axis.T, origin="upper", interpolation=None, cmap='viridis',
                extent=[xf[0], xf[-1], y_axis.shape[1], 0],
                aspect=0.02, vmin=0, vmax=0.005) #vmax corresponds to amplitude
    #axes.set_xlim([0, 1])
    axes.set_xlabel('Frequency (Hz)')
    axes.set_ylabel('Body Segment')
    axes.set_title('Fourier Transsform')

    return axes

if __name__ == '__main__':

    import argparse
    import os

    # This script should save receive the kymogram (without Nans) and the sampling frequency as input,
    # and return the y_axis and the xf in a csv file

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--project_path', help='path to project', required=True)
    parser.add_argument('-kp', '--kymo_path', help='filepath to kymogram', required=True)
    parser.add_argument('-fps', '--sampling_frequency', type=float, help='sampling frequency', required=True)
    args = vars(parser.parse_args())
    project_path = args['project_path']
    kymo_path = args['kymo_path']
    sampling_frequency = args['fps']


    df = pd.read_csv(kymo_path) #should load the averaged kymo already
    #df = df.rolling(window=83, center=True, min_periods=1).mean()

    y_axis, xf = fourier_transform_for_kymo(df, sampling_frequency)
    pd.DataFrame(y_axis).to_csv(os.path.join(project_path, "fft_y_axis.csv"))
    pd.DataFrame(xf).to_csv(os.path.join(project_path, "fft_xf.csv"))

    # plotting
    # fig, axes = plt.subplots()
    # axes = plot_fft(y_axis, xf, axes)
    # axes.set_xlim([0, 1])
    # plt.show()
