# Nose and Tail annotation in DLC for centerline package

It is recommended to work with behavioural data where:
1. Background has been subtracted
2. Data has been normalized

Once you have your images like this, you can select your recordings and extract frames using the dlc.extract_frames().

After extracting frames it is recommended to annotate the frames with the dlc_gui, since it is much faster.


Nose and tail look different during coils. To increase the amount of training images during coils we use the cluster_jobs/array_job_directories_extract_contours.sh which calls the stack_extract_and_save_contours_with_children() python function of the imutils package.
As the code is now it will create a subfolder inside the behaviour folder with frames where there are coils.
Copy them to your local deeplabcut_projects folder
Something like this:
```bash
rsync -av --partial --progres /Volumes/scratch/neurobiology/zimmer/ulises/wbfm/2022*worm*/data/*worm*/*BH/2022*raw_coiled_shapes*/ /Users/ulises.rey/local_code/deeplabcut_projects/wbfm_nose_tail-ulises-2023-01-04/labeled-data
```
It is better to keep them in different folders, because then annotating with the dlc_gui is easier.



