#cluster_train_network (function from DLC, .mp4 video outputs)
import argparse
import os
import pandas as pd
import numpy as np
os.environ["DLClight"]="True"
import deeplabcut
#from natsort import natsorted

ap = argparse.ArgumentParser()
ap.add_argument("-path_config_file", "--path_config_file", required=True, help="path to config file")
ap.add_argument("-displayiters", "--displayiters", required=True, help="")
ap.add_argument("-saveiters", "--saveiters", required=True, help="")
args = vars(ap.parse_args())

path_config_file = args['path_config_file']
displayiters = args['displayiters']
saveiters = args['saveiters']



#ADD MAYBE CREATE LABELED VIDEO
deeplabcut.create_training_dataset(path_config_file, net_type='resnet_50', augmenter_type='imgaug')
print("Training dataset created... Training starts next...")
deeplabcut.train_network(path_config_file, shuffle=1, displayiters=displayiters, saveiters=saveiters)
