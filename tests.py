
import os
import sys
import shutil
import errno
import subprocess
import f90nml

sys.path.append(os.path.abspath("/home/isi/GitHub/FPPlots/"))
from FLEXPARTRun import *

dirPath = '/home/isi/FLEXPART/flexpart10_git/Runs/FPRun_02/'
flexpartPath = '/home/isi/FLEXPART/flexpart10_git/'
meteoPath = '/home/isi/FLEXPART/Meteo/ECMWF/20170829_EA'
params = [  { 'IDATE1': 20170831, 'ITIME1': 105900,
                'IDATE2': 20170831, 'ITIME2': 110000,
                'LON1': -22.981, 'LON2': -22.952,
                'LAT1': 16.786, 'LAT2': 16.787,
                'Z1': 833.51, 'Z2': 833.52,
                'ZKIND': 1, 'MASS': 100000000.0,
                'PARTS': 1000, 'COMMENT': 'RELEASE 1'},
            {   'IDATE1': 20170831, 'ITIME1': 115900,
                'IDATE2': 20170831, 'ITIME2': 120000,
                'LON1': -23.981, 'LON2': -23.952,
                'LAT1': 17.786, 'LAT2': 17.787,
                'Z1': 833.51, 'Z2': 833.52,
                'ZKIND': 1, 'MASS': 100000000.0,
                'PARTS': 1000, 'COMMENT': 'RELEASE 1'}]
# Initialize the run
FPRun = FlexpartRun((dirPath,flexpartPath,meteoPath))
FPRun.prepareFiles()
FPRun.write_COMMAND()
FPRun.write_OUTGRID()
FPRun.write_RELEASES(params)
