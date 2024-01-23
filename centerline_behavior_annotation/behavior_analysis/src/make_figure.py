import matplotlib.cm as cm
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import colors
import pandas as pd
import numpy as np
import os
import glob

from centerline_behavior_annotation.centerline.dev.track_plotting_functions import plot_tracks
from imutils.src.plotting import *



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
    #kymo_path = os.path.join(project_path, 'skeleton_spline_K.csv')
    try:
        df_kymo = pd.read_csv(kymo_path, header=None)
        # print(df_kymo.shape)
        # fig, axes = plt.subplots()  # dpi=400, figsize=(40,4),)
        # fig.suptitle(kymo_path)
        axes.imshow(df_kymo.T, origin="upper", cmap='seismic', extent=[0, df_kymo.shape[0], df_kymo.shape[1], 0],
                    aspect=20, vmin=-0.06, vmax=0.06)

    except:
        print('problem reading the kymograph csv file')

    return axes


def main(arg_list):
    import argparse

    # TODO: add beh annotation in speed plot
    # add head speed, total curvature, PC1, PC2, PC3, etc. See notebook wbfm_analysis
    # TODO: make it for every worm

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--input_path', help='folder with the tracker position', required=True)

    args = vars(parser.parse_args())
    main_folder = args['input_path']

    #main_folder = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1"

    #OLD PARSER
    # parser.add_argument('-i', '--input_path', help='', required=True)
    # parser.add_argument('-k', '--kymo_path', help='', required=True)
    # parser.add_argument('-pcs', '--pcs_path', help='', required=True)
    # parser.add_argument('-stage', '--stage_path', help='', required=True)
    # parser.add_argument('-beh', '--beh_annotation_path', help='', required=True)
    # parser.add_argument('-speed', '--raw_worm_speed_path', help='', required=True)


    #TO RUN LOCALLY (with debugger)
    # main_folder = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221210/data/ZIM2165_Gcamp7b_worm3"

    #main_folder="/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/"

    #ALL
    project_folder = glob.glob(os.path.join(main_folder, "*worm*Ch0-BH*"))[0]
    print("project folder is: ", project_folder)

    #Start Figure
    fig, gs = plot_main_figure(nrows=7, ncols=10)

    #Set size
    fig.set_size_inches(11.69, 8.27)

    # Kymogram
    ax1 = fig.add_subplot(gs[0, :-2])
    kymo_path = glob.glob(os.path.join(project_folder, "skeleton_spline_K_signed_avg.csv"))[0]
    print(kymo_path)
    plot_kymogram(kymo_path, axes=ax1)
    ax1.set_ylabel('Body Segment')

    #Principal Components
    ax2 = fig.add_subplot(gs[1, :-2], sharex = ax1)
    pc_path = glob.glob(os.path.join(project_folder, "principal_components.csv"))[0]
    print(pc_path)
    pcs = pd.read_csv(pc_path)
    pcs[['PC1', 'PC2', 'PC3']].plot(ax=ax2)

    #PC 3d
    #beh_annotation =
    ax10 = fig.add_subplot(gs[1, -2:], projection='3d')
    pcs_avg = pcs.rolling(window=83, center=True).mean()
    ax10.scatter(pcs_avg[['PC1']], pcs_avg[['PC2']], pcs_avg[['PC3']], s=.25, vmin=-1e-4, vmax=1e-4, cmap='bwr')
    ax10.set_xlabel('PC1')
    ax10.set_ylabel('PC2')
    ax10.set_zlabel('PC3')
    ax10.set_ylabel('Smoothed Principal Components')
    #ax9.tick_params(labelsize=7)
    #ax9.set_axis_off()

    #total curvature
    ax3=fig.add_subplot(gs[2, :-2], sharex = ax1)
    df_kymo = pd.read_csv(kymo_path, header=None)
    df_kymo2 = df_kymo.abs()
    df_kymo2.sum(axis=1).plot(ax=ax3)
    ax3.set_ylabel('Total Absolute Curvature (mm⁻¹)')
    ax3.set_ylim([0, 4])

    # signed curvature
    ax4=fig.add_subplot(gs[3, :-2], sharex = ax1)
    df_kymo.sum(axis=1).plot(ax=ax4)
    ax4.set_ylabel('Signed Curvature (mm⁻¹)')
    ax4.set_ylim([-2, 2])
    ax4.axhline(0, color='r', linestyle='--', alpha=0.5)


    # track
    ax5 = fig.add_subplot(gs[0, -2:])
    track_df = pd.read_csv(glob.glob(os.path.join(main_folder, "*-TablePosRecord.txt"))[0])
    plot_tracks(df=track_df, ax=ax5)

    #Ethogram
    ax6 = fig.add_subplot(gs[4, :-2], sharex = ax1)
    ethogram_path = glob.glob(os.path.join(project_folder, 'beh_annotation.csv'))[0]
    print("Rev-Fwd ethogram is :" , ethogram_path)
    ethogram_df = pd.read_csv(ethogram_path, index_col=0) #header should not be None!
    ax6.imshow(ethogram_df.values.T, origin="upper", cmap='seismic',  vmin=-0.00005, vmax=0.00005, aspect=20*100)
    ax6.get_yaxis().set_visible(False)

    # pie chart
    ax6_2 = fig.add_subplot(gs[4, -2:])

    norm = mpl.colors.Normalize(vmin=-0.00005, vmax=0.00005)
    cmap = cm.get_cmap('seismic')
    forward_color = cmap(norm(-1))
    reversal_color = cmap(norm(1))
    quiescence_color = cmap(norm(0))

    #This is to account for the kymogram to have only fwd and reverse (and no quiescence)
    if len(ethogram_df['0'].value_counts()) == 2:
        explode = (0, 0.1)
        ax6_2.pie(ethogram_df['0'].value_counts(), explode=explode,
                colors=[forward_color, reversal_color],
                labels=['Forward', 'Reverse'],
                wedgeprops={"edgecolor": "k", 'linewidth': 2})

    # this is if there are three behavioural states in the ethogram_df
    if len(ethogram_df['0'].value_counts()) == 3:
        explode = (0, 0.1, 0.1)

        ax6_2.pie(ethogram_df['0'].value_counts(), explode=explode,
                colors = [forward_color, reversal_color, quiescence_color],
                labels = ['Forward', 'Reverse', 'Quiesence'],
                wedgeprops={"edgecolor":"k",'linewidth': 2})


    # Turns ethogram
    # make a color map of fixed colors
    cmap = colors.ListedColormap(['purple', 'white', 'green'])
    bounds = [-1, -0.5, 0.5, 1]
    norm = colors.BoundaryNorm(bounds, cmap.N)

    ax7 = fig.add_subplot(gs[5, :-2], sharex = ax1)
    turns_ethogram_path = glob.glob(os.path.join(project_folder, 'turns_annotation.csv'))[0]
    print(turns_ethogram_path)
    turns_ethogram_df = pd.read_csv(turns_ethogram_path, index_col=0) #header should not be None!
    ax7.imshow(turns_ethogram_df.values.T, origin="upper", cmap=cmap, norm=norm, aspect=20*100)#  vmin=-0.00005, vmax=0.00005, aspect=20*100)
    ax7.get_yaxis().set_visible(False)

    #Turns pie chart
    ax7_2 = fig.add_subplot(gs[5, -2:])
    print("The turn ethogram is: ", len(ethogram_df['0'].value_counts()), "counts")
    #This is to account for the kymogram to have only no turn and ventral (and no dorsal)
    if len(turns_ethogram_df['turn'].value_counts()) == 2:
        turns_explode = (0, 0.1)
        ax7_2.pie(turns_ethogram_df['turn'].value_counts(), explode=turns_explode,
                  colors=['white', 'green'],
                  labels=['No-Turn', 'Ventral'],
                  wedgeprops={"edgecolor": "k", 'linewidth': 2})

    if len(turns_ethogram_df['turn'].value_counts()) == 3:
        turns_explode = (0, 0.1, 0.1)
        colors = ['white', 'green', 'purple']
        labels = ['No-Turn', 'Ventral', 'Dorsal']
        print("colors size is, ", len(colors), "labels size is, ", len(labels), "turns ethogram size is, ", len(turns_ethogram_df['turn'].value_counts()))
        ax7_2.pie(turns_ethogram_df['turn'].value_counts(), explode=turns_explode,
                  colors=colors,
                  labels=labels,
                  wedgeprops={"edgecolor": "k", 'linewidth': 2})
    #Speed
    ax8 = fig.add_subplot(gs[6, :-2], sharex = ax1)
    speed_df_path=os.path.join(project_folder, 'signed_worm_speed.csv')
    speed_df = pd.read_csv(speed_df_path)

    speed_df['Raw Speed Signed (mm/s)'].rolling(window=83, center=True).mean().plot(ax=ax8)
    ax8.set_xticks(range(0, len(speed_df), 5000))
    #ax3.set_xlabel(speed_df.index[range(0, len(speed_df), 5000)].values)#,
    #ax3.set_xlabel(np.arange(0, len(speed_df), 5000))                                                                              #xticklabels=range(0, len(speed_df), 5000))
    ax8.set_ylabel('Smoothed Speed (mm/s)')
    ax8.set_ylim([-.25, .25])
    ax8.axhline(0, color='r', linestyle='--', alpha=0.5)

    # plot stimuli, does not work yet
    # start_indexes, counts = consecutive_count(ethogram_df['0'])
    # print(start_indexes)
    # print(counts)
    # # stimulus_start = [100, 7000, 15000]
    # # stimulus_length = [5000, 1000, 2000]
    # plot_stimuli(ax=ax3, stimulus_start=start_indexes, stimulus_length=counts, color='red', alpha=0.5)

    # Speed histogram
    ax9 = fig.add_subplot(gs[6, -2:])
    speed_df['Raw Speed Signed (mm/s)'].rolling(window=83, center=True).mean().plot.hist(bins=50, ax=ax9)
    ax9.axvline(0, color='r', linestyle='--', alpha=0.5)
    ax9.set_xlim([-.25, .25])
    ax9.set_xlabel('Speed (mm/s)')

    plt.savefig(os.path.join(project_folder, 'behavioral_summary_figure.pdf'), dpi=500)
    #plt.show()

    print('end of script')


if __name__ == '__main__':
    import sys
    main(sys.argv[1:])
