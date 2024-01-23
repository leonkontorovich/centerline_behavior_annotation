#cluster_create_labeled_videos (function from DLC, .mp4 video outputs)
import argparse
import os
import pandas as pd
import numpy as np
os.environ["DLClight"]="True"
import deeplabcut

print("python package imports finished")

ap = argparse.ArgumentParser()
ap.add_argument("-path_config_file", "--path_config_file", required=True, help="path to config file")
ap.add_argument("-videofile_path", "--videofile_path", required=True, help="path to the videofile")
ap.add_argument("-filtered", "--filtered", required=False, help="Specify if filtered")
args = vars(ap.parse_args())

print("These are the arguments:")
print(args)

path_config_file = args['path_config_file']
print(path_config_file)
#don't edit these:
#videos dont need to be on the config file: https://gitter.im/DeepLabCut/community?at=5e8f90a85d148a0460f7664a
VideoType = 'avi'
videofile_path = args['videofile_path']
print(videofile_path)
filtered = args['filtered']
print(filtered)
print("parsing finished")

#CREATE LABELED VIDEO
deeplabcut.create_labeled_video(path_config_file, videofile_path, videotype=VideoType, filtered=filtered)
print("deeplabcut.create_labeled_video finished")