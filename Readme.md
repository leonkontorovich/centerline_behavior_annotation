# Quick Skeleton Notebooks - TEST
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

