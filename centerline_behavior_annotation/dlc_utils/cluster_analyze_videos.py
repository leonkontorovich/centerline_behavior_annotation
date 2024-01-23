import argparse
import os
import sys

os.environ["DLClight"]="True"
import deeplabcut


def main(arg_list):
    ap = argparse.ArgumentParser()
    ap.add_argument("-path_config_file", "--path_config_file", required=True, help="path to config file")
    ap.add_argument("-videofile_path", "--videofile_path", required=True, help="path to the videofile")
    args = vars(ap.parse_args(arg_list))

    print("These are the arguments:")
    print(args)
    print("\n")
    path_config_file = args['path_config_file']
    print(path_config_file)

    #don't edit these:
    #videos dont need to be on the config file: https://gitter.im/DeepLabCut/community?at=5e8f90a85d148a0460f7664a
    VideoType = 'avi'
    videofile_path = args['videofile_path']

    print(videofile_path)

    #although this code on the jupyternotebook works, i had an error while using the .py file. It went away with gputouse=None (although I was in a GPU env)
    deeplabcut.analyze_videos(path_config_file, videofile_path, videotype=VideoType, gputouse=None)


if __name__ == "__main__":
    main(sys.argv[1:])
