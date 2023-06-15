import glob
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def worm_speed(df):
    """Calculates the speed in mm/s of a dataframe which has timestamps in ms as index
    Copy of Charlie function in https://github.com/Zimmer-lab/wbfm/blob/a34c976cf73edea837ce1e2326b974ef36390962/wbfm/utils/general/postures/centerline_classes.py#L239
    """
    #TODO: This speed is not by default in mm/s, it is only in mm/s based on the current timestamp

    speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)

    # tdelta = df.index[1] - df.index[0]  # units = nanoseconds
    tdelta = pd.Series(df.index).diff().mean()
    tdelta_s = tdelta.delta / 1e9
    speed_mm_per_s = speed / tdelta_s

    return speed_mm_per_s

main_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/figure_2_data/stage_positions/Gcamp7b"

stage_positions_paths = glob.glob(os.path.join(main_path, "*Table*"))

merged_speed_df= pd.DataFrame()

for stage_positions_path in stage_positions_paths:
    df = pd.read_csv(stage_positions_path, index_col='time')
    df.index = pd.DatetimeIndex(df.index)
    speed_mm_per_s = worm_speed(df)
    speed_mm_per_s_df = pd.DataFrame()
    speed_mm_per_s_df['Raw Speed (mm/s)'] = speed_mm_per_s
    merged_speed_df = pd.concat([merged_speed_df, speed_mm_per_s_df], axis=0)

merged_speed_df.plot.hist()
plt.show()