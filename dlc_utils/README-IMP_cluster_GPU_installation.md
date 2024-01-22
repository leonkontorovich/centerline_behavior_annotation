# How-to install a GPU-ready environment

Tested on a Jupyter Lab environment on the cluster.

First you must request a server, which must be on the **GPU partition** for this to work

## Getting DeepLabCut
You may have already done this, but first git clone:
```
git clone https://github.com/AlexEMG/DeepLabCut.git
```

## Conda environment setup
You can choose your own name, but probably should have 'GPU' in the name:

```
conda create -n DLC-GPU python=3.6.6 cudatoolkit=10.0 cudnn
```

## Conda activate
''''
conda activate DLC-GPU
'''

If there are problems you have to follow the instructions.
Most likely you have to:
>conda init bash
and restart the shell

Activate DLC-GPU
''''
conda activate DLC-GPU
'''


Put the following DLC-GPU-forCBE.txt file somewhere:

```
deeplabcut
ipywidgets
jupyter
seaborn
tensorflow-gpu==1.13.1
https://extras.wxpython.org/wxPython4/extras/linux/gtk3/centos-7/wxPython-4.1.0-cp36-cp36m-linux_x86_64.whl
```

Then install it. For example, if you put it in DeepLabCut/conda-environments, run the following:

```
cd DeepLabCut/conda-environments
pip install -r DLC-GPU-forCBE.txt
```

## In the notebook
You need to turn off the GUI in order to run on the cluster, so add the following lines to the top of the code:

```
import os
os.environ["DLClight"] = True
```


Then it should work!
