import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os


def worm_speed(df):

    speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)

    # tdelta = df.index[1] - df.index[0]  # units = nanoseconds
    tdelta = pd.Series(df.index).diff().mean()
    tdelta_s = tdelta.delta / 1e9
    speed_mm_per_s = speed / tdelta_s

    return speed_mm_per_s


main_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/*worm[1-9]/*TablePosRecord.txt"
df_list = glob.glob(main_path, recursive=True)
print(df_list)

#df_list = ["/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221119/data/ZIM2165_Gcamp7b_worm5_2/2022-11-19_15-06_ZIM2165_GC7b_worm5_2-TablePosRecord.txt"]

mean_speed_list = []
median_speed_list = []
for df_path in df_list:
    #print(df_path)
    df = pd.read_csv(df_path, index_col='time')

    df.index = pd.DatetimeIndex(df.index)


    speed_mm_per_s = worm_speed(df)

    #print(type(speed_mm_per_s))

    # print("mean is ", np.mean(speed_mm_per_s))
    if np.mean(speed_mm_per_s) != 0:
        mean_speed_list.append(round(np.mean(speed_mm_per_s),3))
        # print("median is ", np.median(speed_mm_per_s))
    if np.median(speed_mm_per_s) != 0:
        median_speed_list.append(round(np.median(speed_mm_per_s),3))

print(mean_speed_list)

print(median_speed_list)

fig, axes = plt.subplots(ncols=2)
axes[0].hist(mean_speed_list, 20)
axes[1].hist(median_speed_list, 20)

for ax in axes:
    ax.set_xlim([0, .3])
plt.show()

