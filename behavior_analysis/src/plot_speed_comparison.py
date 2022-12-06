import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

df=pd.read_csv("/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/agar_concentration/speeds.csv", delimiter=' ')
sns.catplot(data=df, kind="bar", x='agar', y="mean_speed")
plt.ylim([0, 0.2])
plt.show()

sns.swarmplot(data=df, x='agar', y="mean_speed")
plt.ylim([0, 0.2])
plt.show()
