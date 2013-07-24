#!/usr/bin/python


import numpy, os, sys, glob, ogr, time
from netCDF4 import Dataset



def grdRead(filename, delimiter=None):
    """
    Read formatted data from an ascii grid format file.
    Returns the longitude and latitude of the grid and the data values
    The files have 6 header lines describing the data, followed by the
    data in a gridded format.

    Headers:
    ncols
    nrows
    xllcorner
    yllcorner
    cellsize
    NODATA_value

    Usage:
    longitude, latitude, data = grdRead(filename, [delimiter])
    """

    fileext = filename.rsplit('.')[-1]

    # If file extention is '.nc' then load as netcdf file
    # Otherwise load with grdRead
    if fileext == 'nc':
        nc_obj = nctools.ncLoadFile(filename)
        lon = numpy.array(nctools.ncGetDims(nc_obj, 'lon'),dtype=float)
        lat = numpy.array(nctools.ncGetDims(nc_obj, 'lat'),dtype=float)
        #lat = numpy.flipud(lat)
        data_varname = set.difference(set(nc_obj.variables.keys()),
                                      set(nc_obj.dimensions.keys()))
        if len(data_varname) != 1:
            raise IOError, 'Cannot resolve data variable in netcdf file: ' + filename
        data = numpy.array(nctools.ncGetData(nc_obj, data_varname.pop()),dtype=float)
        nc_obj.close()
    else:
        try:
            fh = open(filename, 'r')
        except:
            #g_logger.flLog("Cannot open %s"%filename)
            raise IOError, "Cannot open %s"%filename
            return

        metadata = {}
        metadata["ncols"] = []
        metadata["nrows"] = []
        metadata["xllcorner"] = []
        metadata["yllcorner"] = []
        metadata["cellsize"] = []
        metadata["NODATA_value"] = []

        for i in xrange(0,6):
            line = fh.readline()
            contents = line.split()
            label = contents[0]
            metadata[label] = float(contents[1])

        lon0 = metadata["xllcorner"]
        lon = numpy.array(range(int(metadata["ncols"])), dtype=float)
        lon = lon*metadata["cellsize"]+lon0
        lat0 = metadata["yllcorner"]
        lat = numpy.array(range(int(metadata["nrows"])), dtype=float)
        lat = lat*metadata["cellsize"]+lat0
        lat = numpy.flipud(lat)

        data = numpy.zeros([metadata["nrows"], metadata["ncols"]], dtype=float)

        for i in xrange(int(metadata["nrows"])):
            row = numpy.zeros([metadata["ncols"]], dtype=float)
            line = fh.readline()
            for j, val in enumerate(line.split(delimiter)):
                value = float(val)
                if value == metadata["NODATA_value"]:
                    value = numpy.nan
                row[j] = value
            data[i,:] = row
        fh.close()
	
	data.reshape(metadata["nrows"], metadata["ncols"])

    return lon, lat, data


def rebin(a, shape):
    sh = shape[0],a.shape[0]//shape[0],shape[1],a.shape[1]//shape[1]
    return a.reshape(sh).mean(-1).mean(1)


###Main Porgam begins...
if len(sys.argv) < 2:
	print 'Please try again and pass in the variable to process (precip,tmax,tmin)'
	print 'Example of usage: norms2cdf.py tmax'
	sys.exit()
usevar = sys.argv[1]

if usevar == 'precip':
	dvar = 'ppt' # possibilities are: ppt, tmax, tmin
	longdesc = 'Total_Precipitation_Climatology(30-year_Average)'
	units = 'Inches'

if usevar == 'tmax':
	dvar = 'tmax' # possibilities are: ppt, tmax, tmin
	longdesc = 'Maximum_Temperature_Climatology(30-year_Average)'
	units = 'DegreeF'
	
if usevar == 'tmin':
	dvar = 'tmin' # possibilities are: ppt, tmax, tmin
	longdesc = 'Minimum_Temperature_Climatology(30-year_Average)'
	units = 'DegreeF'

files = glob.glob('../Grids/us_'+dvar+'*')
files = sorted(files)


hrlons, hrlats, hrdata = grdRead(files[0])
lons, lats, fakedata = grdRead('us_ppt_2010.01.asc')

grdata = rebin(hrdata,(len(lats),len(lons)))

if usevar == 'precip':
	grdata = (grdata / 100.) / 25.4


if usevar == 'tmax' or usevar == 'tmin':
	grdata = (1.8 * (grdata/100.)) + 32.

rootgrp = Dataset('./us_'+dvar+'_1981-2010_lowres.nc', 'w', format='NETCDF4')
rootgrp.description = longdesc
rootgrp.history = 'Created ' + time.ctime(time.time())
rootgrp.source = 'PRISM Climate Group, Oregon State University, http://prism.oregonstate.edu'


# dimensions
rootgrp.createDimension('len', 12)
rootgrp.createDimension('lat', len(lats))
rootgrp.createDimension('lon', len(lons))

# variables
months = rootgrp.createVariable('month', 'i4', ('len',))
latitudes = rootgrp.createVariable('latitude', 'f4', ('lat',))
longitudes = rootgrp.createVariable('longitude', 'f4', ('lon',))
data = rootgrp.createVariable(dvar, 'f4', ('len', 'lat', 'lon',),zlib=True)


latitudes.units = 'degrees'
longitudes.units = 'degrees'
data.units = units


# data
months[:] = numpy.array(range(12))+1
latitudes[:] = lats
longitudes[:] = lons
data[0,:,:] = grdata


f = Dataset('./us_'+dvar+'_1981-2010_lowres.nc', 'a')
append1 = f.variables[dvar]
ndx = 1
for i in xrange(len(files)-1):
	print 'Reading '+files[ndx]
	newlons, newlats, newhrdata = grdRead(files[ndx])
	newdata = rebin(newhrdata,(len(lats),len(lons)))
	if usevar == 'precip':
		newdata = (newdata / 100.) / 25.4
	if usevar == 'tmax' or usevar == 'tmin':
		newdata = (1.8 * (newdata/100.)) + 32.
	append1[ndx,:,:] = newdata
	ndx = ndx+1
f.close()


rootgrp.close()






