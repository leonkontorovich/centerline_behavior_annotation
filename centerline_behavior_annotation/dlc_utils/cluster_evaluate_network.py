import argparse
import os
os.environ["DLClight"]="True"
import deeplabcut

ap = argparse.ArgumentParser()
ap.add_argument("-path_config_file", "--path_config_file", required=True, help="path to config file")
args = vars(ap.parse_args())

print(args)
path_config_file = args['path_config_file']
print(path_config_file)

#run the code
deeplabcut.evaluate_network(path_config_file, Shuffles=[1], plotting=True)