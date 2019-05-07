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
import matplotlib as mpl
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from seaborn import set_style
from netCDF4 import Dataset, chartostring
from matplotlib.backends.backend_pdf import PdfPages
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


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
        self.ncDataMeta = []
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
            self.ncDataMeta = self.extract_ncMeta()
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
        - df        Dataframe with trajectories data. If None will
                    use the data extracted on initialization.
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

    def get_releases_dateRange(self, releases=None, show=False,
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

    def extract_ncMeta(self):
        '''
        This function extract information about the tracer
        releases from a netCDF4 file generated by FLEXPART.

        It return a tuple containing the time, height, latitude,
        longitude and release comment. 
        '''
        # Open the dataset
        data = self.ncData
        # Extract the variables
        # (!) To see the keys use data.variables.keys()
        time_nc = data.variables['time']
        lon_nc = data.variables['longitude']
        lat_nc = data.variables['latitude']
        hgt_nc = data.variables['height']
        rlsComment_nc = data.variables['RELCOM']
        # <= Here is the place to add more variables to extract

        # Data comes in a class called 'netCDF4._netCDF4.Variable',
        # we just need an array.
        time = time_nc[:]
        lon = lon_nc[:]
        lat = lat_nc[:]
        hgt = hgt_nc[:]
        rlsComment = rlsComment_nc[:]
        # The releases have to be converted
        rlsComment = chartostring(rlsComment)

        # Now we need tro transforme time into dates
        # Get start and end date
        startDate = pd.to_datetime(data.ibdate+data.ibtime)
        endDate = pd.to_datetime(data.iedate+data.ietime)
        # (!) ASSUMING ITS A BACKWARDS SIMULATION
        # 'time' gives the seconds passed since the end date
        # so we add it to 'endDate'
        date = endDate + pd.to_timedelta(time, 'S')

        # Return
        return [date, time, hgt, lat, lon, rlsComment]

    def plotMap_plume(self, date, level=0, releases=None, extent=None,
                      plumeLims=(0, None)):
        """
        Plot a simple plume map from a FLEXPART simulation.

        Input:
        - date      Date to plot in format 'yyyy-mm-dd HH:MM'.
        - level     Defines the height level to plot.
                    By defect is the lowest: 0.
        - extent    Define the map limits. Should be a list with
                    format [lon_min, lon_max, lat_min, lat_max].
                    By default it will use all points available.
        - plumeLims Defines the limits values for the 
                    source-receptor sensitivity colorbar
        """
        # == Prepare data =======================================
        # Retrieve metaData
        dates, time, hgt, lat, lon, releases = self.ncDataMeta
        # Convert input date to datetime
        date = pd.to_datetime(date)
        # Get the requested date index
        idx = dates.get_loc(date, method='nearest')
        # Extract the plume data
        plume = self.ncData.variables['spec001_mr']
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
            levels = np.linspace(pMin, pMax, 10)
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

        return (fig, ax, c1, c2, cb)

    def plotPdfMap_plume(self, saveName=None, releases=None, level=0,
                         plumeLims=(0.1, None), dateLims=[None, None],
                         freq='H', extent=None):
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
        dates, time, hgt, lat, lon, releases = self.ncDataMeta
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
                figData = self.plotMap_plume(date, level=0, releases=None,
                                             extent=None, plumeLims=(0.1, None))
                # Tighthen it and save to pdf
                pdf.savefig(dpi=200, bbox_inches='tight', transparent=True)
                # Close the existing figure to avoid memory overload
                plt.close()


def testing():
    # Define parameters
    runDir = 'testData/output_07_MultipleTrajectories/'
    # Initiate the class
    FPOut = FLEXPARTOutput(runDir)
    # print(FPOut.trajDataMeta.head())
    # print(FPOut.trajData.head())

    # # == Simple plots ===========================================
    # # Make a plot
    # fig, ax = FPOut.plotMap_traj()
    # ax.set_title('Complete Plot')
    # # Add plots with things
    # fig, ax = FPOut.plotMap_traj(releases=list(range(1, int(116/2))))
    # ax.set_title('First Half Plot')
    # fig, ax = FPOut.plotMap_traj(releases=list(range(int(116/2), 117)))
    # ax.set_title('Last Half Plot')

    # # == Manage dates ===========================================
    # # Check releases range
    # dateRange = FPOut.get_releases_dateRange(show=True)
    # print(dateRange)
    # # Restrict the releases range
    # dateLims = ['2017-08-28 00:00', '2017-08-28 02:00']
    # dateRange = FPOut.get_releases_dateRange(show=True, dateLims=dateLims)
    # print(dateRange)

    # # == Folium maps ============================================
    # # Plot folium map
    # m = FPOut.plotFoliumMap_traj()
    # m.save('map_0.html')
    # m = FPOut.plotFoliumMap_traj(releases=dateRange.keys())
    # m.save('map_1.html')

    # == PDF maps =================================================
    # # Plot quicklook with limits
    # dateLims = ['2017-08-28 12:00', '2017-08-28 13:00']
    # FPOut.plotPdfMap_plume(saveName='map_2017-08-28-1200.pdf',dateLims=dateLims)
    # # Plot quicklook without limits
    # FPOut.plotPdfMap_plume(saveName='map_Full.pdf')
    # Plot a pdf map with 5 minutes data of one hour
    dateLims = ['2017-08-28 12:00', '2017-08-28 13:00']
    freq = '5T'
    extent = [-45, 30, -15, 45]
    FPOut.plotPdfMap_plume(saveName='map_5Min_limited.pdf', dateLims=dateLims,
                           freq=freq, extent=extent)
    return FPOut


if __name__ == '__main__':
    print('Ready to go!')
    FPOut = testing()

