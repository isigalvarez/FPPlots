# !usr/bin/env python3
# ===========================================================
# Created on 29/04/2019
# Class to open the output of a FLEXPART simulation and
# extract some information about plume and trajectories.
# ===========================================================

import os
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from netCDF4 import Dataset
from matplotlib.backends.backend_pdf import PdfPages
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

def main():
    # Define parameters
    runDir = 'testData/output_03_MassPlumeTrajectories_netCDF/'
    # Initiate the class
    FPOut = FLEXPARTOutput(runDir)

class FLEXPARTOutput():
    """
    Handle output from a FLEXPART simulation.
    """

    def __init__(self, runDir):
        """
        Initialize the class attributes
        """
        # FLEXPART simulation directory and output
        self.runDir = runDir
        self.outputDir = f'{runDir}output/'
        # Initialize variables
        self.traj = pd.DataFrame()
        self.plume = []
        # Check for trajectories file
        print("Looking for trajectories file... ")
        files_all = os.listdir(self.outputDir)
        files = [f for f in files_all if f.startswith('traj') == True]
        files.sort()
        if len(files) == 1:
            print(' File found.')
            self.trajFile = files[0]
        elif len(files) == 0:  
            print(" No 'trajectories.txt' file found.")
        else:
            print(' More than one trajectories file found. Check Output.')
        # Check for nc files
        print("Looking for netCDF4 files... ")
        files_all = os.listdir(self.outputDir)
        files = [f for f in files_all if f.endswith('.nc') == True]
        files.sort()
        if len(files) == 1:
            print(' File found.')
            self.trajFile = files[0]
        elif len(files) == 0:  
            print(" No 'trajectories.txt' file found.")
        else:
            print(' More than one trajectories file found. Check Output.')


    def extract_trajectories(self):
        '''
        This function extract the trajectories data from a txt file
        and saves it to a pandas Dataframe.

        The file 'trajectories.txt' contains a short header with
        information about the release definition. After that, there
        are 41 columns with detailed information about the clustered
        trajectories and one row per timestep of the simulation

        These variables and its names are, in order:
        j             Release number
        t             Time elapsed (s) since the middle of the release
        xcenter       Longitude of the release plume (RPC)
        ycenter       Latitude of the release plume (RPC)
        zcenter       Height of the release plume (RPC)
        topocenter    Mean topography underlying all particles
        hmixcenter    Mean mixing height for all particles
        tropocenter   Mean tropopause height at the positions of particles
        pvcenter      Mean PV for all particles
        rmsdist       Total horizontal rms distance before clustering
        rms           Total horizontal rms distance after clustering
        zrmsdist      Total vertical rms distance before clustering
        zrms          Total vertical rms distance after clustering
        hmixfract     Fraction of particles under the mean mixing height
        pvfract       Fraction of particles with PV<2pvu
        tropofract    Fraction of particles within the troposphere
        xclust_k      Longitude of the k-th cluster
        yclust_k      Latitude of the k-th cluster
        zclust_k      Height of the k-th cluster
        fclust_k      Fraction of particles belonging k-th cluster
        rmsclust_k    Horizontal rms distance for k-th cluster
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
        df = pd.read_csv(self.trajFile, engine='python', sep='\s+',
                         skiprows=5, header=None, names=names)
        # Return the data
        return df

if __name__ == '__main__':
    print('Ready to go!')
    main()