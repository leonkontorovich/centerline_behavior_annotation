import pandas as pd
from pathlib import Path
import numpy as np
import os
import matplotlib.pyplot as plt
import tifffile as tiff
from natsort import natsorted

def head2(data, px_mm, x_lenght):
    
    return(data*px_mm-x_lenght*px_mm/2)