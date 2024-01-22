Some Jupyter Notebooks and scripts to work with deeplabcut

## Input data into DLC
To annotate with Fiji and then import the data to DLC format.
### Input data from Fiji

Parameters:
- - - - - - - - - 
Inputs:

	Video recording which you wish to annotate.

	It is better if some frames are annotated on DLC previously, therefore the data structure already exisits and does not have to be created from 0. (You want to have folders inside labeled-data and the CollectedData.csv file)

Outputs:

	1. A list of the images you annotated saved in directory.
	2. A text file with the same format as CollectedData.csv

#### Pipeline:	
1. Open a stack on Fiji (Ideally on the cluster: https://it.vbc.ac.at/clip/cbe/xpra#)
2. Open the DLC_annotation_assistant.ijm (from fiji_macros Repository: https://bitbucket.vbc.ac.at/users/ulises.rey/repos/fiji_macros/browse/DLC_annonatation_assistant.ijm)
	2.1 Read the macro and modify the fields that need to be modified
3. Label several frames with the Multi-point tool (Only one bodypart, Only one bodypart per frame!)
	At the moment this does not work for annotation of multiple bodyparts in one frame.
	(Optional: Save the points)
4. After annotating all desired frames, press measure or "m" in Fiji to get the coordinates of all the frames
5. Run the Macro
6. Copy the text output into CollectedData.csv

### Convert/Rename the image filenames and the CollectedData files
In principle the macro saved the names correctly, but ut could be that Fiji saved the files as:
img001.png instead of img000001.png, and the same in the CollectedData.csv
If the names are not properly written DLC does not read them.

The correct number of zeros can be the length of the highest number annotated, but it is better to have it as the highest number possible. For a recording of 200 000 frames it should be img000001.png

To correct this there are two functions in this repository, in the file dlc_utils.py (add_zeros_to_filename and add_zeros_to_csv)
Read their description to use them both.
1. Run add_zeros_to_filename
2. add_zeros_to_csv
3. Manually correct the csv File:
	3.1. Rename CollectedData.csv to CollectedData_original.csv, and CollectedData_new.csv to CollectedData.csv 
	3.2.  Double check that scorers are alright "Ulises", "Ulises" and not "Ulises1", "Ulises2", etc. 
4. Run on a GPU notebook (DLC_useful_functions.ipynb for example) the deeplabcut.convertcsv2h5(config_filepath, userfeedback=True) function.



### Training
After this you can go to the DLC.ipynb notebook and retrain the network.
1. deeplabcut.merge_datasets(path_config_file)
2. deeplabcut.create_training_dataset(path_config_file, net_type='resnet_50', augmenter_type='imgaug')
3. deeplabcut.train_network(path_config_file, shuffle=1, displayiters=5000,saveiters=2500)
 

