import pandas as pd
import numpy as np
from scipy.signal import hilbert, chirp
import matplotlib.pyplot as plt

def hilbert_curvature_example(df , fs=83):

    print(df.shape)

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
                    extent=[0, regenerated_carrier.shape[0], regenerated_carrier.shape[1], 0], aspect=20, vmin=-1, vmax=1)
    axes2[3].set_xlabel('Time (frames)')

    titles = ['Curvature', 'Instantaneous Frequency', 'Instantaneous Amplitude', 'Extracted carrier / TFS']
    for idx, axis in enumerate(axes2):
        axis.set_title(titles[idx])
        axis.set_ylabel('Segment')

    plt.show()

    return inst_amplitude, inst_phase, inst_freq, regenerated_carrier

def hilbert_curvature_one_segment_example(df, segment, fs=83):
    """

    :param segment:
    :param fs:
    :return:
    """
    print(df.shape)

    x = df.values

    z = hilbert(x, axis=0)  # , axis=)#, axis=0)#form the analytical signal
    print(z.shape)
    inst_amplitude = np.abs(z)  # envelope extraction
    inst_phase = np.unwrap(np.angle(z), axis=0)  # inst phase
    # inst_freq = np.diff(inst_phase, axis=0)/(2*np.pi)*fs #inst frequency
    inst_freq = np.diff(inst_phase, axis=0) / (2 * np.pi) * fs  # inst frequency
    print(inst_freq.shape)

    # Regenerate the carrier from the instantaneous phase
    regenerated_carrier = np.cos(inst_phase)

    fig, axes = plt.subplots(4, sharex=True)
    axes[0].plot(x[:,segment])
    axes[0].plot(inst_amplitude[:, segment], 'r')  # overlay the extracted envelope
    axes[0].axhline(y=0, color='k', linestyle='--')

    axes[1].plot(inst_freq[:,segment])
    axes[1].axhline(y=0, color='r', linestyle='--')

    axes[2].plot(inst_amplitude[:,segment])

    axes[3].plot(regenerated_carrier[:,segment])

    titles = ['Curvature', 'Instantaneous Frequency', 'Instantaneous Amplitude', 'Extracted carrier / TFS']
    for idx, axis in enumerate(axes):
        axis.set_title(titles[idx])

    #set figure title
    fig.suptitle('Segment {}'.format(segment))

    return fig, axes


# path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BHbigtiff_skeleton_spline_K_signed_avg.csv"
# df = pd.read_csv(path, index_col=None, header=None)
path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221127/data/ZIM2165_Gcamp7b_worm1/2022-11-27_15-14_ZIM2165_worm1_GC7b_Ch0-BH/skeleton_spline_K_signed_avg.csv"
df = pd.read_csv(path, index_col=None, header=None)
segment = 10
hilbert_curvature_one_segment_example(df, segment, fs=83)
plt.show()
