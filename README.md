# Installation
To install this as package you should know how to install local python packages and how to handle conda environments.

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

### 1.1. Convert ome.tiff files to single bif tiff file.

Run ometiff2bigtiff function as an array of jobs for every behavioural recording (See Cluster jobs repository). This will make one big tiff file for each folder.


### 1.2. Substract background
Check the cluster_jobs files. Use stack_subtract_background.sh file which calls the imfunctions.stack_substract_background()

### 1.3. Run tiff2avi
Run tiff2avi on your background subtracted behavioural data. Avi files are needed for the DLC step of predicting head and tail position.

### 1.4. Generate binary images from the recordings
From the behavioural stacks where background has been subtracted you can run the unet network:
```
scratch/neurobiology/zimmer/ulises/code/unet-master/data/2022_04_24_worm_segmentation_all_worms_good_background/training_results/2626261_1_w_validation_1batchsize_500steps_100epochs_5patience/unet_master.hdf5
```
with the script unet_segmentation_stack.sh in cluster_jobs.

On the U-net output you can run the **binarize.sh** on cluster_jobs, to have a binary image.

If your data looks different and you need U-net, you will have to generate training data. See the unet-master package to see how.


## 2. Run the recordings on the DLC network to detect Head and Tail
If you already have a network trained, you can run it.
For ZIM01 recordings on background subtracted images this network is good:

**/scratch/neurobiology/zimmer/ulises/code/deeplabcut_projects/wbfm_noise_tail-Ulises-2022-06-13/config.yaml**

analyze videos with **bash_to_analyze_videos.sh** in dlc_utils_code.


### 2.1. Train the network, evaluate it, etc.
Use the DLC GUi or the DLC.ipynb notebook for this.
Consider Filtering.

## 3. Obtain Centerlines from the binary images and the hdf5 with Head and Tail position

At the moment this is done with the script **head_and_tail.py** which you can run from **head_and_tail.sh** in cluster_jobs/

Reformat them witht the script __reformat_skeleton_files.py__, which can be run easily with the **array_job_directories.sh** file in cluster_jobs.


## 4. Analyze data (Fourier Transform, PCA, etc.)
Use notebooks:
/code/centerline/centerline/dev/FourierTransform.ipynb
/code/centerline/centerline/dev/PCA_eigenworm.ipynb

## 5. Annotate behaviour based on PCA analysis
/code/centerline/centerline/dev/PCA_eigenworm.ipynb




# Miscellaneous

Skeleton.ipynb is the local version, with a lot of 'experiments' I did before finding the optimal solution.

Skeleton_cluster.ipynb is a working version that runs on cluster.
