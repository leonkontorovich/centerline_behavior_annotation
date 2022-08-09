# Read Me
--------
## Purpose of the package
Analyze the effects on head movements into the sensory input of C. elegans during a foraging task.

## How to
Every project should be organized as follows:

    recording_worm1
    └───RFP_channel
	│   │   RFP_recording.btf
	│   │     ...
	│
	└───GCamp_channel
	│   │   GCamp_recording.btf
	│   │   ...
	│	
	└───Behaviour_channel
	│   │   behaviour_recording.btf
	│   │   ...
	│	
	└───stage_position.txt
	└───reference_image_before.ome.tiff
	└───reference_image_after.ome.tiff
	└───bead_position_zim06.csv
	└───bead_position_before.csv
	└───bead_position_after.csv

(You can use the wbfm processing package to help you organize the data)

### Content
#### Gcamp, RFP and Behaviour files
These are generated as multiple ome.tiff files and should be converted to a single btf.

#### reference images
There are two images, recorded from the BH setups before and after the experiment.
The one before is just as control. From the one after the coordinates of the beads AND the food ring or any other structure, will be extracted.
They might look like this:
![image](https://user-images.githubusercontent.com/64480193/152176471-d908b968-7d58-424d-9a16-820dd44b6068.png)


#### Bead position files
There are three files:
1. bead_position_zim06.csv: from the poistions recorded from the ZIM06 stage controler (acquired at the end of the recording)
2. bead_position_before.csv: from the positions recorded from the reference_image_before.ome.tiff (acquired on a BH setup before the recording)
3. bead_position_after.csv: from the positions recorded from the reference_image_after.ome.tiff (acquired on a BH setup after the recording)

Coordinates 2 and 3 (only one of them is actually needed) can be saved to a csv file at the same time one saves the food border with Napari (see /src/annotate_food_with_napari.ipynb). (They could also be saved using Fiji)

The bead position coordinates should be stored in files with these exact names, and with this format:

Example of bead_position_zim06.csv:
```
bead#,x,y
bead1,6.52,-2.93
bead2,4.4,-3.88
bead3,-7.65,-2.3
bead4,-17.96,-14.27
bead5,-2.64,-29.28
bead6,7.88,-16.23
```
In principle 3 beads are enough, but 5 or more is better.

Example of bead_position_after.csv:
```
bead#,x,y
bead1,540,1542
bead2,630,1503
bead3,1155,1542
bead4,1581,1002
bead5,885,381
bead6,462,966
```

### Get Polygon coordinates with Napari
Use the notebook in src/annotate_food_with_napari.ipynb 
And follow the instructions there.

### Curate Coordiantes files
#### Change all column labels to x y lower case.
The stage position has to change its labels from 'X' and 'Y' to 'x' and 'y' for the code to work.
Run decapitalize_xy_labels() in invert_coordiantes.py for all the stage position files. Use the preprocessing_decapitalize_xy_labels.sh file in /bash_scripts/ subolder of this package.

#### Invert coordinates sign
In order to make everything easier it is good to invert the sign of the coordinates in the stage position. In order not to mess with the transformation the sign of the bead_position_zim06.csv will also be inverted. Basically any coordinates that was annotated from the stage position.
Run again the preprocessing_decapitalize_xy_labels.sh modifying the input files accordingly.

### Apply transformation
Modify the transformation.sh file based on the number of recordings and run
```bash
cd ~/code/epifluorescence_calcium_imaging/epifluorescence_calcium_imaging/bash_scripts
sbatch transformation.sh
```

### Calculate distance
After applying the transformation, you want calculate the distance between the worm coordinates (stage position, nose position, or other) to the ring of food.
For this use the calculate_distance_test.py (under construction)

#### Absolute coordinates of a body part (e.g. nose)
To get the absolute coordinates of a body part annotated with DeepLabcut use these functions: https://github.com/ulisesrey/imutils/blob/master/imutils/src/bodyparts_coordinates.py

### Measure Fluorescent Levels
This part is organize with different bash scrips that can be found in cluster_jobs package.
1. Subtract background
Create an average background image of every channel (Red, Green, Behaviour) and save it in the parent folder /background/channel and run the script below to subtract it.
```bash
sbatch stack_subtract_background.sh
```
3. binarize red channel
Binarize the red channel with the script in local repository bash scripts.
Find an appropiate threshold and save it in the config.yaml file.
```bash
sbatch binarize_project.sh
```
old alternative:
```bash
sbatch binarize.sh
```
After this step check for each recording that the mask is reasonable. Different recordings have different red intensities so the parameters (thresholds) might need one to one adjustment.

5. mask image (each channel with the red mask)
```bash
sbatch mask_img.sh
```
7. measure mask
```bash
sbatch measure_mask.sh
```
8. run save_measurements()
Run this python function to merge the measurements results on each Channel (red and green) into one file in the parent directory.
This code is now in the distance transformation.py module but it might be moved soon.
at the moment it can be run by:
```python
python distance_transformation.py
```

### Plotting to visualize results
Use /dev/GUI.py or /dev/plotting_space.py to visualize your results.

### Run the code (Is this outdated?)
Now you can run the code in epifluorescence_calcium_imaging/dev/distance_transformation.py or use the plotting notebook.

The code will find the transformation between your beads coordinates from bead_position_zim06.csv and bead_position_after.csv and apply it to the coordinates you saved as circle_coords.csv. The new coordinates are saved as circle_coords_mm.csv.

The second part of the code will calculate the distance from the circle_coords_mm.csv to the worm coordinates, saving the shortest distance for every time point to the food.

This distance is to be compared with the Neuronal traces.


