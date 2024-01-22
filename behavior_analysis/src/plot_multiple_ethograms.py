#based on plot_ethogram.py

import os
import matplotlib.pyplot as plt
import pandas as pd
import glob
import os
import numpy as np


projects = glob.glob("/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/*worm*/*BH*/")


for project in projects:
    print(project)
    turns_path = os.path.join(project, "turns_annotation.csv")
    reversals_path = os.path.join(project, "beh_annotation.csv")


    df_turn = pd.read_csv(turns_path)
    turn_ethogram = np.expand_dims(df_turn['turn'], axis=0)

    df_reversals = pd.read_csv(reversals_path)
    #drop the first row, which is the start of the recording
    df_reversals = df_reversals.drop(df_reversals.index[0])
    reversals_ethogram = np.expand_dims(df_reversals['0'], axis=0)

    fig, axes = plt.subplots(nrows=2, dpi=100, sharex=True)
    axes[0].imshow(reversals_ethogram, origin="upper", cmap='tab10', aspect=5*500, vmin=-1, vmax=7)#aspect=20*100, vmin=-1, vmax=7) #vmin and vmax are needed to keep colors consistent
    axes[0].set_ylabel(None)
    axes[0].set_yticks([])
    axes[0].set_xlabel(None)
    axes[0].set_xticks([])

    axes[1].imshow(turn_ethogram, origin="upper", cmap='tab10', aspect=5*500, vmin=-1, vmax=7)#aspect=20*100, vmin=-1, vmax=7) #vmin and vmax are needed to keep colors consistent
    axes[1].set_ylabel(None)
    axes[1].set_yticks([])
    axes[1].set_xlabel(None)
    axes[1].set_xticks([])
    plt.show()