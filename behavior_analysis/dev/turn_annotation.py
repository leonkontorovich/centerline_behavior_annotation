import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#README
# Much of this code is based on PCA_Figure PCA_slider from imutils/dev/sliders or imutils/dev/PCA_Figure.py

#read file
main_path = "/Volumes/scratch/neurobiology/zimmer/ulises/wbfm/20221210/data/ZIM2165_Gcamp7b_worm1/2022-12-10_16-36_ZIM2165_worm1_Ch0-BH"
df = pd.read_csv(glob.glob(os.path.join(main_path,"principal_components.csv"))[0])

df['PC3'].plot.hist(bins=100)
plt.show(block=False)


avg_win=1#167
x=df.loc[:,'PC1'].rolling(window=avg_win, center=True).mean()
y=df.loc[:,'PC2'].rolling(window=avg_win, center=True).mean()
z=df.loc[:,'PC3'].rolling(window=avg_win, center=True).mean()

# add a column in the dataframe which contains 1 if another column is higher than 0.05, -1 if lower than -0.05, and 0 if in between -0.5 and 0.5
df['turn'] = np.where(df['PC3'] > 0.05, 1, np.where(df['PC3'] < -0.05, -1, 0))

#color dictionary
color_dict = {-1: u'yellow',
              0: u'black',
              1: u'orange'}

color = df['turn'].map(color_dict)

#print(color)
# Create the figure and the line that we will manipulate
fig = plt.figure(figsize=plt.figaspect(0.5), dpi=200)

ax1 = fig.add_subplot(1, 1, 1, projection='3d')
#ax1.scatter(x, y, z, lw=0.5)
ax1.scatter(x, y, z, lw=0.5, c=df['turn'].map(color_dict), s=1)
ax1.set_xlabel('PC1')
ax1.set_ylabel('PC2')
ax1.set_zlabel('PC3')
plt.show()
