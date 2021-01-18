#after: https://stackoverflow.com/questions/27529610/call-function-based-on-argparse
import argparse
from centerline.imutils import functions as imutils

# def tiff2avi():
# 	print ('Running tiff2avi function')

# def ometiff2bigtiff():
# 	print ('Running ometiff2bigtiff function')


ap = argparse.ArgumentParser()


FUNCTION_MAP = {'tiff2avi' : imutils.tiff2avi,
                'ometiff2bigtiff' : imutils.ometiff2bigtiff }

ap.add_argument('command', choices=FUNCTION_MAP.keys())

args = ap.parse_args()

func = FUNCTION_MAP[args.command]
func()


# # construct the argument parser and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--tiff_path", required=True, help="path to input tiff file")
# ap.add_argument("-o", "--avi_path", required=True, help="path to output avi file")
# ap.add_argument("-fourcc", "--fourcc", required=True, help="fourcc compression mode, 0 means no compression")
# ap.add_argument("-fps", "--fps", required=True, help="Frames per second")
# #ap.add_argument("-multi", "--multi", required=False, help="Multi ometiff")


# args = vars(ap.parse_args())

# tiff_path=args["tiff_path"]
# avi_path=args["avi_path"]
# fourcc=args["fourcc"]