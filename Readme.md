# Quick Skeleton Notebooks
### Please use the openCV Anaconda environment provided.

Install conda environment
conda env create -f openCV.yml

Skeleton.ipynb is the local version, with a lot of 'experiments' I did before finding the optimal solution.

Skeleton_cluster.ipynb is a working version that runs on cluster.


Skeleton_cluster_GPU.ipynb is a working version that runs on cluster, thought to run on GPU.


## Pipeline
At the moment the code is set up to work with datasets that are multiple ome.tiff files per recording.
In one 20min recording there can be 20 ome tiff files.

1. Convert ome.tiff files to single bif tiff file.
Open the Utils.ipynb notebook and run the ometiff2bigtiff function on the dataset diretory.

2. Run Fiji macro to generate .avi files from bigtiff files.
Since we didnt manage to generate .avi files in python because of codecs and what not, I decided to use Fiji.
I wrote a little macro to do it: "save_bigtiff2avi.ijm"

Run it in the cluster, ideally create one session (<80GB) per bigtiff file because it is a slow process.


```
source_dir = getDirectory("Source Directory");
 
list=getFileList(source_dir);

setBatchMode(true);

for (i=0; i<list.length; i++) {
	
	run("Bio-Formats", "color_mode=Default rois_import=[ROI manager] view=Hyperstack stack_order=XYCZT use_virtual_stack open="+source_dir+list[i]);

	print(source_dir+list[i]);

	run("AVI... ", "compression=JPEG frame=167  save="+source_dir+list[i]+".avi");
	
	run("Close All");
}
```

