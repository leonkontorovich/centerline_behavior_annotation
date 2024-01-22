#import pckgs
import cv2
import tifffile as tiff
import numpy as np
import matplotlib.pyplot as plt
import argparse
from centerline.src.make_binary import make_binary


ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input_filename", required=True, help="path to input file")
ap.add_argument("-bg", "--background_filename", required=True, help="path to the background")
#ap.add_argument("-o", "--output_filename", required=True, help="path to output file")



args = vars(ap.parse_args())

input_filename=args['input_filename']
bg_img_filename= args['background_filename']
output_filename=args['input_filename'][:-11]+'binary.tiff'
#args['output_filename']

print('\n')
print('input:')
print(input_filename)
print('\n')
print('bg:')
print(bg_img_filename)
print('\n')
print('output:')
print(output_filename)

make_binary(input_filename, bg_img_filename, output_filename)               