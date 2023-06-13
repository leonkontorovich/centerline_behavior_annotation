import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

df=pd.read_csv("/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/agar_concentration/speeds_updated_fresh_comparison.csv", delimiter=' ')
# sns.catplot(data=df, kind="bar", x='agar', y="mean_speed")
# plt.ylim([0, 0.2])
# plt.show()

sns.swarmplot(data=df, x='agar', y="median_speed", hue='very_fresh')
plt.ylim([0, 0.12])
plt.show()

two_percent_df  = df.loc[df['agar'] == 2]
sns.swarmplot(data=two_percent_df, x='very_fresh', y="median_speed")
plt.ylim([0.05, 0.1])
plt.show()


very_fresh_df  = df.loc[df['very_fresh'] == True]
print(very_fresh_df.mean())
print(very_fresh_df['median_speed'])
less_fresh_df  = df.loc[df['very_fresh'] == False]
print(less_fresh_df['median_speed'])
print(less_fresh_df.mean())