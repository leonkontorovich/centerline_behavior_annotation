import cv2
import tifffile as tiff
import argparse

def tiff2avi(tiff_path, avi_path, fourcc, fps):
    """
    Convert tiff file into avi file with the specified fourcc codec and fps
    The isColor parameter of the writer is by default set to False.

    Parameters:
    -----------
    tiff_path: str,
        Path to the tiff file
    avi_path: str
        Path to the output file
    fourcc: fourcc code
        0 means no coompression, other codecs will have some compression
        To learn more: https://www.fourcc.org/
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
        fourcc=cv2.VideoWriter_fourcc(fourcc)
    
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