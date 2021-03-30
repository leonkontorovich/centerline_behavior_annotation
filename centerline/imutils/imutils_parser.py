import argparse
from centerline.imutils import functions as imutils

FUNCTION_MAP = {'tiff2avi' : imutils.tiff2avi,
                'ometiff2bigtiff' : imutils.ometiff2bigtiff}


# create the top-level parser
parser = argparse.ArgumentParser(prog='PROG')
# Just add the subparser, no need to add any other argument.
# Pass the "dest" argument so that we can figure out which parser was used.
subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

# create the parser for the "a" command
parser_a = subparsers.add_parser('tiff2avi', help='tiff2avi help')
# Keep the names here in sync with the argument names of the FUNCTION_MAP
parser_a.add_argument("-i", "--tiff_path", required=True, help="path to input tiff file")
parser_a.add_argument("-o", "--avi_path", required=True, help="path to output avi file")
parser_a.add_argument("-fourcc", "--fourcc", required=True, help="fourcc compression mode, 0 means no compression")
parser_a.add_argument("-fps", "--fps", required=True, help="Frames per second")

# create the parser for the "b" command
parser_b = subparsers.add_parser('ometiff2bigtiff', help='ometiff2bigtiff help')
parser_b.add_argument("-path", "--path", required=True, help="path to the input folder")


# create the parser for the "c" command
parser_c = subparsers.add_parser('ometiff2bigtiffZ', help='ometiff2bigtiffZ help')
parser_c.add_argument("-path", "--path", required=True, help="path to the input folder")
parser_c.add_argument("-output_dir", "--output_dir", required=False, help="path to the output folder")
parser_c.add_argument("-actually_write", "--actually_write", required=False, help="True if you actually want to write")
parser_c.add_argument("-num_slices", "--num_slices", required=False, help="Number of slices your Z-Stack should have")

#create the parser for another function


#parse args
args = parser.parse_args()

# subparser_name has either "tiff2avif" or "ometiff2bigtiff".
func = FUNCTION_MAP[args.subparser_name]
# the passed arguments can be taken into a dict like this
func_args = vars(args)
# remove "subparser_name" - it's not a valid argument
del func_args['subparser_name']
# now call the function with its arguments
func(**func_args)