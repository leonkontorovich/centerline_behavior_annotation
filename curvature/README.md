# Read Me
--------
## Purpose of the package
Analyze the curvature of the worm centerline.

### Standarize curvature of worms
The code in centerline package seems to produce consistent sign of the Curvature as a function of the curvature.
If the anterior part of the worm is up, then a c curvature will be positive. and a ↄ curvature will be negative.
If the anterior part of the worm is to the left, then a u curvature will be positive and a n curvature will be negative.

However, depending on where the vulva is on each recording, a positive curvature could mean ventral or dorsal. To standarize this and make that Red is always Ventral each recording has to be manually annotated the location of the vulva. This information should be stored in the config.yaml file.


### Create a PCA model
1. Run make_PCA.py

It will generate a PCA model of your data. You can run it locally. Modify the part after the if __name__ = main to decide from which data to generate the PCA model, and where to save the model. It will also save the PCs as a .csv file.

If you need to merge data check below in Utils section.

2. Run annotate_behaviour.py

Using the PCA model and the folder where skeleton_spline_K.csv files are (BH folders), it will generate two csv files: 
* One with the principal components
* Another one with the behavioural annotation.


#### Utils:
1. To concatenate different spline_K.csv files to have a PCA based on several worms, use the function **concatenate_dataframes()**, which can be run with the /scripts/concatenate_dataframes_wrappers.py

2. To visualize the ethogram together with the kymogram use the ethogram_figure().

3. (Not recommended) To create a PCA model and run it individually per worm, there is the script scripts/run_PCA_and_annotate_behaviour_per_worm.py

4. Other complimentary tools can be found in dev/PCA_eigenworm.ipynb notebook.
