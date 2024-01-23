import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import yaml
from natsort import natsorted

# for each folder, get the agar concentration and the mean and median speed

wbfm_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/2022*/data/*worm*"

projects = glob.glob(wbfm_path)

for recording in natsorted(projects):
    # print(recording)
    try:
        yaml_filepath = os.path.join(recording, 'config.yaml')
        yaml_dict = yaml.safe_load(open(yaml_filepath))
        agar_concentration = yaml_dict['agar']
    except:
        agar_concentration = 'false'
        print('problem loading yaml file')

    try:
        file_string = os.path.join(recording, '*BH*/*raw_worm_speed.csv')
        speed_file = glob.glob(file_string)[0]
        speed = pd.read_csv(speed_file)
    except:
        speed = 0
        print('no speed file in this recording')

    try:
        print(recording, agar_concentration, speed['Raw Speed (mm/s)'].mean(), speed['Raw Speed (mm/s)'].median())
    except:
        print('nothing to print')
