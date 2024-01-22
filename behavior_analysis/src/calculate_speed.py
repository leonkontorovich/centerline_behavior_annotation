import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
def calculate_speed(x,y):
    """Calculate the speed based on its x and y coordinates."""
    speed = np.sqrt(np.gradient(x) ** 2 + np.gradient(y) ** 2)
    return speed



path = "/Volumes/scratch/neurobiology/zimmer/active_sensing/zim06/recordings_to_analyze/josefine_rescue/20230220/data/worm5_2/head_coords_mm.csv"
avg_win = 10

df = pd.read_csv(path)


x,y = df['x'].rolling(avg_win).mean(), df['y'].rolling(avg_win).mean()

speed = calculate_speed(x,y)
plt.plot(speed)
plt.show()
