#!/usr/bin/python

from PIL import Image
from pycoast import ContourWriterAGG
img = Image.new('RGB', (425, 425))
proj4_string = '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs '
area_extent = (-5570248.4773392612, -5567248.074173444, 5567248.074173444, 5570248.4773392612)
area_def = (proj4_string, area_extent)
cw = ContourWriterAGG('/usr/local/GSHHG/')
cw.add_coastlines(img, (proj4_string, area_extent), resolution='l', width=0.5)
img.show()

