# construct the argument parser and parse the arguments
import argparse

ap = argparse.ArgumentParser()
ap.add_argument("-i", "--i_path", required=True, help="path to input images")
args = vars(ap.parse_args())

i_path=(args["i_path"])

ometiff2bigtiff(i_path)