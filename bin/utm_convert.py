#!/usr/bin/env python

# This script returns utm zone numbers for the WGS84 datum as well as EPSG codes for the contiguous United states.  The utm package is required

### # TODO:
# Incorporate handling for one-off lat lon inputs
# bounds rounded to the  that intersect the spatial extent extracted from geotransform information of an input image.  Large parts of this code are sourced from David Shean's dgtools repository and from https://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings

# Usage from command line:
# python utm_convert.py -in image.tif -L left -B bottom -R right -T top

# output format
# text file of corresponding utm zones for contiguous US

import utm
import argparse, gdal, osr, math

parser = argparse.ArgumentParser(description='Geographic coordinates to UTM zone converter')
parser.add_argument('-in', '--input_file', help='GeoTiff image file', required=False)
parser.add_argument('-L', '--left', help='Leftmost bound', required=False, type=float)
parser.add_argument('-B', '--bottom', help='Bottom-most bound', required=False, type=float)
parser.add_argument('-R', '--right', help='Rightmost bound', required=False, type=float)
parser.add_argument('-T', '--top', help='Top bound', required=False, type=float)
parser.add_argument('-zone', '--get_utm_zone', help='Boolean 0 or 1 to return utm zone", required=False, type=int)

args = parser.parse_args()
in_fn = args.input_file
l=args.left
b=args.bottom
r=args.right
t=args.top
z=args.get_utm_zone

# Define functions
def round_down(n, decimals=2):
    '''
    Function to implement floor function and round down to nearest hundredths place
    '''
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier

def round_up(n, decimals=2):
    '''
    Function to implement ceiling function and round up to nearest hundredths place
    '''
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

# Pulled from David Shean's dgtools
# Get functions set up
def getTag(xml_fn, tag):
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_fn)

    # Want to check to make sure tree contains tag
    elem = tree.find('.//%s' % tag)
    if elem is not None:
        return elem.text

def xml_dt(xml_fn):
    t = getTag(xml_fn, 'FIRSTLINETIME')
    dt = datetime.strptime(t,"%Y-%m-%dT%H:%M:%S.%fZ")
    return dt

def getAllTag(xml_fn, tag):
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_fn)

    # Want to check to make sure tree contains tag
    elem = tree.findall('.//%s' % tag)
    return [i.text for i in elem]


def GetExtent(gt, cols, rows):
    '''
    Get spatial extent of input raster based on geotransform information.
    '''
    # corners:   coordinates of each corner (CCW): TL, BL, BR, TR
    gdal_ext=[]
    corners=[]
    xarr=[0,cols]
    yarr=[0,rows]

    for px in xarr:
        for py in yarr:
            x=gt[0]+(px*gt[1])+(py*gt[2])
            y=gt[3]+(px*gt[4])+(py*gt[5])
            corners.append([x,y])
        yarr.reverse()
    gdal_ext=[corners[0][0], corners[2][1], corners[2][0], corners[0][1]] # L, B, R, T

    return gdal_ext, corners

def ReprojectCoords(coords, src_srs, tgt_srs):
    ''' Function to reproject a list of x,y coordinates.

        @type geom:     C{tuple/list}
        @param geom:    List of [[x,y],...[x,y]] coordinates
        @type src_srs:  C{osr.SpatialReference}
        @param src_srs: OSR SpatialReference object
        @type tgt_srs:  C{osr.SpatialReference}
        @param tgt_srs: OSR SpatialReference object
        @rtype:         C{tuple/list}
        @return:        List of transformed [[x,y],...[x,y]] coordinates
    '''
    trans_coords=[]
    transform = osr.CoordinateTransformation(src_srs, tgt_srs)
    for x,y in coords:
        x,y,z = transform.TransformPoint(x,y)
        trans_coords.append([x,y])
    return trans_coords

try:
    xml = in_fn[:-3]+'xml'
    # if in_fn[-3:] == 'XML':
    #     xml=in_fn
    # else:
    #     xml=in_fn[:-3]+'XML'
    f=open(xml)
    f.close()
    ur_lon=float(getTag(xml, 'URLON'))
    ur_lat=float(getTag(xml, 'URLAT'))

    ul_lon=float(getTag(xml, 'ULLON'))
    ul_lat=float(getTag(xml, 'ULLAT'))

    lr_lon=float(getTag(xml, 'LRLON'))
    lr_lat=float(getTag(xml, 'LRLAT'))

    ll_lon=float(getTag(xml, 'LLLON'))
    ll_lat=float(getTag(xml, 'LLLAT'))

    # print(round_down(min(ul_lon, ll_lon), decimals=1),  # Left
    # round_down(min(lr_lat, ll_lat), decimals=1),  # Bottom
    # round_up(max(ur_lon, lr_lon), decimals=1),    # Right
    # round_up(max(ul_lat, ur_lat), decimals=1))    # Top

    # Round to nearest degree (largest extent this time!)
    xmin=int(round_down(min(ul_lon, ll_lon), decimals=0))  # Left
    ymin=int(round_down(min(lr_lat, ll_lat), decimals=0))  # Bottom
    xmax=int(round_up(max(ur_lon, lr_lon), decimals=0))    # Right
    ymax=int(round_up(max(ul_lat, ur_lat), decimals=0))    # Top
except:
    if l is not None:
        if l>180:    # Correct for absolute eastings
            l=l-360
        if r>180:
            r=r-360
        xmin=l
        ymin=b
        xmax=r
        ymax=t
    else:
        # Call functions on input image
        raster_ds = gdal.Open(in_fn, gdal.GA_ReadOnly)
        # Fetch number of rows and columns
        ncol = raster_ds.RasterXSize
        nrow = raster_ds.RasterYSize
        # Fetch geotransform
        gt = raster_ds.GetGeoTransform()
        ext, corners = GetExtent(gt, ncol, nrow)

        src_srs=osr.SpatialReference()
        src_srs.ImportFromWkt(raster_ds.GetProjection())
        print(src_srs.ImportFromWkt(raster_ds.GetProjection()))
        tgt_srs=src_srs.CloneGeogCS()

        geo_ext=ReprojectCoords(corners,src_srs,tgt_srs)

        # Close dataset to free up resources
        raster_ds=None

        # Round to nearest degree (largest extent this time!)
        xmin=int(round_down(min(geo_ext[0][0], geo_ext[1][0]), decimals=0))  # Left
        ymin=int(round_down(min(geo_ext[1][1], geo_ext[2][1]), decimals=0))  # Bottom
        xmax=int(round_up(max(geo_ext[2][0], geo_ext[3][0]), decimals=0))    # Right
        ymax=int(round_up(max(geo_ext[3][1], geo_ext[1][1]), decimals=0))    # Top

# Get center coordinates and pull UTM zone from these
x_center=(xmin + xmax)/2
y_center=(ymin + ymax)/2
zone=utm.from_latlon(y_center, x_center)[2]
epsg="326"+str(zone)

# print(xmin, ymin, xmax, ymax)
# print(x_center, y_center)
# print(zone)
print(epsg)
