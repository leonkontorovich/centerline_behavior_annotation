import argparse

def func1(x,y):
    print (x*y)

def func2(text):
    print (text)

ap = argparse.ArgumentParser()


FUNCTION_MAP = {'func1' : func1,
                'func2' : func2}


# create the top-level parser
parser = argparse.ArgumentParser(prog='PROG')
# Just add the subparser, no need to add any other argument.
# Pass the "dest" argument so that we can figure out which parser was used.
subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

# create the parser for the "a" command
parser_a = subparsers.add_parser('func1', help='func1 help')
# Keep the names here in sync with the argument names for "func1"
# also make sure the expected type is the same (int in this case)
parser_a.add_argument("-x", "--x", required=True, help="number 1", type=int)
parser_a.add_argument("-y", "--y", required=True, help="number 2", type=int)


# create the parser for the "b" command
parser_b = subparsers.add_parser('func2', help='func2 help')
parser_b.add_argument("-text", "--text", required=True, help="text you want to print")


args = parser.parse_args()

# subparser_name has either "func1" or "func2".
func = FUNCTION_MAP[args.subparser_name]
# the passed arguments can be taken into a dict like this
func_args = vars(args) #func1, x, y
# remove "subparser_name" - it's not a valid argument
del func_args['subparser_name']
# now call the function with it's arguments
func(**func_args)