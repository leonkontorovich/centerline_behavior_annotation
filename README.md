# Installation
To install this as package you should check
https://bitbucket.vbc.ac.at/projects/ZL/repos/protocols/browse/Installing_personal_Python_packages.md

Shortly:
1. Open Terminal and activate your environment (example your_env)
	```
	conda activate your_env
	```
2. Install it with a pip command (pointing to the directory where you cloned it)
	```
	pip install /code/centerline/
	```
	or better:
	cd to the directory where you cloned the directory
	```
	cd ../code/centerline/
	```
	And then pip install the local directory
	```
	pip install .
	```
	
	This would be wrong:
	```
	pip install centerline
	```
	Because it will install another centerline package that someone has uploaded to pip.







# Pipeline
1. Process the data to have only one file (.btf and .avi), and also binary images.
2. Run the recordings on the DLC network to detect Head and Tail
3. Obtain Centerlines
4. Analyze data (Fourier Transform, PCA, etc.)
5. Annotate behaviour based on PCA analysis

## Preparing the Data

At the moment the code is set up to work with behavioural datasets that are multiple ome.tiff files per recording.
In one 20min recording there can be 20 ome tiff files.

###1.1. Convert ome.tiff files to single bif tiff file.

Run ometiff2bigtiff function as an array of jobs for every behavioural recording (See Cluster jobs repository). This will make one big tiff file for each folder.

####1.1.2 Copy all the .btf files in a separate directory, like 'btf'

###1.2. Run tiff2avi

Run tiff2avi function as an array of jobs for every behavioural recording

###1.3. Generate binary images from the recordings
Use the python script. At the moment all recordings are substracted the same background. Code needs to be improved to allow for specific background image.

## 2. Run the recordings on the DLC network to detect Head and Tail

### 2.1. Train the network, evaluate it, etc.
Use the DLC.ipynb notebook for this.
Consider Filtering.

##3. Obtain Centerlines from the binary images and the hdf5 with Head and Tail position

##4. Analyze data (Fourier Transform, PCA, etc.)
Use notebooks:
/code/centerline/centerline/dev/FourierTransform.ipynb
/code/centerline/centerline/dev/PCA_eigenworm.ipynb

## 5. Annotate behaviour based on PCA analysis
/code/centerline/centerline/dev/PCA_eigenworm.ipynb




# Miscellaneous

Skeleton.ipynb is the local version, with a lot of 'experiments' I did before finding the optimal solution.

Skeleton_cluster.ipynb is a working version that runs on cluster.
