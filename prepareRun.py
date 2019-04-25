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


def main():
    """
    Wrapper that calls 'prepareSingleRun' iteratively.
    """
    # == Define parameters ======================================
    # Directory where flighst are stored
    flightsDir = '../../FLEXPART/CAFE_flightData/'
    # Directory where runfiles will be created
    runsDir = '../../FLEXPART/flexpart10_git/Runs/CAFE/'
    # Paths to FLEXPART and meteo dirs
    flexpartDir = '../../FLEXPART/flexpart10_git/'
    meteoDir = '../../FLEXPART/Meteo/ECMWF/20170829_EA/'
    # ===========================================================

    # == Iterate over flight files ==============================
    # Look for flights
    flights = os.listdir(flightsDir)
    flights = [flight for flight in flights if flight.startswith('Flight')]
    flights.sort()
    # Iterate over files
    results = {}
    for flight in flights:
        flightID = flight.split('.')[0].split('_')[0]
        results[flightID] = prepareSingleRun(flightsDir+flight,
                                             runsDir+flightID,
                                             flexpartDir, meteoDir)
    # ===========================================================
    return results

def prepareSingleRun(flightPath, runDir, flexpartDir, meteoDir):
    """
    Prepares a single FLEXPART Run based on a flight file.
    """
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
    # Prepare the COMMAND, RELEASES and OUTGRID files
    FP.write_COMMAND(command)
    FP.write_RELEASES(releases)
    FP.write_OUTGRID()
    # Check the particles
    FP.change_particlesNumber(FP.check_totalParticles())
    FP.check_totalParticles()
    # Check meteo encapsulation
    FP.check_meteoRange()
    # Copy the FLEXPART executable
    FP.prepare_Run()
    # ===========================================================

    # == Return classes =========================================
    return (FD, FP)


if __name__ == '__main__':
    print("\nLet's go!")
    results = main()
