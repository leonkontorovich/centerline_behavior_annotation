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