#!/usr/bin/env python


## example
#1. Be on the right environment
#2. Run ometiff2bigtiff.py on the folder containing the subdirectories with all the ome.tiff files:
# python ometiff2bigtiff.py -i /groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/datasets/dataset_20200701/

import numpy as np
import matplotlib.pyplot as plt
import os
import tifffile as tiff
from natsort import natsorted
import re
import argparse


def ometiff2bigtiff(path):
    """
    List all ome.tiff in a directory and make them one bigtiff
    Somehow it gives an error for the last ome tiff, but resulting .btf is fine.

    IMPORTANT: This ometiff2big tiff removes the Z-Stack information in a recording with Z stacks! At least if the number of Z Stacks is inconsistent, which is the case for the current writer in ome.tiff. While recording the microscope saves the ome.tiff file, even if the z-stack is not finished.
    
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


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--i_path", required=True, help="path to input images")
args = vars(ap.parse_args())

main_path=(args["i_path"])

ometiff2bigtiff(main_path)


#for loop (it applies the ometiff2bigtiff function to all subdirectories in the main_path)
# for roots, dirs, files in natsorted(os.walk(main_path)):
#     print(dirs)
#     for single_dir in natsorted(dirs):
#         if 'worm' in single_dir and 'bg' not in single_dir:
#             print('the directory is:')
#             print(os.path.join(roots,single_dir)+'\n')
#             ometiff2bigtiff(os.path.join(roots,single_dir))