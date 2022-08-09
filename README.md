# Read Me
--------
## Purpose of the package
Analyze the curvature of the worm centerline.

### Pipeline steps
1. Run make_PCA.py
It will generate a PCA model of your data
2. Run run_PCA_model_on_splines.py
Using the PCA model and the spline_K.csv files, it will generate two csv files: 1 with the principal components, another one with the behavioural annotation.


Other:
To create a PCA model and run it individually per worm, there is the script annotate_behaviour_per_worm_script.py, but soon will be merged with make_PCA.py

To concatenate different spline_K.csv files to have a PCA based on several worms, use the function **concatenate_dataframes()**
