import glob
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def worm_speed(df):
    """
    Copy of the copied function.
    Original file in behaviour analysis.calculate_parameters.py
    Calculates the speed in mm/s of a dataframe which has timestamps in ms as index
    Copy of Charlie function in https://github.com/Zimmer-lab/wbfm/blob/a34c976cf73edea837ce1e2326b974ef36390962/wbfm/utils/general/postures/centerline_classes.py#L239
    """
    #TODO: This speed is not by default in mm/s, it is only in mm/s based on the current timestamp

    speed = np.sqrt(np.gradient(df['X']) ** 2 + np.gradient(df['Y']) ** 2)

    # tdelta = df.index[1] - df.index[0]  # units = nanoseconds
    tdelta = pd.Series(df.index).diff().mean()
    try:
        tdelta_s = tdelta.delta / 1e9
    except AttributeError:
        # Newer pandas versions have a different way of calculating the timedelta
        tdelta_s = pd.Timedelta(tdelta).total_seconds()
    speed_mm_per_s = speed / tdelta_s

    return speed_mm_per_s

main_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/figure_2_data/speeds"

speeds_path = glob.glob(os.path.join(main_path, "*speed*.csv"))

merged_speed_df= pd.DataFrame()

for speed_path in speeds_path:
    df = pd.read_csv(speed_path, index_col=0)

    merged_speed_df = pd.concat([merged_speed_df, df], axis=0)

merged_speed_df.plot.hist(bins=200)
plt.show()