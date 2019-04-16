#!/usr/bin/env python

"""
SYNOPSIS

  mk_AVAILABLE.py: [-s,--startdate] [-e,--enddate] [-m,--model /ECWMF/ERAI/EI/E5/EA/GFS] [-p, --path] [-a, --avpath] [-i, --interval] [-h] [-v,--verbose] [--version]

DESCRIPTION

  mk_AVAIL is a script to create AVAILABLE files for FLEXPART windfields.

  Example usage:
  %mk_AVAIL.py -s 200601 -e 200701 -m ECMWF -p . -h 

  would create a file: AVAIALABLE that contained paths 
  of all files available in the current directory between 200601 and 200701. 
  The default start date is 197001 and the default end date is TODAY.
  
  adapted and simplified version / Petra Seibert
  v.004: add ERA-Interim with EI as model, proper sorting of dates if year 2000 included, option to define a path for AVAILABLE / Petra Seibert 2015-10-21
  v.005: check whether any files are found before opening AVAILABLE, if not issue warning and stop. / Petra Seibert 2015-12-07
  v.006 PS 2018-04-24:   add ERA5 as model option
  v.007 PS 2018-06-25:   correct bug introduced in v006: 2 spaces missing in output format
  
QUESTIONS to

  JFB: <jfb@nilu.no>
  version>=003: petra.seibert at boku.ac.at

LICENSE

  This script follows creative commons usage.
  Valid-License-Identifier: CC-BY-4.0

VERSION

  $Id: 0.006 $

"""

import sys
import os
import traceback
import optparse
import time
import datetime
import socket
import glob
import string


def main ():

  global options, args, models
  version = '$Id: 0.006 $'  
  
  WIND_dir = '/work/mm0062/b302073/FlexSample/Metfiles/ECMWF_EA5'
  
  # dict of dicts with model information
  # timeindex: index in the filne name string where the time information starts
  print  MODEL.keys()

  AVAIL_head = \
  """DATE     TIME        FILENAME             SPECIFICATIONS\
   \nYYYYMMDD HHMISS\
  \n________ ______      __________________    __________________\n"""
  start_date = options.startdate
  sy = int(start_date[0:4])
  sm = int(start_date[4:6])
  end_date = options.enddate
  ey = int(end_date[0:4])
  em = int(end_date[4:6])
  
  #Get the directory information
  M = MODEL[options.model]
  prfx = M['prefix']
  t = options.path
  avpath = options.avpath
  
  
  #Loop through the files in the directories
  
  warned = False
  d = t #directory
  
  tind = M['timeindex'] #timestamp index
  searchstr = os.path.join(t,prfx)
  print 'searchstring:',searchstr
  files = glob.glob(searchstr + '*')
  if options.verbose: print len(files), ' wind-field files found'
  dict_dates={}
  for f in files:
    if (f[0:2] == './'): f = f[2:] # PS - remove this part if present
    fn = os.path.basename(f)
    if fn[-1] != '*':
      timestamp = fn[tind:]
      year = int(timestamp[0:2])
      if year < 58:
        year += 2000
      else:
        year += 1900
      dtstring = str(year)+' '+timestamp[2:9]
      dict_dates[dtstring] = f
  dates = sorted(dict_dates.items())
  if len(dates) == 0:
    print 'no files found with this search string'
    print 'aborting. '
    sys.exit(0)
  else:
    print 'found ',len(dates),'files'
    #Prepare output files
    fout = file(os.path.join(avpath,'AVAILABLE'),'w')
    fout.write(AVAIL_head)

  for i,date in enumerate(dates): # go through dates in ascending order
    f = date[1] # now we have the filename+path
    fn = os.path.basename(f)
    if fn[-1]!='*':
      timestamp = fn[tind:]
      year = int(timestamp[0:2])
      if year < 58:
        year += 2000
      else:
        year += 1900
      month = int(timestamp[2:4])
      day   = int(timestamp[4:6])
      hour  = int(timestamp[6:8])
      fileT = year*100 + int(month)
# PS: now check for irregular intervals      
      date = datetime.datetime(year,month,day,hour)
      if i == 2:
        if options.timeint == '':
          timeint = date - date1
        else:
          timeint = datetime.timedelta(0,3600*int(options.timeint))  
        if timeint != date - date1:
          print 'WARNING - irregular interval',date - date1
          print date1,f1,'\n',date, f,'\n'
      elif i > 2:
        if timeint != date - date1: 
          print 'WARNING - irregular interval',date - date1
          print date1,f1,'\n',date, f,'\n'
        if options.timeint == '': timeint = date - date1
      date1 = date  
      f1 = f
      
      if i%5000 == 0: print 'progress:', i, 'of', len(dates), f
      
      if fileT >= sy*100 + sm and fileT <= ey*100 + em :

        relpath = os.path.relpath( os.path.dirname(f), avpath )
        f = os.path.join(relpath,fn)
        f = fn

        if (f[0:2] == './'): f = f[2:] #  remove this part if present

        if len(f) > 18: #PS
          if not warned:
            print 'WARNING: Flexpart can only read 18 chars in WF-name'
            print f, ' has ', len(f), ' characters!\n'
            warned = True

        #This is the fortran format: (i8,1x,i6,2(6x,a18))
        string = "%s%s%s %s0000      %s    ON DISC\n" %\
         (year,str(month).zfill(2),str(day).zfill(2),str(hour).zfill(2),f.ljust(18))
        fout.write(string)

  print 'Done: ',i+1 # as i starts with 0
  print 'Written:', os.path.join(avpath,'AVAILABLE')
  fout.close()

if __name__ == '__main__':
  MODEL = {}
  MODEL['ECMWF'] = {'prefix':'EN', 'timeindex':2}
  MODEL['ERAI']  = {'prefix':'EI', 'timeindex':2}
  MODEL['EI']  = {'prefix':'EI', 'timeindex':2}
  MODEL['E5']  = {'prefix':'E5', 'timeindex':2}
  MODEL['EA']  = {'prefix':'EA', 'timeindex':2}
  MODEL['GFS']   = {'prefix':'GF', 'timeindex':2}
  
  models = '/'.join(MODEL.keys())
  
  try:
    start_time = time.time()
    today = datetime.datetime.now()

    parser = optparse.OptionParser(
        formatter = optparse.TitledHelpFormatter(),
        usage = globals()['__doc__'])

    parser.add_option ('-v', '--verbose', action = 'store_true',
        default = False, help = 'verbose output')

    parser.add_option ('-s', '--startdate',
        dest = 'startdate',
        default = '197001',
        help = 'startdate YYYYMM integer')

    parser.add_option ('-e', '--enddate',
        # setting default as TODAY
        dest = 'enddate',
        default = str(today.year) + str(today.month).zfill(2),
        #default = '200712',
        help = 'enddate YYYYMM integer')

    parser.add_option ('-m', '--model',
        dest = 'model',
        default = 'ECMWF', help = models)

    parser.add_option ('-p', '--path',
        dest = 'path',
        default = '.', help = 'path to be searched for windfields. Escape or quote * and ? ')

    parser.add_option ('-a', '--avpath',
        dest = 'avpath',
        default = '.', help = 'path for AVAILABLE file ')

    parser.add_option ('-i', '--interval',
        dest = 'timeint',
        default = '', help = 'expected time interval in h. If omitted, show every change')

    (options, args) = parser.parse_args()

    #QUERY['modelType'] = options.model
    #QUERY['start_date'] = options.startdate
    #QUERY['end_date'] = options.enddate
  
    #if len(args) < 1:
    #  parser.error ('missing argument')

    if options.verbose: print time.asctime()
    exit_code = main()
    if exit_code is None:
      exit_code = 0
    if options.verbose: print time.asctime()
    if options.verbose: print 'TOTAL TIME IN MINUTES:',
    if options.verbose: print (time.time() - start_time) / 60.0
    sys.exit(exit_code)
  except KeyboardInterrupt, e: # Ctrl-C
    raise e
  except SystemExit, e: # sys.exit()
    raise e
  except Exception, e:
    print 'ERROR, UNEXPECTED EXCEPTION'
    print str(e)
    traceback.print_exc()
    os._exit(1)
    
  

# vim:set sr et ts=4 sw=4 ft=python fenc=utf-8: // See Vim, :help 'modeline'
