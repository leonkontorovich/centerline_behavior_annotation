# After this:
# https://vitalflux.com/classification-model-svm-classifier-python-example/

# Basic packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

import pickle

# Sklearn modules & classes
from sklearn.linear_model import Perceptron, LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn import datasets
from sklearn import metrics

def classifier_example():
    # Load the data set; In this example, the breast cancer dataset is loaded.

    bc = datasets.load_breast_cancer()
    X = bc.data
    y = bc.target

    # Create training and test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1, stratify=y)

    sc = StandardScaler()
    sc.fit(X_train)
    X_train_std = sc.transform(X_train)
    X_test_std = sc.transform(X_test)

    # Instantiate the Support Vector Classifier (SVC)
    svc = SVC(C=1.0, random_state=1, kernel='linear')

    # Fit the model
    svc.fit(X_train_std, y_train)

    # Make the predictions
    y_predict = svc.predict(X_test_std)

    # Measure the performance
    print("Accuracy score %.3f" % metrics.accuracy_score(y_test, y_predict))

    return None


#load data

main_path = "/Users/ulises.rey/local_data/test_beh_annotation/1130_w1"

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

X = data_df[['PC1','PC2','PC3', 'PC4', 'PC5', 'curvature']].values
#X = data_df[['PC1','PC2','PC3', 'PC4', 'PC5', 'curvature']].values
#load target
target_path = os.path.join(main_path,"simplest_turn_annotation_timeseries.csv")
y = pd.read_csv(target_path)['Annotation'].values


print(X.shape, "is the shape of the data")
print(y.shape, "is the shape of the target")
# Create training and test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1, stratify=y)

sc = StandardScaler()
sc.fit(X_train)
X_train_std = sc.transform(X_train)
X_test_std = sc.transform(X_test)

# Instantiate the Support Vector Classifier (SVC)
svc = SVC(C=1.0, random_state=1, kernel='rbf')

# Fit the model
svc.fit(X_train_std, y_train)

#save the model
filename = '../models/ventral_dorsal_svc_model.sav'
pickle.dump(svc, open(filename, 'wb'))

# Make the predictions
y_predict = svc.predict(X_test_std)

#compare y_test and y_predict with sklearn functions
print("Accuracy score %.3f" % metrics.accuracy_score(y_test, y_predict))
print(y_test)
print(y_predict)

all_predict=svc.predict(sc.transform(X))


#plot to see the results for the whole dataset (including training data which is not really fair)
# plt.plot(all_predict)
# plt.plot(y, alpha=.5)
# plt.show()

#pre processing
y = np.expand_dims(y, axis=0)
all_predict=np.expand_dims(all_predict, axis=0)

#plotting
# norm = mpl.colors.Normalize(vmin=-0.00005, vmax=0.00005)
# cmap = cm.get_cmap('tab10')
# forward_color = cmap(norm(-1))
# reversal_color = cmap(norm(1))
# quiescence_color = cmap(norm(0))

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