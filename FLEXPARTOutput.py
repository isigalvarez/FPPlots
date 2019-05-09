# !usr/bin/env python3
# ===========================================================
# Created on 29/04/2019
# Class to open the output of a FLEXPART simulation and
# extract some information about plume and trajectories.
# ===========================================================

import os
import csv
import folium
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib as mpl
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from seaborn import set_style
from dask.diagnostics import ProgressBar
from netCDF4 import chartostring
from matplotlib.backends.backend_pdf import PdfPages
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


class FLEXPARTOutput():
    """
    Handle output from a FLEXPART simulation.

    Requires the directory where FLEXPART output
    files are stored at initializaton.

    (!) This code was developed to work with
    backwards simulations. Funny stuff may happen
    when applied on forward output. Please check 
    results carefully.
    """

    def __init__(self, outputDir):
        """
        Initialize the class attributes
        """
        # FLEXPART output directory
        self.outputDir = outputDir
        # Initialize variables
        self.trajFiles = None
        self.trajFilesMeta = None
        self.trajData = None
        self.trajDataMeta = None
        self.ncFile = None
        self.ncData = None
        self.ncDataMeta = None

    def load_netcdf(self, outputDir=None):
        """
        Handles the extraction of netcdf data from
        the given file or files.
        """
        # Save outputDir
        if not outputDir:
            outputDir = self.outputDir
        # Check for nc files
        print("Looking for netCDF4 file... ")
        files_all = os.listdir(outputDir)
        files = [f for f in files_all if f.endswith('.nc') == True]
        files.sort()
        # If there is one file, save the information
        if len(files) == 1:
            self.ncFile = outputDir+files[0]
            self.ncData = self.extract_nc()
            self.ncDataMeta = self.extract_ncMeta()
            print(f' {self.ncFile} found.')
        # IF there is no file or more than one, say it
        elif len(files) == 0:
            print(" No file found.")
        else:
            pass  # ADD MULTIPLE FILES EXRACTION

    def load_trajectories(self, outputDir=None):
        """
        Handles the extraction of trajectories data from
        the given file or files.
        """
        # Save outputDir
        if not outputDir:
            outputDir = self.outputDir
        # Check for trajectories file
        print("\nLooking for trajectories file... ")
        files_all = os.listdir(outputDir)
        files = [f for f in files_all if f.startswith('traj') == True]
        files.sort()
        # If there is one file, save the information
        if len(files) == 1:
            self.trajFiles = outputDir+files[0]
            self.trajData, self.trajDataMeta = self.extract_traj()
            print(f' {self.trajFiles} found.')
        # If there are two files check for data and metadata
        elif len(files) == 2:
            # The last part before the dot should be 'data'
            if files[0].split('.')[0].split('_')[1] == 'data':
                self.trajFiles = files[0]
                self.trajData = pd.read_csv(f'{outputDir}/{files[0]}')
            else:
                raise FileNotFoundError(f'Unexpected file: {files[0]}')
            # The last part before the dot should be 'metaData'
            if files[1].split('.')[0].split('_')[1] == 'metaData':
                self.trajFilesMeta = files[1]
                self.trajDataMeta = pd.read_csv(f'{outputDir}/{files[1]}')
            else:
                raise FileNotFoundError(f'Unexpected file: {files[1]}')
        # If there is no file or more than one, say it.
        elif len(files) == 0:
            raise FileNotFoundError('No files found')
        else:
            raise RuntimeError('More than two files found. Check output.')

    def extract_traj(self, trajFile=None):
        '''
        This function is a wrapper for the functions:
        -   extract_traj_metadata()
        -   extract_traj_data()

        It extract trajectories data and metada into Dataframes.
        '''
        # == Prepare the extraction =============================
        if not trajFile:
            trajFile = self.trajFiles
        # Read the file to know metada number of rows and end date
        with open(trajFile, 'r') as f:
            # Extract the first three rows of the file
            header = list(csv.reader(f))[:3]
            # Extract the date and the hour of the end of simulation
            endDate = header[0][0].split(' ')[0].zfill(8)
            endHour = header[0][0].split(' ')[1].zfill(6)
            # Combine them to make a date
            endDate = pd.to_datetime(endDate+endHour)
            # Extract the number of rows with trajectories metadata
            metaRows = 2*int(header[2][0])
        # Extract data and metadata and return it
        df_meta = self.extract_traj_metaData(trajFile, metaRows, endDate)
        df = self.extract_traj_data(trajFile, metaRows, df_meta)
        return df, df_meta

    def extract_traj_metaData(self, trajFile, metaRows, endDate):
        """
        Extract meta data about the trajectories contained within
        the trajectories file.

        The trajectories.txt file has 3 rows for the header and
        then lists information about all release points in groups
        of two rows for each release

        Variables provided are in the first row:
        t_start     Start time of the release (Seconds since the 
                    begging of the simulation)
        t_end       End time of the release(Seconds since the 
                    begging of the simulation)
        lon_left    Left longitude of the release box
        lat_bottom  Bottom latitude of the release box
        lon_right   Right longitude of the release box
        lat_top     Top latitude of the release box
        z_bottom    Bottom height of the release box
        z_top       Top height of the release box
        spec        Species of the releases
        n_particles Total number of particles released
        j           Index associated with the release

        Variables provided are in the second row:
        comment     Comment
        """
        # == Extract the metadata ===============================
        # Define headers
        headers = ['t_start', 't_end', 'lon_left', 'lat_bottom', 'lon_right',
                   'lat_top', 'z_bottom', 'z_top', 'spec', 'n_particles', 'j',
                   'comment']
        # Extract the metadata
        dfRaw = pd.read_csv(trajFile, sep='\s+', engine='python',
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
        # Return the data
        return df_meta

    def extract_traj_data(self, trajFile, metaRows, df_meta):
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
        # == Define Parameters ==================================
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

        # == Extract the data ===================================
        # Call read_csv
        df = pd.read_csv(trajFile, engine='python', sep='\s+',
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
        return df

    def combine_trajectories(self, runDirs, saveDir):
        """
        Combines all trajectories data and saves in two new
        dataframes, one for trajectories and one for metadata.
        Saves the files in a directory 'output_processed/' in
        the 'saveDir' directory. Return the new location.

        This function will replace the 'j' release index with a 
        new one based on the number of total trajectories
        combined.
        """
        # == Find the netrajectories tCDF files =================
        # Iterate over them finding the nc files
        filesPaths = []
        for folder in runDirs:
            files = os.listdir(f'{folder}/')
            # Take only files starting with 'traj'
            files = [file for file in files if file.startswith('traj')]
            # Add the path
            filesPaths.append(f'{folder}/{files[0]}')

        # == Prepare the output dir =============================
        # Create the output directory
        outputDir = os.path.abspath(f'{saveDir}/output_processed/')
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)

        # == Iterate over the trajectory files ==================
        df_list = []
        dfMeta_list = []
        accumReleases = 0
        for f in filesPaths:
            # Call extract_trajectories
            df, df_meta = self.extract_traj(f)
            # Extract the number of current releases
            currentReleases = len(df['j'].unique())
            # Create a mapping dict to rename the 'j' index
            oldValues = df['j'].unique()
            newValues = np.arange(1, currentReleases+1)+accumReleases
            mapDict = dict(zip(oldValues, newValues))
            # Note down the number of releases so far
            accumReleases += currentReleases
            # Remap the 'j' index
            df['j'].replace(mapDict, inplace=True)
            # Append them
            df_list.append(df)
            dfMeta_list.append(df_meta)
        # Concatenate the dataframes
        df = pd.concat(df_list, ignore_index=True)
        df_meta = pd.concat(dfMeta_list, ignore_index=True)
        # Save the files
        df.to_csv(f'{outputDir}/trajectories_data.csv')
        df_meta.to_csv(f'{outputDir}/trajectories_metaData.csv')
        # Returns the new output directory
        return outputDir

    def extract_nc(self, ncFile=None):
        """
        Open the netcdf file and uploads them. If there is more
        than one it will try to combine them. 
        """
        # Get the file name
        if not ncFile:
            ncFile = self.ncFile
        # Open the dataset
        dataset = xr.open_dataset(ncFile)
        # Take only the airtracer data and return it
        return dataset['spec001_mr']

    def extract_ncMeta(self, ncFile=None):
        '''
        This function extract information about the tracer
        releases from a netCDF4 file generated by FLEXPART.

        It return a tuple containing the time, height, latitude,
        longitude and release comment. 
        '''
        # Get the file name
        if not ncFile:
            ncFile = self.ncFile
        # Open the dataset
        dataset = xr.open_dataset(ncFile)
        # Take only the airtracer data
        ds = dataset['spec001_mr']
        # Extract the coordinates
        date = pd.Index(ds.time.values)
        lon = ds.longitude.to_series()
        lat = ds.latitude.to_series()
        hgt = ds.height.to_series()
        # Get the comments
        rlsComment = [str(c).split("'")[1].strip()
                      for c in dataset['RELCOM'].values]
        # Return
        return [date, hgt, lat, lon, rlsComment]

    def extract_positions(self, df):
        """
        Converts the trajectories dataframe into a dict with 
        one list for each release. Each list consists of three lists
        containing date, longitude, latitude and height.

        (Not being used right now)
        """
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

    def plotMap_traj(self, releases=None, extent=None,
                     fsize=(12, 10)):
        '''
        Plots a simple map to take a quick look about trajectories. 

        Input:
        - releases  List of integers. References the releases numbers
                    to plot
        - extent    Limits of the map (lonMax,lonMin,latMax,latMin). If
                    None will use the limits of the trajectories
        - fsize     Size of the figure (height,width)
        '''
        # Extract inner data
        df = self.trajData.copy()
        # Specify the releases to plot
        if not releases:
            releases = df['j'].unique()
        # Create a dataframe with only the relevant releases
        dfTemp = df[df['j'].isin(releases)]
        # Create figure and axes
        set_style('ticks')
        fig = plt.figure(figsize=fsize)
        ax = plt.axes(projection=ccrs.PlateCarree())
        # Find and stablish its limits
        if extent:
            ax.set_extent(extent)
        else:
            lon_max = np.ceil(dfTemp['xcenter'].max()+0.5)
            lon_min = np.floor(dfTemp['xcenter'].min()-0.5)
            lat_max = np.ceil(dfTemp['ycenter'].max()+0.5)
            lat_min = np.floor(dfTemp['ycenter'].min()-0.5)
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
        # Iterate over releases
        for release in releases:
            # Extract a dataframe for the current release
            df_rls = dfTemp[dfTemp['j'] == release]
            # Plot the first point as a dot
            ax.plot(df_rls.iloc[0]['xcenter'], df_rls.iloc[0]['ycenter'], 'ko')
            # Plot the trajectorys
            ax.plot(df_rls['xcenter'], df_rls['ycenter'],
                    color='red', linestyle='--')
        # return the figure just in case
        return (fig, ax)

    def get_traj_dateRange(self, releases=None, show=False,
                           dateLims=[None, None]):
        """
        Retrieve information about the date range of the releases. If 
        'show' is set to true it will print the information as well.

        The number of the releases to be used can be defined using the
        variable 'releases'. It should be a list with the numbers 
        identifying the releases.
        Example: 4,5,6,7,111,112]

        If date limits are provided, it will restrict the releases 
        according to it, returning those releases which starting date
        is contained within 'dateLims'. This variable is a 2-item list
        with strings defining the start and end limits, respectively.
        Example: ['2017-08-28 12:00','2017-08-28 14:00']
        """
        # Extract inner data
        df = self.trajData.copy()
        # Specify the releases to plot
        if not releases:
            releases = df['j'].unique()
        # Create a dataframe with only the relevant releases
        dfTemp = df[df['j'].isin(releases)]
        # Iterate over releases
        dateRange = {}
        for release in releases:
            # Extract the current dateRange and save it
            dateTemp = dfTemp[dfTemp['j'] == release]['Date']
            dateRange[release] = (dateTemp.min(), dateTemp.max())
        # Restrict releases
        dateRange = self.restrict_releases_dateRange(dateRange, dateLims)
        # If required print a message
        if show:
            print('\nReleases range:')
            for release in dateRange:
                a = dateRange[release][0].strftime("%Y/%m/%d %H:%M")
                z = dateRange[release][1].strftime("%Y/%m/%d %H:%M")
                print(f' Release {release} time range: {a} to {z}')
        # Return results
        return dateRange

    def restrict_releases_dateRange(self, dateRange, dateLims):
        """
        Restrict the releases according to their starting dates
        and provided limits.
        """
        # Transform dateLims to datetime if they exist
        if dateLims[0]:
            dateLims[0] = pd.to_datetime(dateLims[0])
        if dateLims[1]:
            dateLims[1] = pd.to_datetime(dateLims[1])
        # Iterate over dateRange but modifying a copy
        dateRangeCopy = dateRange.copy()
        for release in dateRange:
            if dateLims[0]:
                # Pop out if release beginning <= startLimit
                if dateRange[release][0] <= dateLims[0]:
                    dateRangeCopy.pop(release, None)
            if dateLims[1]:
                # Pop out if release beginning <= endLimit
                if dateRange[release][0] >= dateLims[1]:
                    dateRangeCopy.pop(release, None)
        # Return the result
        return dateRangeCopy

    def plotFoliumMap_traj(self, releases=None):
        '''
        Plots a simple map to take a quick look about trajectories. 

        Input:
        - df        Dataframe with trajectories data. If None will
                    use the data extracted on initialization.
        - releases  List of integers. References the releases numbers
                    to plot
        '''
        # Extract inner data
        df = self.trajData.copy()
        # Specify the releases to plot
        if not releases:
            releases = df['j'].unique()
        # Create a dataframe with only the relevant releases
        dfTemp = df[df['j'].isin(releases)]
        # Create the map
        m = folium.Map(location=[16.7219, -22.9488], tiles='Stamen Terrain',
                       zoom_start=5)
        # Add capacity to see lat/lon on click
        m.add_child(folium.LatLngPopup())
        # Iterate over releases
        for release in releases:
            # Extract a dataframe for the current release
            df_rls = dfTemp[dfTemp['j'] == release]
            # == Plot the first point as a dot ==================
            # Create the position
            pos = (df_rls.iloc[0]['ycenter'], df_rls.iloc[0]['xcenter'])
            # Create an plane icon from 'fontawesome' ('fa') in black
            icon = folium.Icon(icon='fas fa-plane', prefix='fa', color='black')
            # Create a popup message
            popup = f'Plane position at: {df_rls.iloc[0]["Date"]}'
            # Add the marker to the map
            folium.Marker(pos, popup, icon=icon).add_to(m)
            # == Plot the line ==================================
            # Recreate the positions as a tuple
            pos = [(row['ycenter'], row['xcenter'])
                   for idx, row in df_rls.iterrows()]
            # Plot the line
            folium.PolyLine(pos, color='red', weight=2.5, opacity=1).add_to(m)
        # Return the result
        return m

    def plotMap_plume(self, date, level=0, releases=None, extent=None,
                      plumeLims=(0, None), savePath=None, dpi=200):
        """
        Plot a simple plume map from a FLEXPART simulation.

        Return the figure, axes, filled contour, contour and
        colorbar handles as a tuple to allow modifications.

        Input:
        date        Date to plot in format 'yyyy-mm-dd HH:MM'.
        level       Defines the height level to plot.
                    By defect is the lowest: 0.
        extent      Define the map limits. Should be a list with
                    format [lon_min, lon_max, lat_min, lat_max].
                    By default it will use all points available.
        plumeLims   Defines the limits values for the 
                    source-receptor sensitivity colorbar.
        savePath    Saving name. Path can be included.
        dpi         Quality of picture saved .
        """
        # == Prepare data =======================================
        # Retrieve metaData
        dates, hgt, lat, lon, releases = self.ncDataMeta
        # Convert input date to datetime
        date = pd.to_datetime(date)
        # Get the requested date index
        idx = dates.get_loc(date, method='nearest')
        # Extract the plume data
        plume = self.ncData
        plume = plume[0, :, idx, level, :, :]
        # We do not want distinction for each release, sum them
        # ADD RELEASE DISTINCTION
        plume = np.sum(plume, axis=0)

        # == Prepare figure =====================================
        # Create figure and axes
        set_style('ticks')
        fig = plt.figure(figsize=(10, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        # Find and stablish its limits
        if extent:
            ax.axis(extent)
        else:
            lon_max = np.ceil(lon.max())
            lat_max = np.ceil(lat.max())
            lon_min = np.floor(lon.min())
            lat_min = np.floor(lat.min())
            ax.axis([lon_min, lon_max, lat_min, lat_max])
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
        gd.xlabel_style = {'size': 10, 'color': 'k'}
        gd.ylabel_style = {'size': 10, 'color': 'k'}
        # Set title
        ax.set_title(f'{date.strftime("%Y/%m/%d %H:%M")}', color='k')

        # == Plot the data ======================================
        # Define colorbar limits
        pMin = plumeLims[0]
        pMax = plumeLims[1]
        extend = 'both'
        # If no max is provided, change pMax and extend
        if not pMax:
            pMax = np.ceil(np.max(plume))
            extend = 'min'
        # Make sure they're in ascending order
        if pMax > pMin:
            levels = np.linspace(pMin, pMax, 9)
        else:
            levels = 2
        # Call contourf
        c1 = ax.contourf(lon, lat, plume, cmap='jet', levels=levels,
                         extend=extend)
        # Call contour
        c2 = ax.contour(lon, lat, plume, colors=('k',), levels=levels,
                        linewidths=(.5,))

        # == Make the colorbar ==================================
        # Define colors outside boundaries
        c1.cmap.set_under('white')
        # If there is no data, will throw an error. Use a try
        try:
            cb = fig.colorbar(c1, format='%.1f')
            cb.set_label('Source-Receptor Relationship (s)', color='k')
            cb.set_tick_params(color='k')
        except:
            pass
        if savePath:
            fig.savefig(savePath, dpi=dpi,
                        bbox_inches='tight', transparent=True)
        return (fig, ax, c1, c2, cb)

    def plotPdfMap_plume(self, saveName=None, releases=None, level=0,
                         plumeLims=(0.1, None), dateLims=[None, None],
                         freq='H', extent=None, dpi=200):
        """
        Create a pdf with hourly plots about the plume output
        from FLEXPART. The pdf will be saved in the output directory.

        Input:
        - saveName      Name to use when saving the pdf.
        - releases      Defines the range of releases to be plotted.
                        (NOT IMPLEMENTED YET)
        - level         Defines the height level to plot.
                        By defect is the lowest: 0.
        - plumeLims     Defines the limits values for the 
                        source-receptor sensitivity colorbar.
        - dateLims      Defines the date range to plot
        - freq          Defines the frequency of maps
                        'H', '2H', etc. for hour-based intervals
                        'T', '2T', etc. for minute-based intervals
        - extent        Define the map limits. Should be a list with
                        format [lon_min, lon_max, lat_min, lat_max].
                        By default it will use all points available.
        """
        # Retrieve metaData
        dates, hgt, lat, lon, releases = self.ncDataMeta
        # ADD RELEASES RESTRICTION
        # Define the date range (Assuming it's backwards)
        if dateLims[0]:
            dateLims[0] = pd.to_datetime(dateLims[0])
        else:
            dateLims[0] = pd.to_datetime(dates[-1])
        if dateLims[1]:
            dateLims[1] = pd.to_datetime(dateLims[1])
        else:
            dateLims[1] = pd.to_datetime(dates[0])
        dateRange = pd.date_range(dateLims[0], end=dateLims[1], freq=freq)
        # Open a pdf
        if not saveName:
            saveName = f'quickMap_plume_{int(hgt[level])}m.pdf'
        with PdfPages(self.outputDir+saveName) as pdf:
            # Iterate over date range
            for date in dateRange:
                # Call 'plotMap_plume'
                figData = self.plotMap_plume(date, level=level,
                                             releases=releases,
                                             extent=extent, dpi=dpi,
                                             plumeLims=plumeLims)
                # Tighthen it and save to pdf
                pdf.savefig(dpi=200, bbox_inches='tight', transparent=True)
                # Close the existing figure to avoid memory overload
                plt.close()


def reduce_netcdf(runDirs):
    """
    Iterates over a list of FLEXPART simulations directories,
    looks for the output directory and the netCDF output file.
    Then it resave the netCDF with only the airtracer data to
    allow for easy acces later on. 

    Assumes that the directories listed in 'runDirs' are 
    absolute paths to the FLEXPART simulations directories. 
    The new output directory will be created in the 'runDirs'
    parent directory.
    """
    # == Find the netCDF files ==================================
    # Iterate over them finding the nc files
    filesPaths = []
    for folder in runDirs:
        files = os.listdir(f'{folder}/')
        # Take only files ending in .nc
        files = [file for file in files if file.endswith('.nc')]
        # Add the path
        filesPaths.append(f'{folder}/{files[0]}')

    # == Prepare the output dir =================================
    # 'Normalize' the path and find the parent directory
    rootDir = os.path.abspath(runDirs[0])
    rootDir = os.path.dirname(os.path.dirname(rootDir))
    # Create the output directory
    outputDir = os.path.abspath(rootDir+'/output_processed/')
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    # == Clean the files ========================================
    # Iterate over files
    print(f'{len(filesPaths)} netCDF files to be processed:')
    newFiles = []
    for i, f in enumerate(filesPaths):
        print(f' Processing file {i+1}...')
        data = xr.open_dataset(f)
        data = data['spec001_mr']
        print(f'  Saving file {i+1}...')
        newFile = f'{outputDir}/FPOutput_{str(i).zfill(3)}.nc'
        data.to_netcdf(newFile, mode='w')
        newFiles.append(newFile)
        print(f'  Closing the file.')
        data.close()
    # Return the files
    return newFiles


def combine_netcdf(filesList):
    """
    Combine the netCDF in 'filesList' into a single netCDF file.

    This function should be used with the list of files returned
    by 'reduce_netcdf'
    """
    # == Prepare the output dir =================================
    # Find the parent directory
    outputDir = os.path.dirname(filesList[0])

    # == Combine the data files =================================
    # Load with open_mfdataset
    data = xr.open_mfdataset(filesList, concat_dim='pointspec',
                             parallel=True)
    # Save the new data and close the file
    print('\nCombining the files. \nPlease wait, this may take some time...')
    nc = data.to_netcdf(f'{outputDir}/FPOutput_merged.nc',
                        mode='w', compute=False)
    with ProgressBar():
        results = nc.compute()
    print(' Done.')
    data.close()


def testing():
    """
    A bunch of testing code.

    Uncomment what you need to test.
    """

    # # == Load simple trajectories data =================================
    # runDir = 'testData/output_07_MultipleTrajectories/output/'
    # FPOut = FLEXPARTOutput(runDir)
    # # Load simple trajectories
    # FPOut.load_trajectories()
    # print(FPOut.trajDataMeta.info())
    # print(FPOut.trajData.info())
    # # Return output
    # return FPOut

    # # == Simple plots ===========================================
    # runDir = 'testData/output_07_MultipleTrajectories/output/'
    # FPOut = FLEXPARTOutput(runDir)
    # FPOut.load_trajectories()
    # # Make a plot
    # fig, ax = FPOut.plotMap_traj()
    # ax.set_title('Complete Plot')
    # # Add plots with things
    # fig, ax = FPOut.plotMap_traj(releases=list(range(1, int(116/2))))
    # ax.set_title('First Half Plot')
    # fig, ax = FPOut.plotMap_traj(releases=list(range(int(116/2), 117)))
    # ax.set_title('Last Half Plot')

    # # == Manage dates ===========================================
    # runDir = 'testData/output_07_MultipleTrajectories/output/'
    # FPOut = FLEXPARTOutput(runDir)
    # FPOut.load_trajectories()
    # # Check releases range
    # dateRange = FPOut.get_traj_dateRange(show=True)
    # print(dateRange)
    # # Restrict the releases range
    # dateLims = ['2017-08-28 00:00', '2017-08-28 02:00']
    # dateRange = FPOut.get_traj_dateRange(show=True, dateLims=dateLims)
    # print(dateRange)

    # # == Folium maps ============================================
    # runDir = 'testData/output_07_MultipleTrajectories/output/'
    # FPOut = FLEXPARTOutput(runDir)
    # FPOut.load_trajectories()
    # # Check releases range
    # dateRange = FPOut.get_traj_dateRange(show=True)
    # # Plot folium map
    # m = FPOut.plotFoliumMap_traj()
    # m.save(runDir+'map_0.html')
    # # Restrict the releases range
    # dateLims = ['2017-08-28 00:00', '2017-08-28 02:00']
    # dateRange = FPOut.get_traj_dateRange(show=True, dateLims=dateLims)
    # m = FPOut.plotFoliumMap_traj(releases=dateRange.keys())
    # m.save(runDir+'map_1.html')

    # # == Single netcdf maps =====================================
    # runDir = 'testData/output_07_MultipleTrajectories/output/'
    # FPOut = FLEXPARTOutput(runDir)
    # FPOut.load_netcdf()
    # # Default single plume
    # figData = FPOut.plotMap_plume('2017-08-28 08:00',
    #                               savePath='map_plume_0')
    # # Single plume with changes
    # figData = FPOut.plotMap_plume('2017-08-28 08:00', level=1,
    #                               plumeLims=(0.001, None),
    #                               extent=[-40, -15, 0, 20],
    #                               savePath='map_plume_0', dpi=1000)
    # # Return output
    # return FPOut

    # # == PDF maps =================================================
    # runDir = 'testData/output_07_MultipleTrajectories/output/'
    # FPOut = FLEXPARTOutput(runDir)
    # FPOut.load_netcdf()
    # # Plot quicklook with limits
    # dateLims = ['2017-08-28 12:00', '2017-08-28 13:00']
    # FPOut.plotPdfMap_plume(
    #     saveName='map_2017-08-28-1200.pdf', dateLims=dateLims)
    # # Plot quicklook without limits
    # FPOut.plotPdfMap_plume(saveName='map_Full.pdf')
    # # Plot a pdf map with 5 minutes data of one hour
    # dateLims = ['2017-08-28 12:00', '2017-08-28 13:00']
    # freq = '5T'
    # extent = [-45, 30, -15, 45]
    # FPOut.plotPdfMap_plume(saveName='map_5Min_limited.pdf', dateLims=dateLims,
    #                        freq=freq, extent=extent)
    # # Return output
    # return FPOut

    # # == Combining trajectories files =============================
    # runDir = 'D:/Datos/0 - Trabajo/FLEXPART/Mistral_RunsIsi/CAFE_F13_splitted/'
    # FPOut = FLEXPARTOutput(runDir)
    # # Try to load a single file (this should fail)
    # try:
    #     FPOut.load_trajectories()
    # except:
    #     print('Could not find the trajectories file')
    # # Look for the FLEXPART simulations directory
    # FPDirs = [f for f in os.listdir(runDir) if f.startswith('Flight')]
    # FPDirs = [f'{runDir}/{FPdir}/output/' for FPdir in FPDirs]
    # # Call for 'combine_trajectories'
    # outputDir = FPOut.combine_trajectories(FPDirs,runDir)
    # # Try to load again from the processed directory
    # FPOut.load_trajectories(outputDir)
    # # Print results
    # FPOut.trajData.info()
    # FPOut.trajDataMeta.info()
    # print(FPOut.trajData['j'].unique())
    # # Return output
    # return FPOut

    # # == Merging netCDF =========================================
    # # Directory where simulations are stored
    # rootDir = 'D:/Datos/0 - Trabajo/FLEXPART/Mistral_RunsIsi/CAFE_F13_splitted/'
    # # Find directories
    # FPDirs = os.listdir(rootDir)
    # # Take only those that are directories
    # FPDirs = [f for f in FPDirs if f.startswith('Flight')]
    # # Build the absolute path
    # FPDirs = [os.path.abspath(f'{rootDir}{f}') for f in FPDirs]
    # # Reduce files
    # newFiles = reduce_netcdf(FPDirs)
    # # Call 'combine_netcdf'
    # combine_netcdf(newFiles)

    # return FPOut


if __name__ == '__main__':
    print('Ready to go!')
    FPOut = testing()
