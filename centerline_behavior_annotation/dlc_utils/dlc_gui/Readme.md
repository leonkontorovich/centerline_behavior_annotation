Install dlc_gui.
Source: https://gitlab.com/keq/dlc-gui

Somehow installing dlc_gui as described in their repository gives an error.

A friend of Fabio created this file which allows to install dlc_gui without errors.

Steps:
1. Make a copy of your DLC env and name it dlc_gui
https://stackoverflow.com/questions/40700039/how-can-you-clone-a-conda-environment-into-the-root-environment
2. conda activate your dlc_gui environment
3. pip install "path2wheel-file”
4. pythonw -m dlc_gui (for mac)
python -m dlc_gui for windows.

**It is recommended to cd to your labeled-data folder before running dlc_gui**

5. Choose your dlc project config.yaml file
6. Open a folder with data to label
7. To go faster label first the nose in all frames, and then the tail.
Check the gitlab repo for the shortcuts.



!Important: the dlc_gui will not show you annotations even if they exist already  in collected_data_user.h5 (unlike dlc which does), so make sure you only label folders that are still unlabeled. Othwerwise you will label twice and/or overwrite.
