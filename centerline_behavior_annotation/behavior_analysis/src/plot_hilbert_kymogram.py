
import matplotlib.pyplot as plt
import pandas as pd
import glob
def plot_kymogram(kymo_path, smooth, axes):
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
        if smooth:
            df_kymo=df_kymo.rolling(window=24, min_periods=1, win_type='gaussian', center=True).mean(std=3)

        axes.imshow(df_kymo.T, origin="upper", cmap='seismic', extent=[0, df_kymo.shape[0], df_kymo.shape[1], 0],
                    aspect=20, vmin=-0.5, vmax=0.5)#aspect=5, vmin=-0.005, vmax=0.005)

    except:
        print('problem reading the kymograph csv file or plotting it')

    return axes

paths = glob.glob("/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/hilbert_inst_freq.csv")
#print(paths)
smooth = False
for path in paths:
    print(path)
    fig, axes = plt.subplots()

    axes = plot_kymogram(path, smooth, axes)
    fig.suptitle(path)
    plt.show()
print("end")