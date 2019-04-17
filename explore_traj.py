# !usr/bin/env python3
# ===========================================================
# Created on 17/04/2019
# This script is a first aproximation to extract flexpart cluster
# trajectories from the file 'trajectories.txt'
#
# The file 'trajectories.txt' contains a short header with
# information about the release definition. After that, there
# are 41 columns with detailed information about the clustered
# trajectories and one row per timestep of the simulation
#
# This variables and its names are, in order:
# j             Release point
# t             Time elapsed (s) since the middle of the release
# xcenter       Longitude of the release plume
# ycenter       Latitude of the release plume
# zcenter       Height of the release plume
# topocenter    Mean topography underlying all particles
# hmixcenter    Mean mixing height for all particles
# tropocenter   Mean tropopause height at the positions of particles
# pvcenter      Mean PV for all particles
# rmsdist       Total horizontal rms distance before clustering
# rms           Total horizontal rms distance after clustering
# zrmsdist      Total vertical rms distance before clustering
# zrms          Total vertical rms distance after clustering
# hmixfract     Fraction of particles under the mean mixing height
# pvfract       Fraction of particles with PV<2pvu
# tropofract    Fraction of particles within the troposphere
# xclust_k      Longitude of the k-th cluster
# yclust_k      Latitude of the k-th cluster
# zclust_k      Height of the k-th cluster
# fclust_k      Fraction of particles belonging k-th cluster
# rmsclust_k    Horizontal rms distance for k-th cluster
# ===========================================================

import os
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from matplotlib.backends.backend_pdf import PdfPages
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

# == Extract Data ===========================================


def extract_trajectories(filePath):
    '''
    This function extract the trajectories data from a txt file
    and saves it to a pandas Dataframe.
    '''
    # Define the variables names
    names = ['j', 't', 'xcenter', 'ycenter', 'zcenter', 'topocenter',
             'hmixcenter', 'tropocenter', 'pvcenter', 'rmsdist',
             'rms', 'zrmsdist', 'zrms', 'hmixfract', 'pvfract',
             'tropofract']
    names_cluster = ['xclust', 'yclust', 'zclust', 'fclust',
                     'rmsclust']
    # Define the number of clusters
    nClusters = 5
    # Build the whole namelist
    for i in range(nClusters):
        names += [s+f'_{i+1}' for s in names_cluster]
    # Extract the data
    df = pd.read_csv(filePath, engine='python', sep='\s+',
                     skiprows=5, header=None, names=names)
    # Return the data
    return df
# ===========================================================


if __name__ == '__main__':
    # == Define parameters ==================================
    # Path to some grid files
    dataPath = 'testData/output_03_MassPlumeTrajectories_netCDF/'
    # =======================================================

    # == Find data files ====================================
    # First we extract all the files inside output dir
    files_all = os.listdir(dataPath)
    # Take only files beginning with 'grid'
    files = [f for f in files_all if f.startswith('traj') == True]
    # Choose the file
    filePath = dataPath + files[0]
    # =======================================================

    # == Extract data =======================================
    df = extract_trajectories(filePath)
