#!/usr/bin/env python
# requires gdal and geoio from https://github.com/DigitalGlobe/geoio
# uses functions created by dshean (dgtools github repo)

# This script calculates TOA reflectance for WorldView-3 Level 1-B imagery using user input XML file

# import libraries
import math
import geoio
from gdalconst import *
import argparse, numpy as np, gdal, struct, sys
from datetime import datetime, timedelta

# Have user define input bands and output filename
parser = argparse.ArgumentParser(description='GeoTiff WV-3 Multispectral Image to TOA Reflection Image Conversion Script')
parser.add_argument('-in', '--input_file', help='GeoTiff multi band MS image file', required=True)
parser.add_argument('-in_band', '--input_band', help='GeoTiff multi band', required=True)
parser.add_argument('-in_x', '--input_xml', help='GeoTiff multi band xml file', required=True)
parser.add_argument('-out', '--output_file', help='Where TOA reflectance image is to be saved', required=True)
args = parser.parse_args()

in_fn = args.input_file
in_band = args.input_band
xml_fn = args.input_xml
out_fn = args.output_file

# Irradiance dictionary band values
EsunDict = {
'WV03_BAND_P':1574.41,
'WV03_BAND_C':1757.89,
'WV03_BAND_B':2004.61,
'WV03_BAND_G':1830.18,
'WV03_BAND_Y':1712.07,
'WV03_BAND_R':1535.33,
'WV03_BAND_RE':1348.08,
'WV03_BAND_N':1055.94,
'WV03_BAND_N2':858.77,
'WV03_BAND_S1':479.019,
'WV03_BAND_S2':263.797,
'WV03_BAND_S3':225.283,
'WV03_BAND_S4':197.552,
'WV03_BAND_S5':90.4178,
'WV03_BAND_S6':85.0642,
'WV03_BAND_S7':76.9507,
'WV03_BAND_S8':68.0988
}
#WV3 Gain band values
GainDict = {
'WV03_BAND_P':0.923,
'WV03_BAND_C':0.863,
'WV03_BAND_B':0.905,
'WV03_BAND_G':0.907,
'WV03_BAND_Y':0.938,
'WV03_BAND_R':0.945,
'WV03_BAND_RE':0.980,
'WV03_BAND_N':0.982,
'WV03_BAND_N2':0.954,
'WV03_BAND_S1':1.160,
'WV03_BAND_S2':1.184,
'WV03_BAND_S3':1.173,
'WV03_BAND_S4':1.187,
'WV03_BAND_S5':1.286,
'WV03_BAND_S6':1.336,
'WV03_BAND_S7':1.340,
'WV03_BAND_S8':1.392
}
#WV3 Offset band values
OffsetDict = {
'WV03_BAND_P':-1.700,
'WV03_BAND_C':-7.154,
'WV03_BAND_B':-4.189,
'WV03_BAND_G':-3.287,
'WV03_BAND_Y':-1.816,
'WV03_BAND_R':-1.350,
'WV03_OFFSET_RE':-2.617,
'WV03_BAND_N':-3.752,
'WV03_BAND_N2':-1.507,
'WV03_BAND_S1':-4.479,
'WV03_BAND_S2':-2.248,
'WV03_BAND_S3':-1.806,
'WV03_BAND_S4':-1.507,
'WV03_BAND_S5':-0.622,
'WV03_BAND_S6':-0.605,
'WV03_BAND_S7':-0.423,
'WV03_BAND_S8':-0.302,
}

# WV order (0-based indexing)
OrderDict = {
'WV03_BAND_C':0,
'WV03_BAND_B':1,
'WV03_BAND_G':2,
'WV03_BAND_Y':3,
'WV03_BAND_R':4,
'WV03_BAND_RE':5,
'WV03_BAND_N':6,
'WV03_BAND_N2':7,
'WV03_BAND_S1':0,
'WV03_BAND_S2':1,
'WV03_BAND_S3':2,
'WV03_BAND_S4':3,
'WV03_BAND_S5':4,
'WV03_BAND_S6':5,
'WV03_BAND_S7':6,
'WV03_BAND_S8':7
}


img=geoio.GeoImage(in_fn)
# open tif as numpy array
data=img.get_data()

def getTag(xml_fn, tag):
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_fn)
    #Want to check to make sure tree contains tag
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
    #Want to check to make sure tree contains tag
    elem = tree.findall('.//%s' % tag)
    return [i.text for i in elem]

def toa_rad(xml_fn, band=in_band):
    """Calculate scaling factor abs/effbw for top-of-atmosphere radiance
    """
    sat = getTag(xml_fn, 'SATID')
    band = band.upper()
    key = '%s_BAND_%s' % (sat, band)

    abscal = np.array((getAllTag(xml_fn, 'ABSCALFACTOR')), dtype=float)
    effbw = np.array((getAllTag(xml_fn, 'EFFECTIVEBANDWIDTH')), dtype=float)
    #Multiply L1B DN by this to obtain top-of-atmosphere spectral radiance image pixels
    toa_rad_coeff_list = abscal/effbw
    toa_rad_coeff = toa_rad_coeff_list[OrderDict[key]]
    return toa_rad_coeff

def toa_refl(xml_fn=xml_fn, band=in_band):
    """Calculate scaling factor for top-of-atmosphere reflectance
    """
    #These need to be pulled out by individual band
    sat = getTag(xml_fn, 'SATID')
    if band is None:
        band = getTag(xml_fn, 'BANDID')
    band = band.upper()
    key = '%s_BAND_%s' % (sat, band)
    Esun = EsunDict[key]
    gain = GainDict[key]
    offset = OffsetDict[key]

    print(sat, key, Esun, gain, offset)
    msunel = float(getTag(xml_fn, 'MEANSUNEL'))
    sunang = 90.0 - msunel
    dt = xml_dt(xml_fn)
    esd = calcEarthSunDist(dt)
    print(msunel, sunang, dt, esd)
    toa_rad_coeff = toa_rad(xml_fn)

    print("AbsCalFactor/EffBW is ", toa_rad_coeff)

    TOA_refl = (gain * data * toa_rad_coeff + offset) * (esd**2 * np.pi) / (Esun * np.cos(np.radians(sunang)))
    img.write_img_like_this(out_fn, TOA_refl)

def calcEarthSunDist(dt):
    """Calculate Earth-Sun distance
    """
    #Astronomical Units (AU), should have a value between 0.983 and 1.017
    year = dt.year
    month = dt.month
    day = dt.day
    hr = dt.hour
    minute = dt.minute
    sec = dt.second
    ut = hr + (minute/60.) + (sec/3600.)
    #print ut
    if month <= 2:
        year = year - 1
        month = month + 12
    a = int(year/100.)
    b = 2 - a + int(a/4.)
    #jd = timelib.dt2jd(dt)
    jd = int(365.25*(year+4716)) + int(30.6001*(month+1)) + day + (ut/24) + b - 1524.5
    g = 357.529 + 0.98560028 * (jd-2451545.0)
    d = 1.00014 - 0.01671 * np.cos(np.radians(g)) - 0.00014 * np.cos(np.radians(2*g))
    return d
    print("Earth-sun distance", d)

toa_refl()
