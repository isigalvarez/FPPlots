# # !usr/bin/env python3
# ===========================================================
# Created on 07/05/2019
# Test to use xarray to manage netCDF4 output
# ===========================================================

import os

import numpy as np
import pandas as pd
import xarray as xr

# == Define Parameters ======================================
# Directory where simulations are stored
rootDir = 'D:/Datos/0 - Trabajo/FLEXPART/Mistral_RunsIsi/CAFE_F13_splitted/'

# == Find files =============================================
# Find directories
FPDirs = os.listdir(rootDir)
# Take only those that are directories
FPDirs = [f for f in FPDirs if f.startswith('Flight')]
# Build the absolute path
FPDirs = [os.path.abspath(f'{rootDir}{f}') for f in FPDirs]
# Iterate over them finding the nc files
filesPaths = []
for folder in FPDirs:
    files = os.listdir(f'{folder}/output/')
    # Take only files ending in .nc
    files = [file for file in files if file.endswith('.nc')]
    # Add the path
    filesPaths.append(f'{folder}/output/{files[0]}')

# == Merging data - Option 1 ================================
## Step by step. This tooks about 5-7 minutes to complete
## sometimes gives a memory error
# Open individual datasets
datasets = [xr.open_dataset(file) for file in filesPaths]
# Take only the relevant variable
datasets = [data['spec001_mr'] for data in datasets]
# Concat the datasets along releases (pointspec)
merged = datasets[0]
for dataset in datasets[1:]:
    merged = xr.concat([merged,dataset], 'pointspec')
# Save them to a new netCDF4
fileMerged = f'{rootDir}/merged_v1.nc'
merged.to_netcdf(fileMerged)
# Close everything
merged.close()
for data in datasets:
    data.close()

# == Merging data - Option 6 ================================
## Open them one by one, extract only numpy arrays, concatenate
## them and then save them in a new netCDF file. Then use 
## open_mfdataset on the cleaned files
# Iterate over files
print(f'Cleaning {len(filesPaths)} netCDF files...')
newFiles = []
for i,f in enumerate(filesPaths):
    print(f' Loading and cleaning file {i+1}...')
    data = xr.open_dataset(f)
    data = data['sepc001_mr']
    print(f' Saving file {i+1}...')
    data.to_netcdf(f'{rootDir}output/file_{str(i).zfill(3)}')
    newFiles.append(f)
    print(f' Closing the file...')
    data.close()
# Reload with open_mfdataset
data = xr.open_mfdataset(newFiles, concat_dim='pointspec',
                         parallel=True)


# == Merging data - Option 5 ================================
## Open them one by one, extract only what's needed and resave
## them in a new netCDF file. Then use open_mfdataset on the
## cleaned files.
    # This works, takes only 5-7 minutes and its more memory
    # efficient.
# Iterate over files
print(f'Cleaning {len(filesPaths)} netCDF files...')
newFiles = []
for i,f in enumerate(filesPaths):
    print(f' Loading and cleaning file {i+1}...')
    data = xr.open_dataset(f)
    data = data['spec001_mr']
    print(f' Saving file {i+1}...')
    newFile = f'{rootDir}output/file_{str(i).zfill(3)}.nc'
    data.to_netcdf(newFile)
    newFiles.append(newFile)
    print(f' Closing the file...')
    data.close()
# Reload with open_mfdataset
print('Cleaning done. Opening the file...')
data = xr.open_mfdataset(newFiles, concat_dim='pointspec',
                         parallel=True)
# Save the new data and close the file
data.to_netcdf(f'{rootDir}output/files_merged.nc')
data.close()


# == Merging data - Option 4 ================================
## Combine them one by one, closing files to preserve memory
    # This worked but took more than 20 minutes.
# Iterate over files
print(f'Merging {len(filesPaths)} netCDF files...')
for i,f in enumerate(filesPaths):
    # Load the first file into the final dataset
    if i == 0:
        print(f' Loading file {i+1}...')
        merged = xr.open_dataset(f)
        merged = merged['spec001_mr']
    # Open a new dataser and combine them with the previous
    else:
        print(f' Loading file {i+1}...')
        newData = xr.open_dataset(f)
        newData = newData['spec001_mr']
        print(f'  Adding file {i+1}...')
        merged = xr.concat([merged,newData],'pointspec')
        print('  Done. Closing file...')
        newData.close()
print('All files merged. Saving to directory...')
# Save them to a new netCDF4 and close
fileMerged = f'{rootDir}/merged_v2.nc'
merged.to_netcdf(fileMerged)
merged.close()

# == Merging data - Option 3 ================================
## Combine the two, merged those that are identical with
    # Does not work. It gets confused with variables
# open_mfdataset and then do a simpler concat.
data = xr.open_mfdataset(filesPaths[:-1], concat_dim='pointspec',
                         parallel=True,data_vars=['spec001_mr'],
                         coords='minimal')
    # Does not work. It gets confused with variables

# == Merging data - Option 2 ================================
## Using open_mfdataset parallelization
    # Does not work. It gets confused with numpoint and pointspec dimensions
data = xr.open_mfdataset(filesPaths, concat_dim='pointspec',
                         data_vars='spec001_mr',parallel=True)


