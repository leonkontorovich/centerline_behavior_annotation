# construct the argument parser and parse the arguments
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
