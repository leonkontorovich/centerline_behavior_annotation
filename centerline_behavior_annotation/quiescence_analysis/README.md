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
	pip install /code/quiescence/
	```
	or better:
	cd to the directory where you cloned the directory
	```
	cd ../code/quiescence/
	```
	And then pip install the local directory
	```
	pip install .
	```
	
	This would be wrong:
	```
	pip install quiescence/
	```
	Because it will install another centerline package that someone has uploaded to pip.



# Documentation

This script processes binarized time-series images (TIFF format) to compute pixel differences between frames, which helps analyze movement. It removes noise, validates frames based on object size, and calculates quiescence based on speed and pixel changes.

## Functions

```
get_frame_diff(img_path, frame_shift=3, norm_size_threshold=0.4, centroid=None, zscore_threshold=1.5, debug=False, fps=10)
```
Description: Computes the difference in pixels between two frames separated by a given shift.

Parameters:

- img_path: Path to the TIFF file containing binarized image frames.

- frame_shift: Number of frames to shift when computing differences.

- norm_size_threshold: Threshold for ignoring small differences, given as a fraction of the reference size.

- centroid: Optional centroid data for correcting cropping issues.

- zscore_threshold: Absolute z-score threshold for removing frames with anomalous object sizes.

- debug: If True, prints debug information.

- fps: Frame rate of the recording, used for normalizing frame_shift.

Returns: A numpy array containing pixel differences for each frame.


```
get_fixed_crop_based_on_centroid(frame, next_frame, centroid, next_centroid, debug=False)
```

Description: Adjusts frame alignment based on centroid positions to correct cropping inconsistencies.

```
get_average_ref_area(img_path, fraction_frames=0.1, debug=False)
```

Description: Calculates the average object size in a subset of frames to serve as a reference size.


```
validate_frame(frame, ref_size, ref_size_std, zscore_thresh=1.5, debug=False)
```
Description: Validates whether a frame contains a single object of reasonable size based on z-score thresholds.

```
get_segments_area(img, debug=False)
```
Description: Identifies segmented regions in a frame and extracts their area sizes.

```
calculate_pixel_diff(frame, next_frame, ref_size, norm_size_threshold, debug=False)
```
Description: Computes the difference in pixel areas between two frames, filtering out small changes based on a threshold.

```
get_quiescence(speed_arr, pixel_diff_arr, speed_threshold, pixel_diff_threshold, debug=False)
```
Description: Determines periods of quiescence (inactivity) based on speed and pixel change thresholds.

## Thresholds Used

- Frame Shift (frame_shift): controls how many frames apart the script compares when computing the pixel difference. This depends on the framerate of the video, the frameshift for fps 10 is 3. Since recordings differ in fps the script normalizes frame_shift. -> norm_frame_shift = int(round((frame_shift / 10) * fps)) 

- Normalized Size Threshold (norm_size_threshold): Filters out small pixel changes caused by noise, keeping only meaningful differences relative to the object's size. Default is 0.4 % of the worm reference size.
  
- Z-Score Threshold (zscore_threshold): filters frames based on the size of the object. It calculates how many standard deviations the object's area is from the reference size. If the z-score exceeds the threshold, the frame is skipped. Default is 1.5
  
- Reference Size Fraction (fraction_frames): defines the portion of frames used to calculate the average object size.

the following 2 depend largely on your data and have to evaluated by every user:

- Speed Threshold (speed_threshold):  defines the maximum speed at which the worm is considered quiescent.

- Pixel Difference Threshold (pixel_diff_threshold): max pixel difference for worm to be considered quiescent
