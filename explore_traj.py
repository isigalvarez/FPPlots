# !usr/bin/env python3
# ===========================================================
# Created on 17/04/2019
# This script is a first aproximation to extract flexpart
# trajectories output using python
# ===========================================================

import os
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

# == Extract Data ===========================================
def extract_trajectories(filePath):
    '''
    This function extract the trajectories data from a txt file. 
    '''

# ===========================================================

if __name__ == '__main__':
    # == Define parameters ==================================
    # Path to some grid files
    dataPath = 'testData/output_05_BwdTraj_SegunManual_netCDF/'
    # =======================================================

    # == Find data files ====================================
    # First we extract all the files inside output dir
    files_all = os.listdir(dataPath)
    # Take only files beginning with 'grid'
    files = [f for f in files_all if f.startswith('traj') == True]
    # Choose the file
    filePath = dataPath + files[0]
    # =======================================================

