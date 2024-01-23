#cluster_label_videos
import argparse
import os
import pandas as pd
import numpy as np
import cv2
from natsort import natsorted
import re

#this is kind of outdated, check dlc_utils.py label_video()*
#this is kind of outdated, check dlc_utils.py label_video()*
#this is kind of outdated, check dlc_utils.py label_video()*
#this is kind of outdated, check dlc_utils.py label_video()*
#this is kind of outdated, check dlc_utils.py label_video()*
#this is kind of outdated, check dlc_utils.py label_video()*
# * However its implementation to run on the cluster is not ready yet for dlc_utils.py

ap = argparse.ArgumentParser()
ap.add_argument("-video", "--videofile_path", required=True, help="path to the videofile")
ap.add_argument("-h5", "--h5", required=True, help="path to the hdf5 file")
args = vars(ap.parse_args())

print('args: \n')
print(args)

#writing in an avi file
file_path=args['videofile_path']




##loading output of DLC
h5_path=args['h5']#'/groups/zimmer/Ulises/code/deeplabcut_projects/HeadTail-Ulises-2020-08-10/videos/'

df = pd.read_hdf(h5_path)
scorer=df.columns.get_level_values(0)[0]
head_x=df[scorer]['nose']['x'].values
head_y=df[scorer]['nose']['y'].values
tail_x=df[scorer]['tail']['x'].values
tail_y=df[scorer]['tail']['y'].values

#video reader
video_cap = cv2.VideoCapture(file_path)
#video writer
fps=167
frame_width = int(video_cap.get(3))
frame_height = int(video_cap.get(4))
output_filepath=re.split('.avi',args['videofile_path'])[0]+'_labeled.avi'


print('filepath: \n')
print(output_filepath)


video_out = cv2.VideoWriter(output_filepath,cv2.VideoWriter_fourcc('M','J','P','G'), fps, (frame_width,frame_height))

#alpha parameter
alpha=.25
#counter
k=0
while(video_cap.isOpened()):
    ret,frame=video_cap.read()
    if ret == True:
        #copy for the alpha merging
        output=frame.copy()
        cv2.circle(frame, (int(head_x[k]), int(head_y[k])), 2, (20,240,20), 2)
        cv2.circle(frame, (int(tail_x[k]), int(tail_y[k])), 2, (255,20,255), 2)
        #merge to do alpha
        cv2.addWeighted(frame, alpha, output, 1-alpha, 0, output)
        #draw a black dot on the head/tail
        cv2.rectangle(output,(int(head_x[k]), int(head_y[k])),(int(head_x[k]), int(head_y[k])), (0,0,0))
        cv2.rectangle(output,(int(tail_x[k]), int(tail_y[k])),(int(tail_x[k]), int(tail_y[k])), (0,0,0))
        video_out.write(output)
        k=k+1

video_cap.release()
#video_cap.release()
video_out.release()
cv2.destroyAllWindows()