def func1(x,y):
    print (x*y)

def func2(text):
    print (text)

ap = argparse.ArgumentParser()


FUNCTION_MAP = {'func1' : func1,
                'func2' : func2}


# create the top-level parser
parser = argparse.ArgumentParser(prog='PROG')
parser.add_argument('command', choices=FUNCTION_MAP.keys(), help='choose function to run')
subparsers = parser.add_subparsers(help='sub-command help')

# create the parser for the "a" command
parser_a = subparsers.add_parser('func1', help='func1 help')
parser_a.add_argument("-x", "--x", required=True, help="number 1")
parser_a.add_argument("-y", "--y", required=True, help="number 2")


# create the parser for the "b" command
parser_b = subparsers.add_parser('func2', help='func2 help')
parser_b.add_argument("-text", "--text", required=True, help="text you want to print")


args = parser.parse_args()

func = FUNCTION_MAP[args.command]
#I don't know how to put the correct inputs inside the func()
func()