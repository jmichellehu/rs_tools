#!/usr/bin/env python

# This script calculates TOA reflectance for Landsat 8 Level 1 imagery

# import libraries
# requires gdal and geoio from https://github.com/DigitalGlobe/geoio
# uses functions created by dshean's dgtools github repo

import math
import geoio
from gdalconst import *
import argparse

# Have user define input data from MTL file and output filename
parser = argparse.ArgumentParser(description='GeoTiff Landsat 8 Multispectral Image to TOA Reflection Image Conversion Script')

parser.add_argument('-in', '--input_file', help='GeoTiff multi band MS image file', required=True)
# parser.add_argument('-in_band', '--input_band', help='GeoTiff multi band', required=True)
parser.add_argument('-M', '--input_Mp', help='GeoTiff multi band Reflectance Multiplication input', required=True)
parser.add_argument('-A', '--input_Ap', help='GeoTiff multi band Reflectance Addition input', required=True)
parser.add_argument('-sun', '--input_SunEl', help='GeoTiff multi band Sun Elevation input', required=True)
parser.add_argument('-out', '--output_file', help='Where TOA reflectance image is to be saved', required=True)
args = parser.parse_args()

in_filename = args.input_file
Mp = float(args.input_Mp)
Ap = float(args.input_Ap)
sunelev = float(args.input_SunEl)
out_filename = args.output_file

img=geoio.GeoImage(in_filename)

# Numpy arrays of tif
data=img.get_data()

# Calculate TOA reflectances - equations from https://landsat.usgs.gov/using-usgs-landsat-8-product

newdata = Mp * data + Ap
solzenith = 90-sunelev
TOA_refl = newdata/math.cos(solzenith/360*2*math.pi)

img.write_img_like_this(out_filename, TOA_refl)
