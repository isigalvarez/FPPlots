# !usr/bin/env python3
# ===========================================================
# Created on 18/04/2019
# This script extract individual flight data from the file
# 'BahamasData_1min.txt'.
# ===========================================================

import os
import numpy as np
import pandas as pd
import datetime as dt

# == Parameters =============================================
# Data filename
fileName = 'testData/BahamasData/BahamasData_1min.txt'
# fligt parameters
# Dictionary with fligth number as key and the following
# parameters:
#   Name, Start Date
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
# Create a datetime (including leap years!)
date = pd.to_datetime(df['Time'], unit='D')+dt.timedelta(days=47*365+11)
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
