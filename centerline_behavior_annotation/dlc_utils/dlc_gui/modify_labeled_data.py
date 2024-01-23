import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from natsort import natsorted
os.environ["DLClight"]="True"
import deeplabcut



#list_labeled_csv = glob.glob(path)

labeled_csv = "/Users/ulises.rey/local_code/deeplabcut_projects/active_sensing_RIA-josefine_meyer-2023-06-01/labeled-data/2023-05-19_16-15_zim2391_worm6_Ch1_worm6_raw_stack_cropped_normalised_subsampled/CollectedData_josefine_meyer.h5"

df = pd.read_hdf(labeled_csv)
scorer=df.columns.get_level_values(0)[0]
x= df[scorer]['soma']['x'].values

print(x)