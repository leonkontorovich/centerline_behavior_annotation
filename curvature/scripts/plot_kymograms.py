import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os
import glob


main_path='/Volumes/scratch/neurobiology/zimmer/ulises/test_area/autoscope_snakemake/data/'
#main_path="/Users/ulises.rey/local_data/local_spline_files_20230124"

kymo_paths=glob.glob(os.path.join(main_path,'*w*2*/*/*_skeleton_spline_K.csv'))
#kymo_paths=["/Users/ulises.rey/local_data/test_spline/_skeleton_spline_K.csv"]

nan_centerlines=[]

for kymo_path in kymo_paths:
    print(kymo_path)
    #kymo_path = os.path.join(project, 'skeleton_spline_K.csv')
    try:
        df_kymo=pd.read_csv(kymo_path, header=None)
        print(df_kymo.shape)
        fig, axes = plt.subplots()  # dpi=400, figsize=(40,4),)
        fig.suptitle(kymo_path)
        #
        #print('applying rolling mean')
        #df_kymo = df_kymo.rolling(48, center=True, min_periods=24).mean()
        #df_kymo.to_csv(kymo_path, index=False, header=False)
        axes.imshow(df_kymo.T, origin="upper", cmap='seismic', extent=[0, df_kymo.shape[0], df_kymo.shape[1], 0],
                    aspect=2.5, vmin=-0.02, vmax=0.02)
        #decorate figure
        axes.set_xlabel('Volume')
        axes.set_ylabel('Body Part')
        plt.show()
    except: print('problem reading the kymograph csv file')

