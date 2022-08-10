import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os
import glob


main_path='/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20220729/20220729_12ms/data/'

beh_paths=glob.glob(os.path.join(main_path,'*worm*/*BH*'))

for project in beh_paths:
    print(project)
    kymo_path = os.path.join(project, 'skeleton_spline_K.csv')
    df_kymo=pd.read_csv(kymo_path, header=None)
    print(df_kymo.shape)
    fig, axes=plt.subplots()#dpi=400, figsize=(40,4),)
    fig.suptitle(kymo_path)
    axes.imshow(df_kymo.T,origin="upper",cmap='seismic',extent=[0,df_kymo.shape[0],df_kymo.shape[1],0],aspect=20,vmin=-0.06,vmax=0.06)
    plt.show()