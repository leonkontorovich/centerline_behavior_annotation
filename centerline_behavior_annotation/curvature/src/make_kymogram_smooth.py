import matplotlib.cm as cm
import matplotlib as mpl
mpl.use('Agg') # this turns of X server to run on the cluster which has not display
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import colors
import pandas as pd
import numpy as np
import os
import argparse
import sys


def plot_main_figure(nrows, ncols):
    """Function to plot the main behavioural features of a single worm behavioral recording
    input:
    project_folder
    """

    fig = plt.figure(constrained_layout=True)
    gs = GridSpec(nrows, ncols, figure=fig)

    #kymogram
    # ax1 = fig.add_subplot(gs[0, :])
    #
    # ax2 = fig.add_subplot(gs[1, :5])


    return fig, gs

def plot_kymogram(kymo_path, axes):
    """
    Note: plot_kymogram.py exists in curvature package. At the moment it is not using this function. Maybe this fucntion should go there.
    :param project_path:
    :param fig:
    :param axes:
    :return:
    """

    try:
        df_kymo = pd.read_csv(kymo_path, header=None)
        num_frames = len(df_kymo)
        num_lines = 2
        cut_frames = num_frames // num_lines
        df_kymo = df_kymo.rolling(100, center=True, min_periods=10).mean()
        fig, axs = plt.subplots(num_lines, 1, dpi=400, figsize=(10, 1*num_lines))

        for i, ax in enumerate(axs):
            start_idx = i * cut_frames
            end_idx = start_idx + cut_frames
            ax.imshow(df_kymo.iloc[start_idx:end_idx].T, origin="upper", cmap='seismic', aspect=20, vmin=-0.06, vmax=0.06)
            ax.set_xticks(np.linspace(0, cut_frames, 5))
            ax.set_xticklabels(np.linspace(start_idx, end_idx, 5).astype(int))
            if i == num_lines - 1:
                ax.set_xlabel('Frame')            
            ax.set_ylabel('Body Part') 

        plt.tight_layout()
        plt.show()
        
    except:
        print('problem reading the kymograph csv file')

    return axes


def main(arg_list=None):
    # TODO: add beh annotation in speed plot
    # add head speed, total curvature, PC1, PC2, PC3, etc. See notebook wbfm_analysis
    # TODO: make it for every worm

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('--input_path', help='folder with the tracker position', required=True)
    parser.add_argument('--spline_K', help='Path to CSV with Behavior Annotations', required=True)
    parser.add_argument('--output_file', help='Output File Name', required=True)

    args = parser.parse_args(arg_list)

    main_folder = args.input_path
    kymo_path = args.spline_K
    output_file = args.output_file

    project_folder = main_folder
    print("project folder is: ", project_folder)

    # Start Figure
    fig, gs = plot_main_figure(nrows=7, ncols=10)

    # Set size
    fig.set_size_inches(11.69, 8.27)

    # Kymogram
    ax1 = fig.add_subplot(gs[0, :-2])
    print(kymo_path)
    plot_kymogram(kymo_path, axes=ax1)
    ax1.set_ylabel('Body Segment')
    ax1.set_xlabel('Frames')

    plt.savefig(output_file, dpi=500)
    # plt.show()

    print('end of script')


if __name__ == '__main__':
    main(sys.argv[1:])