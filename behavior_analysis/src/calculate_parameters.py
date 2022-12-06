import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

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

def read_and_save_speed(project):
    """
    wrapper
    :param project:
    :return:
    """
    #print(project)

    df_path = glob.glob(os.path.join(project,"*TablePosRecord.txt"))[0]
    df = pd.read_csv(df_path, index_col='time')

    df.index = pd.DatetimeIndex(df.index)

    #print('entered function')
    speed_mm_per_s = worm_speed(df)
    #print(speed_mm_per_s)
    speed_mm_per_s_df = pd.DataFrame()
    speed_mm_per_s_df['Raw Speed (mm/s)']=speed_mm_per_s
    behaviour_directory = glob.glob(os.path.join(project+"/*BH"))[0]
    #print(behaviour_directory)
    speed_mm_per_s_df.to_csv(os.path.join(behaviour_directory, 'raw_worm_speed.csv'))
    #print('saved to csv')


# Run single project
# project = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/ZIM2165_Gcamp7b_worm6"
# read_and_save_speed(project)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--input_path', help='folder with the tracker position', required=True)

    args = vars(parser.parse_args())
    project = args['input_path']

    read_and_save_speed(project)

