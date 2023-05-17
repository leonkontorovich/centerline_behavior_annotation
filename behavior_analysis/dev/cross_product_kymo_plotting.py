# Plots the cross product and the kymogram of a recording

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
from curvature.src.make_PCA import *
from curvature.src.annotate_reversals import *
import os

exp_path = "/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH"
project = "/Volumes" + exp_path

df_kymo = pd.read_csv(os.path.join(project, "skeleton_spline_K_signed_avg.csv"), header=None)

principal_components_df = pd.read_csv(os.path.join(project, "principal_components.csv"))
average_window = 1

pc1_pc2_df = extract_vectors_from_PC_df(principal_components_df, avg_win=average_window)
cross_product_df = calculate_cross_product(pc1_pc2_df)

# Does cross product result in the per convention accepted sign? (cp<0==rev, cp>0==fwd?)
# if not, flip the sign
cross_product_df = - cross_product_df

# plot
fig, axes = plt.subplots(nrows= 2, dpi=100, sharex=True)

axes[0].imshow(df_kymo.T, origin="upper", cmap='seismic', extent=[0, df_kymo.shape[0], df_kymo.shape[1], 0],
            aspect=20, vmin=-0.06, vmax=0.06)
axes[1].plot(cross_product_df['Cross_Product'])
# add a re doted line at y=0 to see if the sign is correct
axes[1].axhline(y=0, color='r', linestyle='--')
plt.show()

# binarize
# values_arr = binarize_cross_product(cross_product_df)
#alternative binarize
values = [float(value) for value in cross_product_df['Cross_Product'].values]
values_arr = np.array(values)
values_arr[values_arr > 0] = 1
values_arr[values_arr < 0] = -1


# plot
# fwd_red_a = np.expand_dims(rv_fwd_ethogram['0'], axis=0)

values_arr = np.expand_dims(values_arr, axis=0)

fig, axes = plt.subplots(nrows= 1, dpi=100, sharex=True)
axes.imshow(values_arr, origin="upper", cmap='tab10', aspect=20*100)
axes.set_title('Ethogram Fwd-Rev')
axes.set_yticks([])
plt.show()