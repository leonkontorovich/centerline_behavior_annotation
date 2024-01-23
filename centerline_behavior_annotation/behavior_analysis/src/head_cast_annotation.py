import pandas as pd
import numpy as np
import os
import glob
import matplotlib.pyplot as plt

# LOAD Project
project_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/"
kymo_path = os.path.join(project_path, "skeleton_spline_K_signed_avg.csv")

hilbert_freq_path = os.path.join(project_path, "hilbert_inst_freq.csv")


df_kymo = pd.read_csv(kymo_path, index_col=None, header=None)
df_hilbert_freq = pd.read_csv(hilbert_freq_path, index_col=None, header=None)

segment = 20

# Plotting
# copied form cross_product_kymo_plotting.py
fig, axes = plt.subplots(nrows= 2, dpi=100, sharex=True)

axes[0].imshow(df_kymo.T, origin="upper", cmap='seismic', extent=[0, df_kymo.shape[0], df_kymo.shape[1], 0],
             vmin=-0.06, vmax=0.06) #aspect=20,
axes[1].plot(df_hilbert_freq.iloc[:, segment])
# add a re doted line at y=0 to see if the sign is correct
axes[1].axhline(y=0, color='r', linestyle='--')
#axes[1].set_title('Cross Product')
axes[1].set_xlabel('Time (frames)')
axes[1].set_ylabel('Inst Frequency of segment ' + str(segment))
plt.show()