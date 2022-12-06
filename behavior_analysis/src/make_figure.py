import matplotlib.cm as cm
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pandas as pd
import os
import glob

from centerline.dev.track_plotting_functions import plot_tracks




def plot_main_figure(project_folder):
    """Function to plot the main behavioural features of a single worm behavioral recording
    input:
    project_folder
    """
    nrows=5
    ncols=10

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


if __name__ == '__main__':

    # TODO: add beh annotation in speed plot
    # add head speed, total curvature, PC1, PC2, PC3, etc. See notebook wbfm_analysis
    # TODO: make it for every worm

    main_folder = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/ZIM2165_Gcamp7b_worm6"
    project_folder = glob.glob(os.path.join(main_folder, "*worm*Ch0-BH*"))[0]
    print(project_folder)

    #Start Figure
    fig, gs = plot_main_figure(project_folder)


    # Kymogram
    ax1 = fig.add_subplot(gs[0, :-2])
    kymo_path = glob.glob(os.path.join(project_folder, "*skeleton_spline_K.csv"))[0]
    print(kymo_path)
    plot_kymogram(kymo_path, axes=ax1)
    ax1.set_ylabel('Body Segment')

    # track
    ax4 = fig.add_subplot(gs[0, -2:])
    track_df = pd.read_csv(glob.glob(os.path.join(main_folder, "*-TablePosRecord.txt"))[0])
    plot_tracks(df=track_df, ax=ax4)

    #Ethogram
    ax2 = fig.add_subplot(gs[1, :-2],sharex = ax1)
    ethogram_path = glob.glob(os.path.join(project_folder, '*beh_annotation.csv'))[0]
    print(ethogram_path)
    ethogram_df = pd.read_csv(ethogram_path, index_col=0) #header should not be None!
    ax2.imshow(ethogram_df.values.T, origin="upper", cmap='seismic',  vmin=-0.00005, vmax=0.00005, aspect=20*100)
    # pie chart
    ax4 = fig.add_subplot(gs[1, -2:])


    norm = mpl.colors.Normalize(vmin=-0.00005, vmax=0.00005)
    cmap = cm.get_cmap('seismic')

    forward_color = cmap(norm(-1))
    reversal_color = cmap(norm(1))
    quiescence_color = cmap(norm(0))
    print(quiescence_color)
    explode = (0, 0.1, 0.1)
    print(ethogram_df.count())
    ax4.pie(ethogram_df.value_counts(), explode=explode,
            colors = (forward_color, reversal_color, quiescence_color),
            labels = ['Forward', 'Reverse', 'Quiesence'],
            wedgeprops={"edgecolor":"k",'linewidth': 2})


    #Speed
    ax3 = fig.add_subplot(gs[3, :-2], sharex = ax1)
    speed_df_path=os.path.join(project_folder, 'raw_worm_speed.csv')
    speed_df = pd.read_csv(speed_df_path)
    #speed_df['Raw Speed (mm/s)'].rolling(window=83).mean().plot(ax=ax3)

    # print(len(speed_df))
    # print(len(ethogram_df.values))
    speed_df['Raw Speed Signed (mm/s)'] = speed_df['Raw Speed (mm/s)']*ethogram_df['0']
    speed_df['Raw Speed Signed (mm/s)'] = speed_df['Raw Speed Signed (mm/s)'] * -1 # to invert because fwd is -1 in the ethogram
    speed_df['Raw Speed Signed (mm/s)'].rolling(window=83).mean().plot(ax=ax3)
    ax3.set_ylabel('Speed (mm/s)')
    ax3.set_ylim([-.2, .2])
    ax3.axhline(0, color='r', linestyle='--', alpha=0.5)


    # Speed histogram
    ax6 = fig.add_subplot(gs[3, -2:])
    speed_df['Raw Speed Signed (mm/s)'].rolling(window=83).mean().plot.hist(bins=50, ax=ax6)
    ax6.set_xlim([-.2, .2])
    ax6.set_xlabel('Speed (mm/s)')

    plt.savefig(os.path.join(project_folder, 'behavioural_figure.png'), dpi=1500)
    plt.show()

    print('end of script')