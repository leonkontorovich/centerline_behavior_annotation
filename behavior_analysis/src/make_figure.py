import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec




def plot_main_figure(project_folder):
    """Function to plot the main behavioural features of a single worm behavioral recording
    input:
    project_folder
    """
    nrows=3
    ncols=10

    fig = plt.figure(constrained_layout=True)
    gs = GridSpec(nrows, ncols, figure=fig)

    #kymogram
    ax1 = fig.add_subplot(gs[0, :])

    ax2 = fig.add_subplot(gs[1, :5])


    return fig

def plot_kymogram(project_path, fig, axes):
    kymo_path = os.path.join(project_path, 'skeleton_spline_K.csv')
    try:
        df_kymo = pd.read_csv(kymo_path, header=None)
        print(df_kymo.shape)
        fig, axes = plt.subplots()  # dpi=400, figsize=(40,4),)
        fig.suptitle(kymo_path)
        axes.imshow(df_kymo.T, origin="upper", cmap='seismic', extent=[0, df_kymo.shape[0], df_kymo.shape[1], 0],
                    aspect=20, vmin=-0.06, vmax=0.06)
        plt.show()


    except:
        print('problem reading the kymograph csv file')

    return fig, axes

project_folder = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/ZIM2165_Gcamp7b_worm1/2022-10-13_11-18_ZIM2165_worm1_Ch0-BH"

fig = plot_main_figure(project_folder)

kymo_fig, axes =

plt.show()