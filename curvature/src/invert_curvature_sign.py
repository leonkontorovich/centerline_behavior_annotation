# The scripts here aim to invert the sign of some spline_K
# recordings so that Ventral and Dorsal Curvatures have the same sign across worms

import pandas as pd
import yaml

def invert_df(input_path, output_path):
    """
    Invert the sign of a dataframe from the input_path and save it in the output_path
    Works when the dataframe does not have header nor index.
    Not clear it would work if the df ahas actually headers or index.
    
    :param input_path: 
    :param output_path: 
    :return: 
    """
    df = pd.read_csv(input_path, index_col=None, header=None)
    df = - df
    df.to_csv(output_path, header=None, index=None)

    return df

def invert_df_based_on_ventral(input_path, output_path, config_yaml_path):
    """
    Flip the sign of the spline_K file if vetral is on the left side
    :param input_path:
    :param output_path:
    :param config_yaml_path:
    :return:
    """

    with open(config_yaml_path, "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        ventral = data['ventral']

        if ventral == 'left':
            print('ventral is on the left side of the image, changing signs')
            invert_df(input_path, output_path)

        else:
            if ventral == 'right':
                print('ventral is on the right side of the image, keeping signs')
                df = pd.read_csv(input_path, index_col=None, header=None)
                df.to_csv(output_path, header=None, index=None)
            else:
                raise AttributeError(f"ventral should be either 'left' or 'right', you have: {ventral}")


    return None



if __name__ == "__main__":


    # # INVERT SIGN with all inputs
    # import argparse
    # parser = argparse.ArgumentParser(description='Description of your program')
    # parser.add_argument('-i', '--i_path', type=str, help='input path', required=True)
    # parser.add_argument('-o', '--o_path', type=str, help='output path', required=True)
    # parser.add_argument('-c', '--config_yaml', type=str, help='path to the config yaml file', required=True)
    #
    # args = vars(parser.parse_args())
    # input_path = args['i_path']
    # output_path = args['o_path']
    # config_yaml_path = args['config_yaml']
    #
    # invert_df_based_on_ventral(input_path, output_path, config_yaml_path)

    # Invert sign with folder name PREFERABLY with DATASET FOLDER (NOT BH folder)
    import argparse
    import os
    import glob
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--input_path', help='folder of wbfm dataset', required=True)

    args = vars(parser.parse_args())
    project = args['input_path']

    print(project)

    input_path = glob.glob(os.path.join(project, "*/skeleton_spline_K.csv"))[0]
    output_path = os.path.splitext(input_path)[0]+"_signed.csv"
    config_yaml_path = glob.glob(os.path.join(project, "*config.yaml"))[0]

    invert_df_based_on_ventral(input_path, output_path, config_yaml_path)
