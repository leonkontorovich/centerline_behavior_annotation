import cv2
import tifffile as tiff
import argparse

#Ulises Rey.
#it uses a cv2 WRITER and a tiff Reader
#based on a jupyternotebook on skeleton_utils.ipynb


#example:
#python /groups/zimmer/Ulises/code/skeleton/tiff2avi.py -i /groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/all_btf/2020-07-01_14-41-11_chemotaxisl_worm2-channel-0-bigtiff.btf -o /groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/all_good_avis/test.avi -fps 167 -fourcc MJPG

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--tiff_path", required=True, help="path to input tiff file")
ap.add_argument("-o", "--avi_path", required=True, help="path to output avi file")
ap.add_argument("-fourcc", "--fourcc", required=True, help="fourcc compression mode, 0 means no compression")
ap.add_argument("-fps", "--fps", required=True, help="Frames per second")
#ap.add_argument("-multi", "--multi", required=False, help="Multi ometiff")


args = vars(ap.parse_args())

tiff_path=args["tiff_path"]
avi_path=args["avi_path"]
fourcc=args["fourcc"]

if fourcc == '0':
    fourcc=0
else:
    fourcc=cv2.VideoWriter_fourcc(*args["fourcc"])

fps=int(args["fps"])
#multi=args["multi"]

#To improve: Write Multifile as option, so it can be set to True
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
	fps: num
		Number of frames per second at which the recording was acquired

    """

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

#run function
tiff2avi(tiff_path, avi_path, fourcc, fps)