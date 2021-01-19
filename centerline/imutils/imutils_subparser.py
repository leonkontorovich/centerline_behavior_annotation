#after: https://stackoverflow.com/questions/27529610/call-function-based-on-argparse
import argparse
from centerline.centerline.imutils import functions as imutils

ap = argparse.ArgumentParser()


FUNCTION_MAP = {'tiff2avi' : imutils.tiff2avi,
                'ometiff2bigtiff' : imutils.ometiff2bigtiff }

#parser.add_argument('command', choices=FUNCTION_MAP.keys())

#args = ap.parse_args()



# create the top-level parser
parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('command', choices=FUNCTION_MAP.keys(), help='choose function to run')
subparsers = parser.add_subparsers(help='sub-command help')

# create the parser for the "a" command
parser_a = subparsers.add_parser('tiff2avi', help='tiff2avi help')#could it be FUNCTION_MAX.key() ?
parser_a.add_argument("-i", "--tiff_path", required=True, help="path to input tiff file")
parser_a.add_argument("-o", "--avi_path", required=True, help="path to output avi file")
parser_a.add_argument("-fourcc", "--fourcc", required=True, help="fourcc compression mode, 0 means no compression")
parser_a.add_argument("-fps", "--fps", required=True, help="Frames per second")
#ap.add_argument("-multi", "--multi", required=False, help="Multi ometiff")


# create the parser for the "b" command
parser_b = subparsers.add_parser('ometiff2bigtiff', help='ometiff2bigtiff help')
parser_b.add_argument('--path', help='path to input directory witht he ome.tiff files')


args = parser.parse_args()

func = FUNCTION_MAP[args.command]
func()
