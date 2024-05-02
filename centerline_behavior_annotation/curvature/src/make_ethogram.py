import sys
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl
mpl.use('Agg') # this turns of X server to run on the cluster which has not display
from matplotlib.gridspec import GridSpec
import pandas as pd
import numpy as np
import os
import glob
import argparse



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

def plot_ethogram(etho_path, axes):
    """
    Note: plot_kymogram.py exists in curvature package. At the moment it is not using this function. Maybe this fucntion should go there.
    :param project_path:
    :param fig:
    :param axes:
    :return:
    """
    #kymo_path = os.path.join(project_path, 'skeleton_spline_K.csv')
    try:
        df_etho = pd.read_csv(etho_path, index_col=0)
        num_frames = len(df_etho)
        num_lines = 2
        cut_frames = num_frames // num_lines
        # df_etho = df_etho.rolling(100, center=True, min_periods=10).mean()
        fig, axs = plt.subplots(num_lines, 1, dpi=400, figsize=(10, 1*num_lines))

        for i, ax in enumerate(axs):
            start_idx = i * cut_frames
            end_idx = start_idx + cut_frames
            ax.imshow(df_etho.iloc[start_idx:end_idx].T, origin="upper", cmap='seismic_r', aspect=20*100, vmin=-0.06, vmax=0.06)
            ax.set_xticks(np.linspace(0, cut_frames, 5))
            ax.set_xticklabels(np.linspace(start_idx, end_idx, 5).astype(int))
            if i == num_lines - 1:
                ax.set_xlabel('Frame')            
            ax.set_ylabel('Beh. State')

            # Add the legend
            if i == 0:
                from matplotlib.lines import Line2D
                legend_elements = [Line2D([0], [0], color='red', label='Reversal'),
                                   Line2D([0], [0], color='blue', label='Forward motion')]
                ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.1, 1), frameon=True)

        plt.tight_layout()
        #plt.show()
        
    except:
        print('problem reading the kymograph csv file')

    return axes


def main(arg_list=None):

    # TODO: add beh annotation in speed plot
    # add head speed, total curvature, PC1, PC2, PC3, etc. See notebook wbfm_analysis
    # TODO: make it for every worm

    parser = argparse.ArgumentParser(description='Ehtogram Parser')
    parser.add_argument('--input_path', help='folder with the tracker position', required=True)
    parser.add_argument('--beh_annotation', help='Path to CSV with Behavior Annotations', required=True)
    parser.add_argument('--output_file', help='Output File Name', required=True)

    args = parser.parse_args(arg_list)
    main_folder = args.input_path
    etho_path = args.beh_annotation
    output_file = args.output_file

    project_folder = main_folder
    print("project folder is: ", project_folder)

    #Start Figure
    fig, gs = plot_main_figure(nrows=7, ncols=10)

    #Set size
    fig.set_size_inches(11.69, 8.27)  # Use if you need to put on A4
    # fig.set_size_inches(11.69, 4.13)  # Use if you need other formats

    #Ethogram
    ax1 = fig.add_subplot(gs[4, :-2])
    print(etho_path)
    plot_ethogram(etho_path, axes=ax1)
    ax1.set_ylabel('Beh. State')
    ax1.set_xlabel('Frames')

    plt.savefig(os.path.join(project_folder, 'ethogram.png'), dpi=500)

if __name__ == '__main__':

    main(sys.argv[1:])
