import pandas as pd
import glob
import os
import numpy as np
import matplotlib.pyplot as plt
from natsort import natsorted
import matplotlib.colors as mcolors



path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/bodypart*_coords_mm.csv"
files = glob.glob(path)

fig, axes = plt.subplots(2)

colors = list(mcolors.TABLEAU_COLORS.keys())
print(colors)

for idx, file in enumerate(natsorted(files)):

    print(file)
    df = pd.read_csv(file)

    df['X']=df['x']
    df['Y']=df['y']

    df.loc[0:10].plot(x='X', y='Y', ax=axes[0], color=colors[idx])
    df.loc[500:510].plot(x='X', y='Y', ax=axes[0], color=colors[idx])
    df.loc[1000:1010].plot(x='X', y='Y', ax=axes[0], color=colors[idx])
    df.loc[1500:1510].plot(x='X', y='Y', ax=axes[0], color=colors[idx])
    df.loc[2000:2010].plot(x='X', y='Y', ax=axes[0], color=colors[idx])

    if "bodypart15" in file:
        df.plot(x='X', y='Y', ax=axes[0], color='k', linewidth=0.5, alpha=0.5)



    #Speed
    speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)
    #speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)

    # tdelta = df.index[1] - df.index[0]  # units = nanoseconds
    tdelta = pd.Series(df.index).diff().mean()
    tdelta_s = 0.012 #1/(24*0.012)#tdelta.delta / 1e9
    speed_mm_per_s = speed / tdelta_s

    speed_df = pd.DataFrame(speed_mm_per_s)

    speed_df.rolling(window=83, center=True).mean().plot(ax=axes[1])

    #speed_df.rolling(window=83, center=True).mean().plot.hist(bins=50,ax=ax2)

axes[0].invert_xaxis()
axes[0].invert_yaxis()
plt.show()

