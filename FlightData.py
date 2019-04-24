# !usr/bin/env python3
# ===========================================================
# Created on 24/04/2019
# This script aims to extract flight data and use it to
# prepare a flexpart run considering release points along
# the flight path data.
# ===========================================================

import os
import numpy as np
import pandas as pd
import datetime as dt


def testing():
    """
    This is a wrapper for several tests for FlighData class.
    """
    # Initialize an instace of the class and show the data
    FD = FlightData(
        '/home/isi/FLEXPART/CAFE_flightData/Flight13_ITCZ_2017-08-31.csv')
    print(FD.data)
    # Resample to 5 min


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
        # Initialize the dataframe and load the data
        self.data = pd.DataFrame()
        self.loadData()

    def loadData(self):
        """
        This method extracts data from the csv file.

        The file should have a first line with headers:
        - Date  Date and hour of the location
        - lat   Latitude in degrees
        - long  Longitude in degrees
        - pres  Pressure in hPa
        - alt   Altitude in metes
        and the data stored in that order.
        """
        # Load and save the file
        self.data = pd.read_csv(self.filePath,
                                parse_dates=['Date'],
                                index_col=['Date'])

    def gen_RELEASES(self, timeStep='5Min'):
        """
        This method resamples the flightData to a provided
        timestep. The first point will always be used.

        timeStep should be a string readable by pandas as
        'XMin'. This will resample to 'X' minutes long intervals
        doing the mean to compute the resampled values.

        Returns a list of dictionaries to configure a RELEASES
        file for a FLEXPART simulation.
        """
        # Resample the dataframe
        df = self.data.resample(timeStep).mean()
        # Initialize the list of dicts
        releases = []
        # Iterate over rows
        for idx, row in df.iterrows():
            # Initialize the dict
            release = {}
            # Save the start and end date and hour
            release['IDATE1'] = idx.strftime('%Y%m%d')
            release['iTIME1'] = idx.strftime('%H%M%S')
            release['IDATE2'] = idx.strftime('%Y%m%d')
            release['iTIME2'] = idx.strftime('%H%M%S')
            # Save the release location
            release['LON1'] = row['long']
            release['LON2'] = row['long']
            release['LAT1'] = row['lat']
            release['LAT2'] = row['lat']
            release['Z1'] = row['altit']
            release['Z2'] = row['altit']
            # Save a comment
            release['COMMENT'] = f'Flight Position at: {idx.strftime("%Y-%m-%d %H:%M")}'
            # Append to the list
            releases.append(release)
        # return the releases list of dicts
        return releases

    def gen_COMMAND(self, time_before=72, time_after=1):
        """ 
        This method generates a COMMAND file for FLEXPART.

        It will include all flight data points and a buffer time
        before and after the flight.

        By defect, the simulation will be backwards oriented:
        - 'time_before' especifies how many hours after the flight
        begins will be simulated.
        - 'time_after' especifies how many hours before the flight 
        ends will be simulated.
        """
        # Extract the first and last dates
        firstDate = (self.data.index[0] -
                     pd.Timedelta(hours=time_before)).floor('H')
        lastDate = (self.data.index[-1] +
                    pd.Timedelta(hours=time_after)).ceil('H')
        # Create the dict for COMMAND
        command = {'IBDATE': firstDate.strftime('%Y%m%d'),
                   'IBTIME': firstDate.strftime('%H%M%S'),
                   'IEDATE': lastDate.strftime('%Y%m%d'),
                   'IETIME': lastDate.strftime('%H%M%S')}
        # return the command dict
        return command


def extract_BahamasData_1min():
    """
    This function takes in the file with al Bahamas data with 1
    minute resolution and separates it in different files, one 
    for each flight.
    """
    # == Parameters =============================================
    # Data filename
    fileName = '/home/isi/FLEXPART/CAFE_flightData/BahamasData_1min.txt'
    # Dictionary with fligth number as key and the parameters:
    #   Name, Start-Date
    flightParams = {'03': ['Transfer', '2017-08-07'],
                    '04': ['BBfresh', '2017-08-10'],
                    '05': ['BBaged', '2017-08-12'],
                    '06': ['North', '2017-08-15'],
                    '07': ['Stack1', '2017-08-17'],
                    '08': ['Stack2', '2017-08-19'],
                    '09': ['Ghana', '2017-08-22'],
                    '10': ['EuropeanAfrican', '2017-08-24'],
                    '11': ['Stack3', '2017-08-26'],
                    '12': ['BiomassProfile', '2017-08-29'],
                    '13': ['ITCZ', '2017-08-31'],
                    '14': ['OutflowHurrikan', '2017-09-02'],
                    '15': ['ITCZ2', '2017-09-04']}
    # ===========================================================

    # == Load data ==============================================
    # Call read_csv
    df = pd.read_csv(fileName)
    # Create a datetime
    date = pd.to_datetime(df['Time'], unit='D',
                          origin=pd.Timestamp('2017-01-01'))
    # Modify the format
    date = pd.to_datetime(date.dt.strftime('%Y-%m-%d %H:%M'))
    # Set the date as index and change its name
    df.set_index(date, inplace=True)
    df.index.names = ['Date']
    # ===========================================================

    # == Save separate data =====================================
    # Iterate over params
    for key in flightParams.keys():
        # extract start date
        start = pd.to_datetime(flightParams[key][1])
        # Take a portion of the dataframe
        df_temp = df.loc[start:start+dt.timedelta(days=1)]
        # Create a savename and save the data
        name = flightParams[key][0]
        date = start.strftime("%Y-%m-%d")
        name = f'testData/BahamasData/Flight{key}_{name}_{date}.csv'
        df_temp.to_csv(name)
    # ===========================================================


if __name__ == '__main__':
    print('\nReady to go!\n')
    testing()
