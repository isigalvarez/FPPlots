# !usr/bin/env python3
# ===========================================================
# Created on 24/04/2019
# This script is a wrapper for 'FLEXPARTRun' and 'FlighData'
# classes. It uses both of them to configure a FLEXPART run.
# ===========================================================

from FlightData import FlightData
from FLEXPARTRun import FlexpartRun
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath("/home/isi/GitHub/FPPlots/"))

# == Define parameters ======================================
# Path to flight
flightPath = '/home/isi/FLEXPART/CAFE_flightData/Flight13_ITCZ_2017-08-31.csv'
# Path to FLEXPART dirs
runDir = '/home/isi/FLEXPART/flexpart10_git/Runs/FPRun_02/'
flexpartDir = '/home/isi/FLEXPART/flexpart10_git/'
meteoDir = '/home/isi/FLEXPART/Meteo/ECMWF/20170829_EA'
# ===========================================================

# == Extract info from the flight ===========================
# Initialize the flight
FD = FlightData(flightPath)
# Extract releases and command
releases = FD.gen_RELEASES('5min')
command = FD.gen_COMMAND()
# ===========================================================

# == Prepare the FLEXPART run ===============================
# Initialize the FLEXPART class
FP = FlexpartRun((runDir, flexpartDir, meteoDir))
# Prepare the COMMAND and RELEASES files
FP.write_COMMAND(command)
FP.write_RELEASES(releases)
# Check the particles if needed
n_particles = FP.print_totalparticles()
if n_particles:
    FP.change_particlesNumber(n_particles)
# Prepare OUTGRID
FP.write_OUTGRID()
# Copy the FLEXPART executable
FP.prepare_Run()
# ===========================================================