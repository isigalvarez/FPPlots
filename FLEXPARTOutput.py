# !usr/bin/env python3
# ===========================================================
# Created on 29/04/2019
# Class to open the output of a FLEXPART simulation and
# extract some information about plume and trajectories.
# ===========================================================

import os
import csv
import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.cm as mpl_cm
import iris.quickplot as qplt

from netCDF4 import Dataset
from matplotlib.backends.backend_pdf import PdfPages
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


def main():
    # Define parameters
    runDir = '/home/isi/FLEXPART/flexpart10_git/Runs/CAFE/Flight13/'
    # Initiate the class
    FPOut = FLEXPARTOutput(runDir)
    print(FPOut.trajDataMeta.head())
    print(FPOut.trajData.head())
    return FPOut

    # # Other tests
    # trajPath = '/home/isi/FLEXPART/flexpart10_git/Runs/CAFE/Flight13/output/trajectories.txt'
    # dfChunks = pd.read_csv(trajPath, sep='\s+', engine='python',
    #                        skiprows=3, nrows=116*2, header=None)
    # df_locs = dfChunks.iloc[::2].reset_index(drop=True)
    # df_commt = dfChunks.iloc[1::2].reset_index(drop=True)
    # df_commt['Comment'] = df_commt.iloc[:, 0:5].apply(
    #     lambda x: ' '.join(x), axis=1)
    # df_commt['Date'] = df_commt.iloc[:, 3:5].apply(
    #     lambda x: ' '.join(x), axis=1)
    # df_commt['Date'] = pd.to_datetime(df_commt['Date'])
    # df_commt.drop(np.arange(10), inplace=True, axis=1)
    # df = pd.concat([df_locs, df_commt], axis=1)
    # df.columns = ['t_start', 't_end', 'lon_left', 'lat_down', 'lon_right',
    #               'lat_up', 'z_dowm', 'z_top', 'spec', 'n_particles',
    #               'comment', 'release_date']


class FLEXPARTOutput():
    """
    Handle output from a FLEXPART simulation.

    (!) This code was developed to work with
    bacwards simulations. Funny stuff may happen
    when applied on forward output. Please check 
    results carefully.
    """

    def __init__(self, runDir):
        """
        Initialize the class attributes
        """
        # FLEXPART simulation directory and output
        self.runDir = runDir
        self.outputDir = f'{runDir}output/'
        # Initialize variables
        self.trajFile = ''
        self.trajData = pd.DataFrame()
        self.trajDataMeta = pd.DataFrame()
        self.ncFile = ''
        self.ncData = []
        # Call load_files()
        self.load_files()

    def load_files(self):
        """
        Looks for data and loads it.
        """
        # Check for trajectories file
        print("\nLooking for trajectories file... ")
        files_all = os.listdir(self.outputDir)
        files = [f for f in files_all if f.startswith('traj') == True]
        files.sort()
        # If there is one file, save the information
        if len(files) == 1:
            self.trajFile = self.outputDir+files[0]
            self.trajData, self.trajDataMeta = self.extract_trajectories()
            print(f' {self.trajFile} found.')
        # IF there is no file or more than one, say it.
        elif len(files) == 0:
            print(" No file found.")
        else:
            print(' More than one file found. Check Output.')
        # Check for nc files
        print("Looking for netCDF4 file... ")
        files_all = os.listdir(self.outputDir)
        files = [f for f in files_all if f.endswith('.nc') == True]
        files.sort()
        # If there is one file, save the information
        if len(files) == 1:
            self.ncFile = self.outputDir+files[0]
            self.ncData = Dataset(self.ncFile)
            print(f' {self.ncFile} found.')
        # IF there is no file or more than one, say it.
        else:
            print(" No file found.")

    def extract_trajectories(self):
        '''
        Extract the trajectories data from a txt file
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
        # == Prepare the extraction =============================
        # Read the file to know metada number of rows and end date
        with open(self.trajFile, 'r') as f:
            # Extract the first three rows of the file
            header = list(csv.reader(f))[:3]
            # Extract the date and the hour of the end of simulation
            endDate = header[0][0].split(' ')[0].zfill(8)
            endHour = header[0][0].split(' ')[1].zfill(6)
            # Combine them to make a date
            endDate = pd.to_datetime(endDate+endHour)
            # Extract the number of rows with trajectories metadata
            metaRows = 2*int(header[2][0])

        # == Extract the metadata ===============================
        # Define headers
        headers = ['t_start', 't_end', 'lon_left', 'lat_down', 'lon_right',
                   'lat_up', 'z_dowm', 'z_top', 'spec', 'n_particles', 'j',
                   'comment']
        # Extract the metadata
        dfRaw = pd.read_csv(self.trajFile, sep='\s+', engine='python',
                            skiprows=3, nrows=metaRows, header=None)
        # Take only the odd rows to extract data about releases
        df_locs = dfRaw.iloc[0::2].reset_index(drop=True)
        # Define the release number
        df_locs['j'] = len(df_locs.index)-df_locs.index.values
        # Take only the even rows to extract the comments
        df_commt = dfRaw.iloc[1::2].reset_index(drop=True)
        # Collapse all columns to make the comment
        df_commt['Comment'] = df_commt.iloc[:, 0:5].apply(
            lambda x: ' '.join(x), axis=1)
        # Drop unwanted columns and combine both dataframes
        df_commt.drop(np.arange(10), inplace=True, axis=1)
        df_meta = pd.concat([df_locs, df_commt], axis=1)
        # Rename the columns
        df_meta.columns = headers
        # Build the date
        df_meta['Date'] = endDate + \
            pd.to_timedelta(df_meta['t_start'].astype(int), 'S')

        # == Extract the data itself ============================
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
                         skiprows=metaRows+3, header=None, names=names)
        # Extract releases number
        releases = df['j'].unique()
        # Iterate over each realease
        df_list = []
        for release in releases:
            # Create a temporal dataframe for the current release
            df_temp = df[df['j'] == release]
            # Extract the release date for the current release
            release_date = df_meta[df_meta['j'] == release]['Date'].values
            # Add the date to those releases
            df_temp['Date'] = release_date + \
                pd.to_timedelta(df_temp['t'].astype(int), 'S').values
            # Save the positions
            df_list.append(df_temp)
        # Concatenate the dataframes
        df = pd.concat(df_list, ignore_index=True)
        # return the data
        return df, df_meta

    def extract_positions(self, df):
        """
        Converts the trajectories dataframe into a dict with 
        one item for each release. Each item consists of a tuple
        of longitude, latitude and height.
        """
        # Load the data
        df = self.trajData.copy()
        # Extract info about releases
        releases = df['j'].unique()
        # Iterate over each realease
        releases_pos = {}
        for release in releases:
            # Create a dataframe with the release info
            df_temp = df[df['j'] == release]
            # Create a list of tuples (longitude, latitude, height)
            pos_temp = [(row['xcenter'], row['ycenter'], row['zcenter'])
                        for idx, row in df_temp.iterrows()]
            # Save the positions
            releases_pos[release] = pos_temp
        # Return the results
        return releases_pos

    def plotMap_trajectories(self, pos_list, extent=None, fsize=(12, 10)):
        '''
        Plots a simple map to take a quick look about trajectories. 
        '''
        # Create figure and axes
        fig = plt.figure(figsize=fsize)
        ax = plt.axes(projection=ccrs.PlateCarree())
        # Find and stablish its limits
        if extent:
            ax.set_extent(extent)
        else:
            lon_max = np.ceil(lon.max())
            lon_min = np.floor(lon.min())
            lat_max = np.ceil(lat.max())
            lat_min = np.floor(lat.min())
            ax.set_extent([lon_min, lon_max, lat_min, lat_max])
        # Draw coastlines
        ax.coastlines('50m', linewidth=1, color='black')
        # Prepare the grid
        gd = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                          linewidth=1, linestyle='--', color='k',
                          alpha=0.5)
        gd.xlabels_top = False  # Take out upper labels
        gd.ylabels_right = False  # Take out right labels
        gd.xformatter = LONGITUDE_FORMATTER  # Format of lon ticks
        gd.yformatter = LATITUDE_FORMATTER  # Format of lat ticks
        # Iterate over positions
        for pos in pos_list:
            # Extract latitude and longitude
            lat, lon = pos
            # Plot the first point as a dot
            ax.plot(lon[0], lat[0], 'o')
            # Plot the trajectorys
            ax.plot(lon, lat, color='red', linestyle='--')
            # return the figure just in case
            return (fig, ax)


if __name__ == '__main__':
    print('Ready to go!')
    FPOut = main()
