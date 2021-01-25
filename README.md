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



# Quick Skeleton Notebooks

(This readme is from before it was a package and needs to be updated)
### Please use the openCV Anaconda environment provided.


Install conda environment
conda env create -f openCV.yml

Skeleton.ipynb is the local version, with a lot of 'experiments' I did before finding the optimal solution.

Skeleton_cluster.ipynb is a working version that runs on cluster.

Skeleton_cluster_GPU.ipynb is a working version that runs on cluster, thought to run on GPU.


## Pipeline
At the moment the code is set up to work with datasets that are multiple ome.tiff files per recording.
In one 20min recording there can be 20 ome tiff files.

###1. Convert ome.tiff files to single bif tiff file.

Run ometiff2bigtiff.py as an array of jobs for every folder (See Cluster jobs repository). This will make one big tiff file for each folder.

Alternatively you can run:

```
conda activate openCV
python ometiff2bigtiff.py -i /groups/zimmer/Ulises/wbfm/chemotaxis_assay/2020_Only_behaviour/datasets/dataset_20200701/
```
Or you can open the Utils.ipynb notebook and run the ometiff2bigtiff function on the dataset directory (Discouraged).

####1.1 Copy all the .btf files in a separate directory, like 'btf'

###2. Run tiff2avi.py


###3. Generate binary images from the recordings
Use the python script. At the moment all recordings are substracted the same background. Code needs to be improved to allow for specific background image.

###4. Run skeletonization code on the binary images

