import pandas as pd
import numpy as np
from scipy.signal import hilbert, chirp
import matplotlib.pyplot as plt


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

    plt.plot(inst_amplitude, 'r');  # overlay the extracted envelope
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

#tutorial_example()
#load dataframe with body curvature
def hilbert_curvature_example(path, fs=83):

    path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm3/2022-11-27_15-59_ZIM2165_worm3_GC7b_Ch0-BH/2022-11-27_15-59_ZIM2165_worm3_GC7b_Ch0-BHbigtiff_skeleton_spline_K_signed.csv"
    df=pd.read_csv(path)
    df = df.rolling(window=83, center=True, min_periods=1).mean()
    #df = df.iloc[]
    #df = df.iloc[13500+9000:28000,:].rolling(window=25, center=True, min_periods=1).mean()
    print(df.shape)

    #fs = 83 #600.0 #sampling frequency

    x = df.values

    fig, axes = plt.subplots(4)
    #signal
    axes[0].plot(x) #plot the "modulated" signal, in my case raw signal

    z = hilbert(x, axis=0)#, axis=)#, axis=0)#form the analytical signal
    print(z.shape)
    inst_amplitude = np.abs(z) #envelope extraction
    inst_phase = np.unwrap(np.angle(z), axis=0)#inst phase
    #inst_freq = np.diff(inst_phase, axis=0)/(2*np.pi)*fs #inst frequency
    inst_freq = np.diff(inst_phase, axis=0)/(2*np.pi)*fs #inst frequency
    print(inst_freq.shape)
    #axes[1].subplot(3,1,2)
    #plt.plot(inst_phase)
    axes[1].plot(inst_freq)
    axes[1].set_title('Inst Frequency')


    #Regenerate the carrier from the instantaneous phase
    regenerated_carrier = np.cos(inst_phase)

    axes[2].plot(inst_amplitude) #overlay the extracted envelope
    axes[0].plot(inst_amplitude,'r') #overlay the extracted envelope

    axes[2].set_title('Modulated signal and extracted envelope')
    axes[2].set_xlabel('n')
    axes[2].set_ylabel('x(t) and |z(t)|')


    #plt.subplot(3,1,3)
    #plt.plot(inst_phase)
    axes[3].plot(regenerated_carrier)
    axes[3].set_title('Extracted carrier or TFS')
    axes[3].set_xlabel('n')
    axes[3].set_ylabel('cos[\omega(t)]')
    plt.show(block=False)


    fig2, axes2 = plt.subplots(4, sharex=True, sharey=True)
    axes2[0].imshow(x.T, origin="upper", cmap='seismic', extent=[0, x.shape[0], x.shape[1], 0],
                        aspect=20, vmin=-0.06, vmax=0.06)

    axes2[1].imshow(inst_freq.T, origin="upper", cmap='seismic', extent=[0, inst_freq.shape[0],
                        inst_freq.shape[1], 0], aspect=20, vmin=-1, vmax=1)
    axes2[2].imshow(inst_amplitude.T, origin="upper", cmap='viridis',
                    extent=[0, inst_amplitude.shape[0], inst_amplitude.shape[1], 0], aspect=20, vmin=0, vmax=0.05)

    axes2[3].imshow(regenerated_carrier.T, origin="upper", cmap='seismic',
                    extent=[0, regenerated_carrier.shape[0], regenerated_carrier.shape[1], 0], aspect=20, vmin=-0.06, vmax=0.06)

    titles = ['Curvature', 'Instantaneous Frequency', 'Instantaneous Amplitude', 'Extracted carrier / TFS']
    for idx, axis in enumerate(axes2):
        axis.set_title(titles[idx])

    plt.show()

def hilbert_transform_on_kymogram(path, fs):
    """

    :param path:
    :param fs:
    :return:
    """

    df = pd.read_csv(path) #Not sure if I should load the df instead
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
    return


if __name__ == '__main__':

    import argparse
    import pandas as pd
    import glob
    import os

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
    parser.add_argument('-p', '--project_path', help='path to project', required=True)
    parser.add_argument('-kp', '--kymo_path', help='filepath to kymogram', required=True)
    parser.add_argument('-fs', '--fs', help='sampling frequency', required=True)
    args = vars(parser.parse_args())
    project_path = args['project_path']
    kymo_path = args['kymo_path']
    fs = args['fs']

    df = pd.read_csv(kymo_path)

    #inst_amplitude, inst_phase, inst_freq, regenerated_carrier = hilbert_transform_on_kymogram(path, fs)
    # inst_amplitude_df = pd.DataFrame(inst_amplitude)
    # inst_phase_df = pd.DataFrame(inst_phase)
    # inst_freq_df = pd.DataFrame(inst_freq)
    # regenerated_carrier_df = pd.DataFrame(regenerated_carrier)
    # inst_amplitude_df.to_csv(os.path.join(path,"inst_amplitude.csv"))
    #and so on...

    results = hilbert_transform_on_kymogram(kymo_path, fs)
    results_names = ["inst_amplitude", "inst_phase", "inst_freq", "regenerated_carrier"]
    for i, result in enumerate(results):
        result_df = pd.Dataframe(result)
        result_df.to_csv(os.path.join(project_path, results_names[i]+".csv"))