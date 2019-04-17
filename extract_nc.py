# !usr/bin/env python3
# ===========================================================
# 16/04/2019
# This script is a first aproximation to extract flexpart
# output information using python
# ===========================================================

import os
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from netCDF4 import Dataset
from matplotlib.backends.backend_pdf import PdfPages
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

# == Extract Data ===========================================
def extract_nc(filePath):
    '''
    This function extract the airtracer variable from a 
    netCDF4 file generated by FLEXPART.

    It return a tuple containing the time, height, latitude,
    longitude and the airtracer data. 
    The airtracer is an array with 4 dimensions related to time,
    latiude and longitude, in that order. 
    '''
    # Create a dataset
    data = Dataset(filePath)
    # Extract the variables
    # (!) To see the keys use data.variables.keys()
    time_nc = data.variables['time']
    lon_nc = data.variables['longitude']
    lat_nc = data.variables['latitude']
    hgt_nc = data.variables['height']
    airtracer_nc = data.variables['spec001_mr']
    # <= Here is the place to add more variables to extract

    # Data comes in a class called 'netCDF4._netCDF4.Variable',
    # we just need an array.
    time = time_nc[:]
    lon = lon_nc[:]
    lat = lat_nc[:]
    hgt = hgt_nc[:]
    airtracer = airtracer_nc[0, 0, :]  # First two dims are irrelevant
    # Return data
    return (time, hgt, lat, lon, airtracer)
# ===========================================================

# == Plot Data ==============================================
def plotMap_contour(lat,lon,data,fsize=(12, 10)):
    '''
    This function plots a simple map to take a quick look 
    about some datapoints. 
    '''
    # Create figure and axes
    fig = plt.figure(figsize=fsize)
    ax = plt.axes(projection=ccrs.PlateCarree())
    # Find and stablish its limits
    lon_max = np.ceil(lon.max())
    lon_min = np.floor(lon.min())
    lat_max = np.ceil(lat.max())
    lat_min = np.floor(lat.min())
    ax.axis([lon_min, lon_max, lat_min, lat_max])
    # Draw coastlines
    ax.coastlines('50m', linewidth=1, color='black')
    # Prepare the grid
    gd = ax.gridlines(crs=ccrs.PlateCarree(),draw_labels=True,
                        )
    gd.xlabels_top = False  # Take out upper labels
    gd.ylabels_right = False  # Take out right labels
    gd.xformatter = LONGITUDE_FORMATTER  # Format of lon ticks
    gd.yformatter = LATITUDE_FORMATTER  # Format of lat ticks
    gd.
    # Plot the data and show it
    ax.contour(lon,lat,data)
    # return the figure just in case
    return (fig,ax)
# ===========================================================

# == Save plotted data to pdf ===============================
def savePlot_toPDF(time,hgt,lat,lon,data):
    '''
    This function will iteratively plot data on a map over a
    time and height series and save the plots to a pdf.

    'time'  list of timesteps in seconds
    'hgt'   list a heights in meters
    'lat'   list of latitude points
    'lon'   list of longitude points
    'data'  Contains the data to be plotted. It should be an
            array with dimensions (time,hgt,lat,lon)
    '''
    # Display something
    print('Printing figures!')
    # Iterate over heights
    for idx_h in range(len(hgt)):
        # Build the name for the pdf
        savePDF = f'mapPDF_height-{hgt[idx_h]}.pdf'
        # Start a new pdf
        with PdfPages(savePDF) as pdf:
            # Iterate over time
            for idx_t in range(len(time)):
                # Call the function
                fig,ax = plotMap_contour(lat,lon,data[idx_t,idx_h,:,:])
                ax.set_title(f'{time[idx_t]} s from the beginning')
                # Save to pdf 
                pdf.savefig()
                # Close the existing figure
                plt.close()
    # Say that you're done
    print('Done!')
# ===========================================================

if __name__ == '__main__':
    # == Define parameters ==================================
    # Path to some grid files
    dataPath = 'testData/output_03_MassPlumeTrajectories_netCDF/'
    # =======================================================

    # == Find data files ====================================
    # First we extract all the files inside output dir
    files_all = os.listdir(dataPath)
    # Take only files ending with '.nc'
    files_nc = [f for f in files_all if f.endswith('.nc') == True]
    # Choose the file
    filePath = dataPath + files_nc[0]
    # =======================================================

    # == Extract the data ===================================
    # Call 'extract_nc'
    time,hgt,lat,lon,data = extract_nc(filePath)
    # Call 'plotMap_contour' to check that it works
    fig, ax = plotMap_contour(lat,lon,data[77,1,:,:])
    # Call 'savePlot_toPDF'
    time = time[:10]
    savePlot_toPDF(time,hgt,lat,lon,data)

