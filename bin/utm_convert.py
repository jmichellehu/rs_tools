#!/usr/bin/env python

# This script returns EPSG codes and utm zone numbers for the WGS84 datum.  Coordinate conversion uses pyproj library
# Parts of this code are sourced from:
# David Shean's dgtools repository, 
# https://gis.stackexchange.com/questions/57834/how-to-get-raster-corner-coordinates-using-python-gdal-bindings, 
# and https://github.com/DigitalGlobe/gdal_ortho/blob/master/gdal_ortho/gdal_ortho.py

'''Usage from command line:
utm_convert.py -in image.tif -L left -B bottom -R right -T top -z T/F (get_utm_zone) -c T/F (get_projected_coordinates)
output format: print epsg and utm zones 
'''

import argparse, gdal, osr, math
import sys, os

def round_down(n, decimals=2):
    '''Function to implement floor function and round down to nearest hundredths place'''
    multiplier = 10 ** decimals
    return math.floor(n * multiplier) / multiplier

def round_up(n, decimals=2):
    '''Function to implement ceiling function and round up to nearest hundredths place'''
    multiplier = 10 ** decimals
    return math.ceil(n * multiplier) / multiplier

def getTag(xml_fn, tag):
    '''From David Shean's dgtools'''
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_fn)

    # Want to check to make sure tree contains tag
    elem = tree.find('.//%s' % tag)
    if elem is not None:
        return elem.text

def xml_dt(xml_fn):
    '''From David Shean's dgtools'''
    t = getTag(xml_fn, 'FIRSTLINETIME')
    dt = datetime.strptime(t,"%Y-%m-%dT%H:%M:%S.%fZ")
    return dt

def getAllTag(xml_fn, tag):
    '''From David Shean's dgtools'''
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_fn)
    elem = tree.findall('.//%s' % tag)
    return [i.text for i in elem]

def GetExtent(gt, cols, rows):
    '''Get spatial extent of input raster based on geotransform information.
    corners:   coordinates of each corner (CCW): TL, BL, BR, TR'''
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

def get_utm_epsg_code(lat, lon, z=None):
    import shapely.geometry
    import json
    """Modified from https://github.com/DigitalGlobe/gdal_ortho/blob/master/gdal_ortho/gdal_ortho.py
    Looks up the UTM zone for a point. This function uses the UTM Zone Boundaries shapefile from this
    location: http://earth-info.nga.mil/GandG/coordsys/grids/universal_grid_system.html
    Args:
        lat: Latitude of the point to use.
        lon: Longitude of the point to use.
    Returns the integer EPSG code for the UTM zone containing the input point.
    """

    UTM_ZONES_PATH="../data/UTM_Zone_Boundaries.geojson"

    # Load the UTM zones
    zone_geoms = {}
    with open(UTM_ZONES_PATH, "r") as f_obj:
        zones_dict = json.load(f_obj)
    for feature in zones_dict["features"]:
        zone_geom = shapely.geometry.shape(feature["geometry"])
        zone_str = feature["properties"]["Zone_Hemi"]
        zone_geoms[zone_str] = zone_geom

    # Loop through zones and find the zone that contains the point
    pt = shapely.geometry.Point([lon, lat])
    found_zone = None
    for (zone_str, zone_geom) in zone_geoms.items():
        if zone_geom.contains(pt):
            found_zone = zone_str
    if found_zone is None:
        raise InputError("Latitude %.10f Longitude %.10f is not in any UTM zone" % \
                         (lat, lon))
    # Parse the zone
    (zone_num, hemisphere) = found_zone.split(",")
    if hemisphere == "n":
        base_epsg = 32600
    else:
        base_epsg = 32700

    epsg = base_epsg + int(zone_num)
    
    if z is not None:
        print("ZONE:", zone_num + hemisphere.upper())
        print("EPSG:", epsg)
    return('epsg:'+str(epsg), epsg)

def run(in_fn=None, l=None, b=None, r=None, t=None, z=None, c=None):
    try:
        if os.path.exists(in_fn[:-3]+'xml'):
            xml = in_fn[:-3]+'xml'
        elif os.path.exists(in_fn[:-3]+'XML'):
            xml = in_fn[:-3]+'XML'    
        ur_lon=float(getTag(xml, 'URLON'))
        ur_lat=float(getTag(xml, 'URLAT'))

        ul_lon=float(getTag(xml, 'ULLON'))
        ul_lat=float(getTag(xml, 'ULLAT'))

        lr_lon=float(getTag(xml, 'LRLON'))
        lr_lat=float(getTag(xml, 'LRLAT'))

        ll_lon=float(getTag(xml, 'LLLON'))
        ll_lat=float(getTag(xml, 'LLLAT'))

        # Round to nearest degree (largest extent)
        xmin=int(round_down(min(ul_lon, ll_lon), decimals=0))  # Left
        ymin=int(round_down(min(lr_lat, ll_lat), decimals=0))  # Bottom
        xmax=int(round_up(max(ur_lon, lr_lon), decimals=0))    # Right
        ymax=int(round_up(max(ul_lat, ur_lat), decimals=0))    # Top
    except:
        if l is not None:
            xmin, ymin, xmax, ymax=l, b, r, t
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
            tgt_srs=src_srs.CloneGeogCS()

            geo_ext=ReprojectCoords(corners,src_srs,tgt_srs)

            # Close dataset to free up resources
            raster_ds=None

            # Round to nearest degree (largest extent this time!)
            xmin=int(round_down(min(geo_ext[0][0], geo_ext[1][0]), decimals=0))  # Left
            ymin=int(round_down(min(geo_ext[1][1], geo_ext[2][1]), decimals=0))  # Bottom
            xmax=int(round_up(max(geo_ext[2][0], geo_ext[3][0]), decimals=0))    # Right
            ymax=int(round_up(max(geo_ext[3][1], geo_ext[1][1]), decimals=0))    # Top

    if xmin>180:    # Correct for absolute eastings
        xmin=xmin-360
    if xmax>180:
        xmax=xmax-360
        
    # Get center coordinates and pull UTM zone from these
    x_center=(xmin + xmax)/2
    y_center=(ymin + ymax)/2

    proj_str, epsg = get_utm_epsg_code(y_center, x_center, z)
    
    # convert input coordinates to projected UTM coordinates with pyproj
    if c is None:
        print(epsg)
    else:
        from pyproj import Proj, transform
        inProj = Proj(init='epsg:4326')
        outProj = Proj(init=proj_str)
        min_easting, min_northing =transform(inProj, outProj, xmin, ymin)
        max_easting, max_northing =transform(inProj, outProj, xmax, ymax)
        print(min_easting, min_northing, max_easting, max_northing)

def get_parser():
    parser = argparse.ArgumentParser(description='Geographic coordinates to UTM zone converter')
    parser.add_argument('-in', '--input_file', help='GeoTiff image file', required=False)
    parser.add_argument('-L', '--left', help='Leftmost bound', required=False, type=float)
    parser.add_argument('-B', '--bottom', help='Bottom-most bound', required=False, type=float)
    parser.add_argument('-R', '--right', help='Rightmost bound', required=False, type=float)
    parser.add_argument('-T', '--top', help='Top bound', required=False, type=float)
    parser.add_argument('-zone', '--get_utm_zone', help='Flag to block returning UTM zone', required=False)
    parser.add_argument('-coords', '--convert_coords', help='Flag to convert coordinates to UTM', required=False)
    return parser
        
def main():
    parser = get_parser()
    args = parser.parse_args()
    in_fn = args.input_file
    l=args.left
    b=args.bottom
    r=args.right
    t=args.top
    z=args.get_utm_zone
    c=args.convert_coords
    
    run(in_fn=in_fn, l=l, b=b, r=r, t=t, z=z, c=c)
    
if __name__ == "__main__":    
    main()
