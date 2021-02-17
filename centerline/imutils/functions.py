import cv2
import tifffile as tiff

import numpy as np
import matplotlib.pyplot as plt
import os
from natsort import natsorted
import re



def tiff2avi(tiff_path, avi_path, fourcc, fps):
    """
    Convert tiff file into avi file with the specified fourcc codec and fps
    The isColor parameter of the writer is harcoded set to False.

    Parameters:
    -----------
    tiff_path: str,
        Path to the tiff file
    avi_path: str
        Path to the output file
    fourcc: fourcc code
        0 means no coompression, other codecs will have some compression
        To learn more visit: https://www.fourcc.org/
    fps: float (should it be int?)
        Number of frames per second at which the recording was acquired

    To improve:
    ----------
    Write Multifile as option, so it can be set to True

    """

    #corrects fourcc nomenclature
    if fourcc == '0':
        fourcc=0
    else:
        fourcc=cv2.VideoWriter_fourcc(*fourcc)
    
    #make fps a float
    fps=float(fps)
    
    #tiff read object
    with tiff.TiffFile(tiff_path, multifile=False) as tif:
        #print(tif)
        frameSize=tif.pages[0].shape
        frame_height, frame_width=tif.pages[0].shape
        video_out = cv2.VideoWriter(avi_path, apiPreference=0, fourcc=fourcc, fps=fps, frameSize=(frame_width,frame_height), isColor=False)

        for i, page in enumerate(tif.pages):
            #print(i)
            img=page.asarray()
            #img=cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
            video_out.write(img)
            #if i>20: break
    video_out.release()


def ometiff2bigtiff(path):
    """
    List all ome.tiff in a directory and make them one bigtiff
    Somehow it gives an error for the last ome tiff, but resulting .btf is fine.

    IMPORTANT: This ometiff2big tiff removes the Z-Stack information in a recording with Z stacks!
    At least if the number of Z Stacks is inconsistent, which is the case for the current writer in ome.tiff. While recording, the microscope saves the ome.tiff file even before the z-stack is finished.
    
    Parameters:
    -----------
    path: str,
        Path to the directory containing the several ome tiff files.

    """
    print(path)
    if path.endswith('/'):
        output_filename=path+re.split('/',path)[-2]+'bigtiff.btf'
    else:
        output_filename=path+'/'+re.split('/',path)[-1]+'bigtiff.btf'
    with tiff.TiffWriter(output_filename, bigtiff=True) as output_tif:
        for file in natsorted(os.listdir(path)):
            print(f'list is {os.listdir(path)}')
            print(os.path.join(path,file))
            if file.endswith('ome.tif') and 'bg' not in file:
                print(os.path.join(path,file))
                with tiff.TiffFile(os.path.join(path,file), multifile=False) as tif:
                    #print('entered writing')
                    hyperstack = tif.asarray()
                    #omexmlMetadataString = tif.ome_metadata IF YOU RUN THIS LINE IT GIVES ERRORS!
                    #print('writing...')
                    output_tif.save(hyperstack, photometric='minisblack')#, description=omexmlMetadataString)
        

        