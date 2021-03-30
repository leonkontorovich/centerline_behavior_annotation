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


def ometiff2bigtiffZ(path, output_dir=None, actually_write=True, num_slices=None):
    """
    This function was copied from video_conversions/Python/bigtiff/
    """
    if output_dir is None:
        output_dir = path
    if path.endswith('/'):
        output_filename=output_dir+re.split('/',path)[-2]+'bigtiff.btf'
    else:
        output_filename=output_dir+'/'+re.split('/', path)[-1]+'bigtiff.btf'

    print(f"File will be written that is divisible by {num_slices}")
    print(f"And written to filename {output_filename}")
    total_num_frames = 0
    buffer = []
    with tiff.TiffWriter(output_filename, bigtiff=True) as output_tif:
        for i_file, file in enumerate(natsorted(os.listdir(path))):
            if not file.endswith('ome.tif') or 'bg' in file:
                continue
            this_ome_tiff = os.path.join(path,file)
            print("Currently reading: ")
            print(this_ome_tiff)
            with tiff.TiffFile(this_ome_tiff, multifile=False) as tif:
                for i, page in enumerate(tif.pages):
                    print(f'Page {i}/{len(tif.pages)} in file {i_file}')
                    # Bottleneck line
                    img = page.asarray()
                    # Convert to proper format, and write single frame
                    # img = (alpha*img).astype('uint8')
                    total_num_frames += 1
                    if num_slices is None:
                        if actually_write:
                            output_tif.save(img, photometric='minisblack')
                    else:
                        buffer.append(img)
                        if len(buffer) >= num_slices:
                            print(f"Writing {num_slices} frames from buffer...")
                            for img in buffer:
                                if actually_write:
                                    output_tif.save(img, photometric='minisblack')
                            buffer = []
            if len(buffer)>0:
                print(f"{len(buffer)} frames not written")

                    # if num_frames is not None and i > num_frames: break