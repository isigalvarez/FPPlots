#!usr/bin/env python3
# ===========================================================
# 16/04/2019
# This script is a first aproximation to extract flexpart
# output information using python
# ===========================================================

import os
import struct

# == Define parameters ======================================
# Path to some grid files
dataPath = 'testData/output_02_MassPlumeTrajectories/'
# ===========================================================

# == Classifying data =======================================
# First we extract all the files inside output dir
files_all = os.listdir(dataPath)
# Separate them in 'conc', 'time' and 'partpos'
files_conc = [f for f in files_all if f.startswith('grid_conc') == True]
files_time = [f for f in files_all if f.startswith('grid_time') == True]
files_ppos = [f for f in files_all if f.startswith('partposit') == True]
# ===========================================================

# == Trying to extract info =================================
# Open the last file about particles positions
filePath = dataPath + files_ppos[-1]
# Open the file ('rb' is for read binary)
with open(filePath,'rb') as f:
    for i in range(1,10):
        print(f'Iteration {i} result:')
        rl = struct.unpack('<i',f.read(4))
        print(rl)
