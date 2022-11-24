import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pandas as pd
import os
import glob




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

project_folder = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/ZIM2165_Gcamp7b_worm6/2022-10-13_15-58_ZIM2165_worm6_Ch0-BH"
print(project_folder)

#Start Figure
fig, gs = plot_main_figure(project_folder)


# Kymogram
ax1 = fig.add_subplot(gs[0, :])
kymo_path = glob.glob(os.path.join(project_folder, "*skeleton_spline_K.csv"))[0]
print(kymo_path)
plot_kymogram(kymo_path, axes=ax1)

#Ethogram
ax2 = fig.add_subplot(gs[1, :],sharex = ax1)
ethogram_path = glob.glob(os.path.join(project_folder, '*beh_annotation.csv'))[0]
print(ethogram_path)
ethogram_df = pd.read_csv(ethogram_path, index_col=0, header=None)
ax2.imshow(ethogram_df.values.T, origin="upper",cmap='seismic',  vmin=-0.00005, vmax=0.00005, aspect=20*100)
#Speed
ax3 = fig.add_subplot(gs[3, :], sharex = ax1)
speed_df_path=os.path.join(project_folder, 'raw_worm_speed.csv')
speed_df = pd.read_csv(speed_df_path)
speed_df['Raw Speed (mm/s)'].rolling(window=83).mean().plot(ax=ax3)

speed_df['Raw Speed Signed (mm/s)'] = speed_df['Raw Speed (mm/s)']*ethogram_df.values.T[:-1]
speed_df['Raw Speed Signed (mm/s)'].rolling(window=83).mean().plot(ax=ax3)

plt.show()