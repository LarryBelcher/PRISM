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


def getfiles(var,year):

	if int(year) >= 2010 and int(year) <=2019:
		ydir = '2010-2019'
	if int(year) >= 2000 and int(year) <=2009:
		ydir = '2000-2009'
	if int(year) >= 1990 and int(year) <=1999:
		ydir = '1990-1999'
	if int(year) >= 1980 and int(year) <=1989:
		ydir = '1980-1989'
	if int(year) >= 1970 and int(year) <=1979:
		ydir = '1970-1979'
	if int(year) >= 1960 and int(year) <=1969:
		ydir = '1960-1969'
	if int(year) >= 1950 and int(year) <=1959:
		ydir = '1950-1959'
	if int(year) >= 1940 and int(year) <=1949:
		ydir = '1940-1949'
	if int(year) >= 1930 and int(year) <=1939:
		ydir = '1930-1939'
	if int(year) >= 1920 and int(year) <=1929:
		ydir = '1920-1929'
	if int(year) >= 1910 and int(year) <=1919:
		ydir = '1910-1919'
	if int(year) >= 1900 and int(year) <=1909:
		ydir = '1900-1909'
	if int(year) >= 1890 and int(year) <=1899:
		ydir = '1890-1899'
	
	if var == 'precip':
		var = 'ppt'
	
	ndx = 1
	for mm in range(12):
		mms = str(ndx)
		if(mm < 9):
			mms = '0'+mms
		url = 'ftp://prism.oregonstate.edu//pub/prism/us/grids/'+var+'/'+ydir+'/us_'+var+'_'+year+'.'+mms+'.asc.gz'
		cmd = 'wget '+url
		os.system(cmd)
		ndx = ndx + 1
	cmd = 'gunzip *.asc.gz'
	os.system(cmd)
	cmd = 'mv *.asc ../Grids'
	os.system(cmd)


###Main Porgam begins...
if len(sys.argv) < 3:
	print 'Please try again and pass in the variable to process (precip,tmax,tmin)'
	print 'and the year to process (e.g., 2012)'
	print 'Example of usage: asc2cdf.py tmax 2013'
	sys.exit()
usevar = sys.argv[1]
yyyy = sys.argv[2]

if usevar == 'precip':
	dvar = 'ppt' # possibilities are: ppt, tmax, tmin
	longdesc = 'Total_Precipitation_'+str(yyyy)
	units = 'Inches'

if usevar == 'tmax':
	dvar = 'tmax' # possibilities are: ppt, tmax, tmin
	longdesc = 'Maximum_Temperature_'+str(yyyy)
	units = 'DegreeF'
	
if usevar == 'tmin':
	dvar = 'tmin' # possibilities are: ppt, tmax, tmin
	longdesc = 'Minimum_Temperature_'+str(yyyy)
	units = 'DegreeF'



getfiles(usevar,yyyy)


files = glob.glob('../Grids/us_'+dvar+'*')
files = sorted(files)



lons, lats, grdata = grdRead(files[0])

if usevar == 'precip':
	grdata = (grdata / 100.) / 25.4


if usevar == 'tmax' or usevar == 'tmin':
	grdata = (1.8 * (grdata/100.)) + 32.

rootgrp = Dataset('./us_'+dvar+'_'+yyyy+'.nc', 'w', format='NETCDF4')
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


f = Dataset('./us_'+dvar+'_'+yyyy+'.nc', 'a')
append1 = f.variables[dvar]
ndx = 1
for i in xrange(len(files)-1):
	print 'Reading '+files[ndx]
	newlons, newlats, newdata = grdRead(files[ndx])
	if usevar == 'precip':
		newdata = (newdata / 100.) / 25.4
	if usevar == 'tmax' or usevar == 'tmin':
		newdata = (1.8 * (newdata/100.)) + 32.
	append1[ndx,:,:] = newdata
	ndx = ndx+1
f.close()


rootgrp.close()

#Clean up...
if usevar == 'precip':
	cmd = 'mv *.nc ../NetCDF/Precip/'
	os.system(cmd)
if usevar == 'tmax':
	cmd = 'mv *.nc ../NetCDF/Tmax/'
	os.system(cmd)
if usevar == 'tmin':
	cmd = 'mv *.nc ../NetCDF/Tmin/'
	os.system(cmd)
cmd = 'rm ../Grids/*.asc'
os.system(cmd)


