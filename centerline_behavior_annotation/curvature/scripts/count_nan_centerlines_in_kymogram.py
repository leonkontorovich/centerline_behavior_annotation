# Based on code that is in centerline/dev/visualize_centerlines.ipynb

import pandas as pd
import glob

spline_path_list = glob.glob('/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/2*/data/*/*BH*/*spline_K.csv')

list_of_nan_values = []
list_of_relative_nan_values = []

list_of_nan_values = []
list_of_relative_nan_values = []

for spline_path in spline_path_list:

    print(spline_path)
    df_kymo = pd.read_csv(spline_path, header=None)
    number_of_nan_values = (df_kymo.isna().any(axis=1).sum())
    print(number_of_nan_values)
    relative_nan_values = number_of_nan_values / df_kymo.shape[0]

    print(number_of_nan_values)
    print(relative_nan_values)


    list_of_nan_values.append(number_of_nan_values)
    list_of_relative_nan_values.append(relative_nan_values)
    # print('list of nan values')
    # for i in list_of_nan_values:
    #     print(i)
    # print('list of relative nan values')
    # for ii in list_of_relative_nan_values:
    #     print(ii)
print('end')
