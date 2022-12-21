import pandas as pd
import numpy as np
from scipy.signal import hilbert, chirp
import matplotlib.pyplot as plt


# based on https://www.gaussianwaves.com/2017/04/extract-envelope-instantaneous-phase-frequency-hilbert-transform/

#This function was written by Itamar, and shared via email
def get_num_undulations_per_event(curvature_df: pd.DataFrame, event_df: pd.DataFrame, segment_K: int = 25,
                                  timeshift: int = 0):
    '''
    This function gets curvature dataframe and events dataframe and returns dataframe with the number of undulations per reversal event
    To caculate the undulations the function first extracts the undulation phase from the total oscilations of the chosen body segment
    this is done using hilberts transformation. Then the carrier phase which is the undulations is divided by 2pi to get to the number of
    full undulations. In addition hilbert's transformation cannot deal with NaN data points, so those are ignored.
    This may causes some under estimation of undulations if in the middle of undulation there was NaN.

    Parameters:
    curvature_df:pd.DataFrame
        curvature dataframe holding the curvature per body segment.
    event_df:pd.DataFrame
        events dataframe holding event start and event end in frames
    segment_K:int
        integer noting which body segment to focus on when calculating undulations
        default is 25 which is the middle segment if you have 50 segments skeleton
    timeshift:int
        integer noting what is the time shift between the event anotations and curvature data
        this is because the curvature data is saved without the full time of the recording
        this is in contrast with how the event data is saved

    '''

    ##get phase of undulations from selection body

    # get curvature of segment
    segment_K = curvature_df[segment_K].to_numpy()

    #     print("segment data length",len(segment_K))
    # deal with NaNs
    nan_K = np.isnan(segment_K)
    K_noNaN_pos = ~nan_K
    noNaN_K = segment_K[K_noNaN_pos]

    # perform hilbert transformation
    # to get the carrier phase of undulations
    hilbert_K = signal.hilbert(noNaN_K)  # form the analytical signal
    # to get the number of full undlations we had to divide to 2 pi (whole cycle)
    inst_phase = np.unwrap(np.angle(hilbert_K)) / (2 * math.pi)

    # bring back NaNs
    inst_phase_wNaN = np.empty_like(segment_K)
    inst_phase_wNaN[:] = np.nan
    inst_phase_wNaN[K_noNaN_pos] = inst_phase

    # initialize list to hold results
    undulations_phase = []

    ##iterate over events to collect undulation number
    for event in event_df.iterrows():
        # get event start and end
        curr_event_start = event[1]['start'] - timeshift
        curr_event_end = event[1]['end'] - timeshift
        # get the undulation number of the current event
        # just by substracting the phase at the end with the one at the start
        # this is because the phases rise continuously with time

        if curr_event_end > len(inst_phase_wNaN):
            print("for some reason no curvature data for these frames. Check the code and timeshift calculations!")
            current_phase_diff = np.nan
            continue

        current_phase_diff = inst_phase_wNaN[curr_event_end] - inst_phase_wNaN[curr_event_start]

        # save current undulation
        undulations_phase.append(current_phase_diff)

    return undulations_phase

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
    return

#tutorial_example()

#load dataframe with body curvature
path  = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/ZIM2165_Gcamp7b_worm7/2022-10-13_17-27_ZIM2165_worm7_Ch0-BH/2022-10-13_17-27_ZIM2165_worm7_Ch0-BHbigtiff_skeleton_spline_K.csv"
df=pd.read_csv(path)
df = df.iloc[:,5].rolling(window=20, center=True).mean()
df = df.iloc[22000:26000]

fs = 83 #600.0 #sampling frequency


x = df.values

fig, axes = plt.subplots(4)
#signal
axes[0].plot(x) #plot the "modulated" signal, in my case raw signal

z = hilbert(x) #form the analytical signal
inst_amplitude = np.abs(z) #envelope extraction
inst_phase = np.unwrap(np.angle(z))#inst phase
inst_freq = np.diff(inst_phase)/(2*np.pi)*fs #inst frequency

#axes[1].subplot(3,1,2)
#plt.plot(inst_phase)
axes[1].plot(inst_freq, color='black')
axes[1].set_title('Inst Frequency')


#Regenerate the carrier from the instantaneous phase
regenerated_carrier = np.cos(inst_phase)

axes[2].plot(inst_amplitude,'r'); #overlay the extracted envelope
axes[0].plot(inst_amplitude,'r'); #overlay the extracted envelope

axes[2].set_title('Modulated signal and extracted envelope')
axes[2].set_xlabel('n')
axes[2].set_ylabel('x(t) and |z(t)|')


#plt.subplot(3,1,3)
#plt.plot(inst_phase)
axes[3].plot(regenerated_carrier)
axes[3].set_title('Extracted carrier or TFS')
axes[3].set_xlabel('n')
axes[3].set_ylabel('cos[\omega(t)]')
plt.show()