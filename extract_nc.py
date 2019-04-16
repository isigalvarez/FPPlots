#!usr/bin/env python3
# ===========================================================
# 16/04/2019
# This script is a first aproximation to extract flexpart
# output information using python
# ===========================================================

import os
import netCDF4

# == Define parameters ======================================
# Path to some grid files
dataPath = 'testData/output_03_MassPlumeTrajectories_netCDF/'
# ===========================================================

# == Find data files ========================================
# First we extract all the files inside output dir
files_all = os.listdir(dataPath)
# Separate them in 'conc', 'time' and 'partpos'
files_nc = [f for f in files_all if f.endswith('.nc') == True]
# ===========================================================

# == Extract Data ===========================================
# Choose the file
filePath = dataPath + files_nc[0]
# Create a dataset
data = netCDF4.Dataset(filePath)
# Extract the variables
# (!) To see the keys use data.variables.keys()
time_nc = data.variables['time']
lon_nc = data.variables['longitude']
lat_nc = data.variables['latitude']
hgt_nc = data.variables['height']
airmass_nc = data.variables['spec001_mr']
# Data comes in a class called 'netCDF4._netCDF4.Variable',
# we just need an array.
time = time_nc[:]
lon = lon_nc[:]
lat = lat_nc[:]
hgt = hgt_nc[:]
airmass = airmass_nc[:]
# ===========================================================
