# Read Me
--------
## Purpose of the package
Analyze the curvature of the worm centerline.

### Standarize curvature of worms
The code in centerline package seems to produce consistent sign of the Curvature as a function of the curvature.
If the anterior part of the worm is up, then a c curvature will be positive. and a ↄ curvature will be negative.
If the anterior part of the worm is to the left, then a u curvature will be positive and a n curvature will be negative.

However, depending on where the vulva is on each recording, a positive curvature could mean ventral or dorsal. To standarize this and make that Red is always Ventral each recording has to be manually annotated the location of the vulva. This information should be stored in the config.yaml file.

### Automatic Behavior Annotations
Based on the output of the PCA model, behaviors are annotated automatically and is stored in the behavior folder in beh_annotation.csv (REV, FWD) and turns_annotation.csv (VENTRAL, DORSAL TURNS). The behavior is encoded with numbers -1, 0 and 1.


**REV/FWD**

1.......... REV

-1......... FWD

0.......... NaN


**TURNS**

1.......... VENTRAL

-1......... DORSAL

0.......... no turn/NaN


### Use a Wrapper to create a PCA model ###
The wrapper does the following:
https://github.com/Zimmer-lab/centerline_behavior_annotation/blob/main/centerline_behavior_annotation/curvature/scripts/make_PC_model_wrapper.py

- finds all the curvature files of all projects inside a root folder

- concatenates them to a huge curvature dataframe

- uses predefined segments to focus on the relevant body segments (for wbfm its 30-80)

- makes a PC model based on all that data and saves it

- reports:

-- how much variance does the model explains (especially PC1 and 2)

-- for all provided curvature files: gives scatter plots of PC1 versus PC2, showing the circle of undulations (as quality control)

-- a histogram of the cross product values from all data, to help you chose a threshold for reversal annotation

-- tries to guess (based on what happens more) the directionality of the model, whether cross product > 0 or < 0 is reversal.

### Manually Create a PCA model
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
