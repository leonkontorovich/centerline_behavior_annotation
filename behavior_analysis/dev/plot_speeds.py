import pandas as pd
import glob
import os
import numpy as np
import matplotlib.pyplot as plt


fig, ax = plt.subplots()
fig2, ax2 = plt.subplots()

path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/bodypart0_coords_mm.csv"


df = pd.read_csv(path)

df['X']=df['x']
df['Y']=df['y']

speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)
#speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)

# tdelta = df.index[1] - df.index[0]  # units = nanoseconds
tdelta = pd.Series(df.index).diff().mean()
tdelta_s = 0.012 #1/(24*0.012)#tdelta.delta / 1e9
speed_mm_per_s = speed / tdelta_s

speed_df = pd.DataFrame(speed_mm_per_s)

speed_df.rolling(window=83, center=True).mean().plot(ax=ax)

speed_df.rolling(window=83, center=True).mean().plot.hist(bins=50,ax=ax2)

path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/bodypart50_coords_mm.csv"


df = pd.read_csv(path)

df['X']=df['x']
df['Y']=df['y']

speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)
#speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)

# tdelta = df.index[1] - df.index[0]  # units = nanoseconds
tdelta = pd.Series(df.index).diff().mean()
tdelta_s = 0.012 #1/(24*0.012)#tdelta.delta / 1e9
speed_mm_per_s = speed / tdelta_s

speed_df = pd.DataFrame(speed_mm_per_s)

speed_df.rolling(window=83, center=True).mean().plot(ax=ax)
speed_df.rolling(window=83, center=True).mean().plot.hist(bins=50,ax=ax2)
plt.show()

