#!usr/bin/env python3
# ===========================================================
# 16/04/2019
# This script is a first aproximation to extract flexpart
# output information using python
# ===========================================================

import os

# == Define parameters ======================================
# Path to some grid files
dataPath = 'testData/test1_DoesThisWork/output/'
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



