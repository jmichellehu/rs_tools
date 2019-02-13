#!/usr/bin/env python

# This script calculates TOA reflectance for Landsat 8 Level 1 imagery

# import libraries
# requires gdal and geoio from https://github.com/DigitalGlobe/geoio
# uses functions created by dshean's dgtools github repo

import math
import geoio
from gdalconst import *
import argparse
import re

# Have user define input data from MTL file and output filename
parser = argparse.ArgumentParser(description='GeoTiff Landsat 8 Multispectral Image to TOA Reflectance Script')

parser.add_argument('-in', '--input_file', help='GeoTiff multi band MS image file', required=True)
# parser.add_argument('-in_band', '--input_band', help='GeoTiff multi band', required=True)
# parser.add_argument('-M', '--input_Mp', help='GeoTiff multi band Reflectance Multiplication input', required=True)
# parser.add_argument('-A', '--input_Ap', help='GeoTiff multi band Reflectance Addition input', required=True)
# parser.add_argument('-sun', '--input_SunEl', help='GeoTiff multi band Sun Elevation input', required=True)

parser.add_argument('-in_MTL', '--input_MTL_textfile', help='Delivered with L8 imagery', required=True)

parser.add_argument('-out', '--output_file', help='Where TOA reflectance image is to be saved', required=True)
args = parser.parse_args()

in_filename = args.input_file
# Mp = float(args.input_Mp)
# Ap = float(args.input_Ap)
# sunelev = float(args.input_SunEl)
in_MTL_filename = args.input_MTL_textfile
out_filename = args.output_file

######## --------- Define functions --------- ########

# Check that values for list are equivalent.  Sourced from https://stackoverflow.com/questions/3844801/check-if-all-elements-in-a-list-are-identical

def check_equal(some_list):
    # return boolean of equality for 2nd element to end and 1st element to penultimate
   return some_list[1:] == some_list[:-1]

def get_val(some_list):
    # extract value after " = " in list of strings
    vals = [val.split(' = ')[1] for val in some_list]
    return(vals)


### --- Extract Mp, Ap, and sunelev values from MTL file --- ###
mtl_list = []

with open(in_MTL_filename, 'r') as f:
    for line in f:
        # strip the trailing newline character
        line=line.rstrip()
        # and strip the leading whitespaces, newline, and tab characters
        line=line.lstrip()
        # append this to the list
        mtl_list.append(line)

# Use regular expressions to find matches for the Mp, Ap, and SunEl values
Mp_pattern=re.compile(r"(REFLECTANCE_MULT).*")
Ap_pattern=re.compile(r"(REFLECTANCE_ADD).*")
Sun_pattern=re.compile(r"(SUN_).*")


# iterate through each line in the list and return matches
Mp_list = [m.group() for line in mtl_list for m in [Mp_pattern.search(line)] if m]
Ap_list = [m.group() for line in mtl_list for m in [Ap_pattern.search(line)] if m]
Sun_list = [m.group() for line in mtl_list for m in [Sun_pattern.search(line)] if m]

# extract corresponding value (i.e. the bit after " = ")
Mp_val = get_val(Mp_list)
Ap_val = get_val(Ap_list)
Sun_val = get_val(Sun_list)

# Check that each band has the same value for Mp and Ap, and save extracted values as floats in the Mp, Ap, and sunel variables to be used in L8_toa_refl calculations.  Otherwise, flag it and tell the user to check the MTL file

if check_equal(Mp_val):
    Mp=float(Mp_val[0])
else:
    print("Mp values are not equal, examine MTL file")
    print(Mp_list)

if check_equal(Ap_val):
    Ap=float(Ap_val[0])
else:
    print("Ap values are not equal, examine MTL file")
    print(Ap_list)

if (float(Sun_val[1]) <= 90.0 and float(Sun_val[1]) >=0.0):
    sunelev = float(Sun_val[1])
else:
    print("Sun elevation value out of bounds, examine MTL file")
    print(Sun_val)

print(Mp, Ap, sunelev)

######## --------- CONVERT TO TOA REFLECTANCE --------- ########

# Open the multiband landsat image
img=geoio.GeoImage(in_filename)

# Numpy arrays of tif
data=img.get_data()

# Calculate TOA reflectances - equations from https://landsat.usgs.gov/using-usgs-landsat-8-product

newdata = Mp * data + Ap
solzenith = 90-sunelev
TOA_refl = newdata/math.cos(solzenith/360*2*math.pi)

img.write_img_like_this(out_filename, TOA_refl)
