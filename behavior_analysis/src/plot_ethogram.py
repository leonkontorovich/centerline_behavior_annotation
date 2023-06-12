import os
import matplotlib.pyplot as plt
import pandas as pd
import glob
import os
import numpy as np

# path = "/Users/ulises.rey/local_data/test_beh_annotation/1127_w1/turn_annotation_timeseries.csv"
# ethogram = pd.read_csv(path, index_col=0)
#
# a = np.expand_dims(ethogram['Annotation'], axis=0)
#
# fig, ax = plt.subplots(dpi=100)
# ax.imshow(a, origin="upper", cmap='tab10', aspect=20*100)


# path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/beh_annotation.csv"
# rv_fwd_ethogram = pd.read_csv(path, index_col=0)
# rv_fwd_ethogram.fillna(0, inplace=True)
# fwd_red_a = np.expand_dims(rv_fwd_ethogram['0'], axis=0)
#
# fig, axes = plt.subplots(nrows= 1, dpi=100, sharex=True)
# axes.imshow(rv_fwd_ethogram.T, origin="upper", cmap='tab10', aspect=20*100)
# axes.set_title('Ethogram Fwd-Rev')
# axes.set_yticks([])
#
# #fig, axes = plt.subplots(nrows= 1, dpi=100, sharex=True)
# #axes[0].imshow(rv_fwd_ethogram.T, origin="upper", cmap='tab10', aspect=20*100)
# #axes[0].set_title('Ethogram Fwd-Rev')
# #axes[1].imshow(a, origin="upper", cmap='tab10', aspect=20*100)
# #axes[1].set_title('Ethogram with Turns')
#
# # for ax in axes:
# #     ax.set_yticks([])
#
# plt.show()


main_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/"
#path=os.path.join(main_path,"202*/data/*/*/ground_truth_beh_annotation/beh_annotation_timeseries.csv")
#path=os.path.join(main_path,"202*/data/*/*/beh_annotation_manual_corrected_timeseries.csv")
path=os.path.join(main_path,"20221127/data/*worm*/*/turns_annotation.csv")
print(path)
#path="/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/ground_truth_beh_annotation/simplest_turn_annotation_timeseries.csv"
beh_annotation_files = glob.glob(path)
print("there are", len(beh_annotation_files), "beh_annotation_timeseries files:")
beh_annotation_files
for file in beh_annotation_files:
    print(file)
    df=pd.read_csv(file)
    df['turn']
    a = np.expand_dims(df['turn'], axis=0)
    fig, ax = plt.subplots(dpi=300)
    ax.imshow(a, origin="upper", cmap='tab10', aspect=5*500, vmin=-1, vmax=7)#aspect=20*100, vmin=-1, vmax=7) #vmin and vmax are needed to keep colors consistent
    ax.set_ylabel(None)
    ax.set_yticks([])
    ax.set_xlabel(None)
    ax.set_xticks([])
    plt.show()