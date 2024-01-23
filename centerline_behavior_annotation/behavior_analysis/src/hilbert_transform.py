import sys

import pandas as pd
import numpy as np
from scipy.signal import hilbert, chirp
import matplotlib.pyplot as plt
import argparse
import pandas as pd
import glob
import os


# based on https://www.gaussianwaves.com/2017/04/extract-envelope-instantaneous-phase-frequency-hilbert-transform/

def tutorial_example():
    import numpy as np
    from scipy.signal import hilbert, chirp
    import matplotlib.pyplot as plt

    fs = 600.0  # sampling frequency
    duration = 1.0  # duration of the signal
    t = np.arange(int(fs * duration)) / fs  # time base

    a_t = 1.0 + 0.7 * np.sin(2.0 * np.pi * 3.0 * t)  # information signal
    c_t = chirp(t, 20.0, t[-1], 80)  # chirp carrier
    x = a_t * c_t  # modulated signal

    plt.subplot(2, 1, 1)
    plt.plot(x)  # plot the modulated signal

    z = hilbert(x)  # form the analytical signal
    inst_amplitude = np.abs(z)  # envelope extraction
    inst_phase = np.unwrap(np.angle(z))  # inst phase
    inst_freq = np.diff(inst_phase) / (2 * np.pi) * fs  # inst frequency

    # Regenerate the carrier from the instantaneous phase
    regenerated_carrier = np.cos(inst_phase)

    #plt.plot(inst_amplitude, 'r');  # overlay the extracted envelope
    plt.title('Modulated signal and extracted envelope')
    plt.xlabel('n')
    plt.ylabel('x(t) and |z(t)|')
    plt.subplot(2, 1, 2)
    plt.plot(regenerated_carrier)
    plt.title('Extracted carrier or TFS')
    plt.xlabel('n')
    plt.ylabel('cos[\omega(t)]')
    plt.show()
    print('done')

    plt.plot(inst_freq)
    plt.show()
    return

def hilbert_transform_on_kymogram(df, fs):
    """

    :param path:
    :param fs:
    :return:
    """

    #df = pd.read_csv(path) #Not sure if I should load the df instead
    x = df.values
    z = hilbert(x, axis=0)

    # envelope extraction
    inst_amplitude = np.abs(z)
    inst_phase = np.unwrap(np.angle(z), axis=0)

    # inst frequency
    inst_freq = np.diff(inst_phase, axis=0)/(2*np.pi)*fs

    #Regenerate the carrier from the instantaneous phase
    regenerated_carrier = np.cos(inst_phase)

    return inst_amplitude, inst_phase, inst_freq, regenerated_carrier


def hilbert_transform_on_kymograms_wrapper():
    #at the moment not needed, using the argparse
    return

# tutorial_example()
# #inst_amplitude, inst_phase, inst_freq, regenerated_carrier = hilbert_curvature_example(fs=83)
# # fig1, axes1 = hilbert_curvature_one_segment_example(10,1)
# # plt.show(block=False)
# # fig2, axes2 = hilbert_curvature_one_segment_example(50,1)
# # plt.show(block=False)
# #hilbert_curvature_example(fs=83)
#
# print('debug')


def main(arg_list):
    print("arg_list:", arg_list)

    # specify files
    # parser = argparse.ArgumentParser(description='Description of your program')
    # parser.add_argument('-kp', '--kymo_path', help='filepath to kymogram', required=True)
    # parser.add_argument('-fs', '--fs', help='sampling frequency', required=True)
    #
    # args = vars(parser.parse_args())
    # kymo_filepath = args['kymo_path']
    # fs = args['fs']

    # or project only
    # parser = argparse.ArgumentParser(description='Description of your program')
    # parser.add_argument('-p', '--project_path', help='path to project', required=True)
    # args = vars(parser.parse_args())
    # project_path = args['project_path']
    # kymo_filepath = glob.glob(os.path.join(project_path, "*K*signed.csv"))[0]
    # fs =  # read from config yaml file? or from parser

    #or both
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-i', '--project_path', help='path to project', required=True)
    parser.add_argument('-kp', '--kymo_path', help='filepath to kymogram', required=True)
    parser.add_argument('-fs', '--fs', type=float, help='sampling frequency', required=True)
    parser.add_argument('-w', '--window', type=int, help='averaging window', required=True)
    args = vars(parser.parse_args(arg_list))
    project_path = args['project_path']
    kymo_path = args['kymo_path']
    fs = args['fs']
    window = args["window"]

    # project_path = "/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH"
    # kymo_path = "/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BHbigtiff_skeleton_spline_K_signed.csv"
    # fs = 83

    df = pd.read_csv(kymo_path, index_col=None, header=None)
    # This should be done outside this function!
    df = df.rolling(window=window, center=True, min_periods=1).mean()
    print("You are using a window to average, in the future you want to avoid this")

    # do the hilbert transform
    results = hilbert_transform_on_kymogram(df, fs)

    results_names = ["inst_amplitude", "inst_phase", "inst_freq", "regenerated_carrier"]
    for i, result in enumerate(results):
        result_df = pd.DataFrame(result)
        result_df.to_csv(os.path.join(project_path, "hilbert_"+results_names[i]+".csv"), float_format='%.5f', header=None, index=None)
    #
    print('Script Finished. If the files are empty it is probably because the Kymogram contains NaNs')


if __name__ == '__main__':

    print("Shell commands passed:", sys.argv)
    main(sys.argv[1:])  # exclude the script name from the args when called from shell
