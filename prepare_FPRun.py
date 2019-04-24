# !usr/bin/env python3
# ===========================================================
# Created on 24/04/2019
# This script aims to extract flight data and use it to
# prepare a flexpart run considering release points along
# the flight path data.
# ===========================================================

import os

def testing():
    """
    This is a wrapper for several tests for FlighData class.
    """
    FD = FlightData('/home/isi/FLEXPART/CAFE_flightData/Flight13_ITCZ_2017-08-31-09-57-40.txt')

class FlightData:
    """
    This is a class to handle fligt data. Needs a path to 
    csv file where the flight data is stored.
    """

    def __init__(self, filePath):
        """
        Initialize parameters. Needs a path to csv file where 
        the flight data is stored.
        """
        # Store path to file
        self.filePath = os.path.abspath(filePath)
        # Initialize the starting locations
        self.startLocs = []

    def loadData(self):
        """
        This function extracts data from the csv file.
        
        The file should have a first line with headers:
            secs_after_start, lat, lon, pres, alt
        and the data stored in that order.
        """
        # Initialize the variables
        startLocs = []
        # Open the file
        with open(self.filePath,'r') as f:
            # Loop over the lines
            for i,line in enumerate(f):
                # Split the line by its commas
                line = line.split(',')
                # The first line are headers, we ignore them
                if (i != 0):
                    if (float(line[0])%3600 == 0):
                        # Build the locations (lat, lon, height)
                        locs = f'{line[1]} {line[2]} {line[4]}'
                        # Append the data
                        startLocs.append(locs)
        # Save the value
        self.startLocs = startLocs

if __name__ == '__main__':
    print('\nReady to go!\n')
    testing()