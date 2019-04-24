
from FLEXPARTRun import FlexpartRun
import os
import sys
import shutil
import errno
import subprocess
import f90nml
import pandas as pd

sys.path.append(os.path.abspath("/home/isi/GitHub/FPPlots/"))

# == Extracting dates from available ==================================
meteoDir = '/home/isi/FLEXPART/Meteo/ECMWF/20170829_EA'
# Open the AVAILABLE file
df = pd.read_csv(f'{meteoDir}/AVAILABLE', skiprows=3, dtype='str',
                 header=None, sep='\s+', usecols=[0, 1])
# Create the date
date = pd.to_datetime(df[0]+df[1])
# extract the limits
firstDate = date.min()
lastDate = date.max()
# =====================================================================

# == Generating a COMMNAD dict =======================================
# Define parameters
time_before = 72
time_after = 1
# Load the data
filePath = '/home/isi/FLEXPART/CAFE_flightData/Flight13_ITCZ_2017-08-31.csv'
df = pd.read_csv(filePath, parse_dates=['Date'], index_col=['Date'])
# Extract the first and last dates
firstDate = (df.index[0] - pd.Timedelta(hours=time_before)).floor('H')
lastDate = (df.index[-1] + pd.Timedelta(hours=time_after)).ceil('H')
# Create the dict for COMMAND
command = {'IBDATE': firstDate.strftime('%Y%m%d'),
           'IBTIME': firstDate.strftime('%H%M%S'),
           'IEDATE': lastDate.strftime('%Y%m%d'),
           'IETIME': lastDate.strftime('%H%M%S')}
# =====================================================================

# == Generating a RELEASES list =======================================
# Load the data
filePath = '/home/isi/FLEXPART/CAFE_flightData/Flight13_ITCZ_2017-08-31.csv'
df = pd.read_csv(filePath, parse_dates=['Date'], index_col=['Date'])
# Resample
df_5min = df.resample('5Min').mean()
# Initialize the list of dicts
releases = []
# Iterate over rows
for idx, row in df_5min.iterrows():
    # Initialize the dict
    release = {}
    # Save the start and end date and hour
    release['IDATE1'] = int(idx.strftime('%Y%m%d'))
    release['iTIME1'] = int(idx.strftime('%H%M%S'))
    release['IDATE2'] = int(idx.strftime('%Y%m%d'))
    release['iTIME2'] = int(idx.strftime('%H%M%S'))
    # Save the release location
    release['LON1'] = row['long']
    release['LON2'] = row['long']
    release['LAT1'] = row['lat']
    release['LAT2'] = row['lat']
    release['Z1'] = row['altit']
    release['Z2'] = row['altit']
    # Save a comment
    release['COMMENT'] = f'"Flight Position at: {idx.strftime("%Y-%m-%d %H:%M")}"'
    # Append to the list
    releases.append(release)
# =====================================================================

# == Testing os.symlink() =============================================
dirPath = '/home/isi/FLEXPART/flexpart10_git/Runs/FPRun_02/'
flexpartPath = '/home/isi/FLEXPART/flexpart10_git/'
# We want to create a simlink to FLEXPART inside the simulation root
# folder 'FPRun_02'.
os.symlink(flexpartPath+'src/FLEXPART', dirPath+'FLEXPART')
# =====================================================================

# == Testing the namelist creation ====================================
dirPath = '/home/isi/FLEXPART/flexpart10_git/Runs/FPRun_02/'
flexpartPath = '/home/isi/FLEXPART/flexpart10_git/'
meteoPath = '/home/isi/FLEXPART/Meteo/ECMWF/20170829_EA'
params = [{'IDATE1': 20170831, 'ITIME1': 105900,
           'IDATE2': 20170831, 'ITIME2': 110000,
           'LON1': -22.981, 'LON2': -22.952,
           'LAT1': 16.786, 'LAT2': 16.787,
           'Z1': 833.51, 'Z2': 833.52,
           'ZKIND': 1, 'MASS': 100000000.0,
           'PARTS': 1000, 'COMMENT': 'RELEASE 1'},
          {'IDATE1': 20170831, 'ITIME1': 105900,
           'IDATE2': 20170831, 'ITIME2': 110000,
           'LON1': -22.981, 'LON2': -22.952,
           'LAT1': 16.786, 'LAT2': 16.787,
           'Z1': 833.51, 'Z2': 833.52,
           'ZKIND': 1, 'MASS': 100000000.0,
           'PARTS': 1000, 'COMMENT': 'RELEASE 1'}]
# Initialize the run
FPRun = FlexpartRun((dirPath, flexpartPath, meteoPath))
FPRun.write_COMMAND()
FPRun.write_OUTGRID()
FPRun.write_RELEASES(params)
# Create a copy of the existing RELEASES filename
shutil.copy(dirPath+'options/RELEASES', dirPath+'options/RELEASES.original')
# Open a namelsit with f90nml
nml = f90nml.read(dirPath+'options/RELEASES.original')
# Change something
for param in params:
    for key in param.keys():
        nml['releases'][key] = param[key]
# Write the change
nml.write(dirPath+'options/RELEASES_temp')
os.replace(dirPath+'options/RELEASES_temp', dirPath+'options/RELEASES')
# =====================================================================
