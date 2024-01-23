# Basic packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle

# Sklearn modules & classes
from sklearn.linear_model import Perceptron, LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn import datasets
from sklearn import metrics

#load model
filename = "/Volumes/scratch/neurobiology/zimmer/ulises/code/behavior_analysis/models/ventral_dorsal_svc_model.sav"

svc = pickle.load(open(filename, 'rb'))

#load data
main_path= "/Users/ulises.rey/local_data/test_beh_annotation/1127_w1"

spline_path = os.path.join(main_path,"skeleton_spline_K_signed_avg.csv")
spline_df = pd.read_csv(spline_path, header=None)
curvature = spline_df.iloc[:,10:90].sum(axis=1)
curvature.fillna(0, inplace=True)
curvature = pd.DataFrame(curvature, columns=['curvature'])

pca_path = os.path.join(main_path,"principal_components.csv")
pca_df = pd.read_csv(pca_path)
pca_df.fillna(0, inplace=True)

#speed
speed_path = os.path.join(main_path,"raw_worm_speed.csv")
speed_df = pd.read_csv(speed_path)

# concatenate pca_df and curvature, addining header 'curvature' to the curvature column
data_df = pd.concat([pca_df, curvature, speed_df], axis=1)

#X = data_df[['PC1','PC2','PC3', 'PC4', 'PC5', 'curvature', 'Raw Speed (mm/s)']].values
X = data_df[['PC1','PC2','PC3', 'PC4', 'PC5', 'curvature']].values
#load target

target_path = os.path.join(main_path,"simplest_turn_annotation_timeseries.csv")
y = pd.read_csv(target_path)['Annotation'].values

# scale data
sc = StandardScaler()
sc.fit(X)
X_std = sc.transform(X)

# predict
all_predict=svc.predict(X_std)

print("Accuracy score %.3f" % metrics.accuracy_score(y, all_predict))



y = np.expand_dims(y, axis=0)
all_predict=np.expand_dims(all_predict, axis=0)

#plotting

fig, axes = plt.subplots(nrows=2,  sharex=True, dpi=100)

axes[0].imshow(y, origin="upper", cmap='tab10', aspect=20*100)
axes[0].set_title('Ground truth')

axes[1].imshow(all_predict, origin="upper", cmap='tab10', aspect=20*100)
axes[1].set_xlabel('Time (frames)')
axes[1].set_title('Predicted')

for ax in axes:
    ax.set_yticks([])
plt.show()
print('end')