import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import os
import glob
from curvature.src.annotate_behaviour import ethogram_figure


main_path='/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/'

beh_paths=glob.glob(os.path.join(main_path,'*worm*/*BH*'))

for project in beh_paths:
    print(project)

    kymo_path=glob.glob(os.path.join(project, '*skeleton_spline_K.csv'))[0]
    df_kymo=pd.read_csv(kymo_path, header=None)

    beh_annotation_path = glob.glob(os.path.join(project, '*beh_annotation.csv'))[0]
    beh_annotation_df = pd.read_csv(beh_annotation_path, index_col=0, header=None)
    # beh_annotation_df= beh_annotation_df*-1
    # beh_annotation_df.to_csv(os.path.join(project, 'beh_annotation.csv'))
    fig = ethogram_figure(df_kymo, beh_annotation_df)
    #fig.set_size_inches(400, 2)
    plt.show()

