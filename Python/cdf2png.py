#!/usr/bin/python

import numpy, os, sys, glob, ogr, time
from netCDF4 import Dataset


###Main Porgam begins...
if len(sys.argv) < 3:
	print 'Please try again and pass in the variable to process (precip,tmax,tmin,tavg)'
	print 'and the year to process (e.g., 2012)'
	print 'and the month to process (e.g., 1 for Jan...)'
	print 'Example of usage: cdf2png.py tmax 2013'
	sys.exit()
usevar = sys.argv[1]
yyyy = sys.argv[2]


#Reading the NetCDF file
root_grp = Dataset('test.nc')
temp = root_grp.variables['temp']


