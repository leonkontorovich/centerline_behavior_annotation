#defines some functions, useful when training DLC

import re
import os
import pandas as pd
from natsort import natsorted
import tifffile as tiff
import cv2
import seaborn as sns
import numpy as np

def label_videos(file_path, h5_filepath, output_filepath, fourcc, fps):
    """
    Annotate all frames of an avi file using the hdf5 output file from DeepLabCut.
    Equivalent version of deeplabcut.label_videos() but works on single avi file, annotates all frames.
    Parameters:
    -----------
    file_path: str
    path to the input avi file
    h5_filepath: str
    path to the dlc h5 file with the bodyparts coordinates
    output_filepath: str
    path where the output avi file will be saved (has to exist)
    fourcc: str
    fourcc code
    0 means no coompression, other codecs will have some compression
    To learn more visit: https://www.fourcc.org/
    fps: str
    Number of frames per second at which the recording was acquired, and at which you want to save the output file
    """
    #corrects fourcc nomenclature
    if fourcc == '0':
        fourcc=0
    else:
        fourcc=cv2.VideoWriter_fourcc(fourcc)

    #make fps a float
    fps=float(fps)
    
    
    #read h5 file from dlc
    print(h5_filepath)
    df = pd.read_hdf(h5_filepath)
    #list with the tracks
    tracks=df.columns.levels[0]
    #list with the bodyparts
    bodyparts=df.columns.levels[1]

    #video reader
    video_cap = cv2.VideoCapture(file_path)
    
    #video writer

    frame_width = int(video_cap.get(3))
    frame_height = int(video_cap.get(4))
    video_out = cv2.VideoWriter(output_filepath,cv2.VideoWriter_fourcc('M','J','P','G'), fps, (frame_width,frame_height))

    #coloring
    color_values =  sns.color_palette(palette='tab10' ,n_colors=bodyparts.shape[0])
    bodypart_keys = df.columns.levels[1].values
    color_dict=dict(zip(bodypart_keys,255*np.array(color_values)))
    
    print('everything loaded')
    #counter (only for dev purposes)
    k=0
    while(video_cap.isOpened()):
        ret,frame=video_cap.read()
        if ret == True:
            print('ret == True')
            for idx, track in enumerate(natsorted(tracks)):
                print('track: ' + track)
                #print(df[track])
                for bodypart in bodyparts:
                    #print('body part: ' + bodypart)
                    x_coord=df[track][bodypart]['x'][k]
                    y_coord=df[track][bodypart]['y'][k]
                    if np.isnan(x_coord)== False or np.isnan(y_coord)==False:
                        cv2.circle(frame, (int(x_coord), int(y_coord)), 1, tuple(color_dict[bodypart]), 2)
        video_out.write(frame)
        k=k+1
#         if k==250:
#             video_cap.release()
#             video_out.release()
    video_cap.release()
    video_out.release()

def extract_frames(input_image, output_folder, frames_list, file_format):
    """
    This function is not maintained anymore in here, check imutils package!
    Parameters:
    -----------
    input_image: str,
        Path to the input_image (stack)
    output_folder: str
        Path to the folder where the images will be saved
    frames_list: list?
        list of integers, frames that will be extracted
    file_format: str
        extension of the output file, for example 'png' or 'tiff' (not sure this works)
    """
    print('This function is not maintained anymore in here, check imutils package!')
    with tiff.TiffFile(input_image) as tif:
        for i, page in enumerate(tif.pages):
            #if the image is not on the frames_list then skip
            if i in frames_list:
                img=page.asarray()
                #print(os.path.join(output_folder,'img'+str(i)+'.'+str(file_format)))
                tiff.imwrite(os.path.join(output_folder,'img'+str(i)+'.'+str(file_format)),img)


#defines two functions, one to rename img file names, the other to rename the csv file.
def add_zeros_to_filename():
    print('This function is now on the imutils package')

def add_zeros_to_csv(path, scorer_name, len_max_number=6):
    """
    Change the row name of the CollectedData.csv from DeepLabCut to include zeros when needed.
    It has a sister function: add_zeros_to_filename

    Parameters:
    -----------
    path: str,
        Path to directory with the CollectedData_Scorer.csv file
    scorer_name: str
        Name of the DLC scorer
    len_max_number: int
        number of digits the number should have, default is 6
    """
    
    #load csv file produced with the DLC_annotation_assistant.ijm Fiji macro (which does not have the numbers correct)
    csv_filename='CollectedData_'+scorer_name+'.csv'
    csv_file=os.path.join(path,csv_filename)
    
    #it is not a good idex to have index_col=0 beucase index are not mutables
    df=pd.read_csv(csv_file, index_col=0)
    df.head(10)
    scorer=df.columns.get_level_values(0)[0]

    #create regex to get the filename from the pandas dataframe
    regex_name = re.compile(r'img\d+.png')

    #create regex to get the number in the filename
    regex_num=re.compile(r'\d+')

    #len_max_number (should be hard coded or calculated somewhere):
    len_max_number=6

    #iterate over idx (it includes the first two idx: 'bodyparts' and 'coords')
    for idx in df.index:
        #skip the first two rows (bodyparts and coords) /It would be better to have an error handler?
        if idx=='bodyparts' or idx=='coords': continue
        
        #print(idx)
        #get the filename (ex: img00245.png)
        filename=regex_name.search(idx).group(0)
        #print(filename)

        #get the number in the filename (ex: 00245)
        number=regex_num.search(filename).group(0)
        #print(number)

        #if the number has less digits than the max add zeros until it has same
        if len(str(number)) < len_max_number:
            while len(str(number)) < len_max_number:
                number='0'+str(number)
            #output contains the number with the added zeros
            new_number=number
            #print(output)
            #this contains a string with the name before the filename
            new_name=re.split(regex_name,idx)[0]
            #print('new name'+str(new_name))
            #now we add it the new filename
            new_name=new_name+'img'+new_number+'.png'
            #we save it in the corresponding row of the dataframe
            df.rename(index={idx: new_name}, inplace=True)
            #print(new_name)
            #print(idx)

    df.sort_index(inplace=True)
    #print(df)
    #we save the dataframe into csv file
    csv_filename_new='CollectedData_'+scorer_name+'_new.csv'
    csv_file_new=os.path.join(path,csv_filename_new)
    #print(csv_file_new)
    df.to_csv(csv_file_new)
    
    #next step
    return print('Now: \n 0. Rename CollectedData.csv to CollectedData_original.csv, and CollectedData_new.csv to CollectedData.csv \n 1. Double check that scorers are alright "Ulises", "Ulises" and not "Ulises1", "Ulises2", etc. \n 2. Convert csv to hdf5 with deeplabcut.convertcsv2h5(path))')