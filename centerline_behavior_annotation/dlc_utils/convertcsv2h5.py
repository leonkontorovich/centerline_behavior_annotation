import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from natsort import natsorted
os.environ["DLClight"]="True"
import deeplabcut

config_filepath='/Volumes/scratch/neurobiology/zimmer/fabio/code/deeplabcut_projects/autoscope_trial-fabo-2022-05-04/config.yaml'


deeplabcut.convertcsv2h5(config_filepath, userfeedback=True)
print('done')