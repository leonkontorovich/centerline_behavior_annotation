import os
import argparse

def make_beh_ann2(beh_ann2_path, project_folder, output_file):
    with open(beh_ann2_path, 'r') as f:
        lines = f.readlines()

    offset = 0
    while offset < len(lines):
            start_i = offset + 2400 - 1
            end_i = offset + 2640

            for i in range(start_i, end_i):
                if i < len(lines):
                     parts = lines[i].strip().split(',') # Splitting line by comma
                     if len(parts) > 1:                  # Checking if there's at least two columns
                          parts[1] = '3'                  # Modifying the B column
                     lines[i] = ','.join(parts) + '\n'   # Joining parts back together
            
            offset += 2560

    # Setting output filename based on the original filename but in the provided project folder
    output_path = output_file

    with open(output_path, 'w') as f:
        f.writelines(lines)

    print(f"Modified CSV saved at: {output_path}")

def main(arg_list=None):

    parser = argparse.ArgumentParser(description='Modify behavior annotation CSV file')
    parser.add_argument('--input_path', help='Input CSV file path', required=True)
    parser.add_argument('--input_file', help='Input CSV file path', required=True)
    parser.add_argument('--output_file', help='Input CSV file path', required=True)

    args = parser.parse_args(arg_list)

    input_file = args.input_file
    output_file = args.output_file

    main_folder = args.input_path

    project_folder = main_folder

    beh_ann2_path = input_file

    make_beh_ann2(beh_ann2_path, project_folder, output_file)

if __name__ == '__main__':

    main(sys.argv[1:])
