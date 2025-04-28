def main(arg_list=None):
    parser = argparse.ArgumentParser(description='Process input data with tracking algorithm')
    parser.add_argument('--input_data1', type=str, required=True, help='Path to input data file 1')
    parser.add_argument('--input_data2', type=str, required=True, help='Path to input data file 2')
    parser.add_argument('--param1', type=str, required=True, help='First parameter name')
    parser.add_argument('--param2', type=str, required=True, help='Second parameter name')
    parser.add_argument('--param3', type=int, default=20, help='Third parameter value (default: 20)')
    parser.add_argument('--param4', type=float, default=60, help='Fourth parameter value (default: 60)')
    parser.add_argument('--output_data', type=str, required=True, help='Path to output data file')
    args = parser.parse_args(arg_list)

if __name__ == '__main__':
    main(sys.argv[1:])  # exclude the script name from the args when called from shell