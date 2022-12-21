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

path  = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221013/data/ZIM2165_Gcamp7b_worm7/2022-10-13_17-27_ZIM2165_worm7_Ch0-BH/2022-10-13_17-27_ZIM2165_worm7_Ch0-BHbigtiff_skeleton_spline_K.csv"
df=pd.read_csv(path)
df = df.iloc[22000:26000,2:90:45].rolling(window=10, center=True, min_periods=5).mean()
#df = df.iloc[]
print(df.shape)

fs = 83 #600.0 #sampling frequency


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
plt.show()