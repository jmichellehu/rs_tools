#!/usr/bin/env python
# requires gdal, uses and modifies functions created by dshean (dgtools repo)

# This script calculates TOA reflectance for WorldView-2 and -3 Level 1-B imagery using user input XML file.  Calibration factors (irradiance, gain, and offset) are obtained from DG_ABSCALVAL_2016v0 - https://dg-cms-uploads-production.s3.amazonaws.com/uploads/document/file/209/ABSRADCAL_FLEET_2016v0_Rel20170606.pdf

# import libraries
import argparse
from datetime import datetime
import numpy as np
import rasterio as rio

# Irradiance dictionary band values
EsunDict = {
'WV02_BAND_P':1571.36,
'WV02_BAND_C':1773.81,
'WV02_BAND_B':2007.27,
'WV02_BAND_G':1829.62,
'WV02_BAND_Y':1701.85,
'WV02_BAND_R':1538.85,
'WV02_BAND_RE':1346.09,
'WV02_BAND_N':1053.21,
'WV02_BAND_N2':856.599,

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

#WV Gain band values
GainDict = {
'WV02_BAND_P':0.942,
'WV02_BAND_C':1.151,
'WV02_BAND_B':0.988,
'WV02_BAND_G':0.936,
'WV02_BAND_Y':0.949,
'WV02_BAND_R':0.952,
'WV02_BAND_RE':0.974,
'WV02_BAND_N':0.961,
'WV02_BAND_N2':1.002,

'WV03_BAND_P':0.950,
'WV03_BAND_C':0.905,
'WV03_BAND_B':0.940,
'WV03_BAND_G':0.938,
'WV03_BAND_Y':0.962,
'WV03_BAND_R':0.964,
'WV03_BAND_RE':1.000,
'WV03_BAND_N':0.961,
'WV03_BAND_N2':0.978,

'WV03_BAND_S1':1.200,
'WV03_BAND_S2':1.227,
'WV03_BAND_S3':1.199,
'WV03_BAND_S4':1.196,
'WV03_BAND_S5':1.262,
'WV03_BAND_S6':1.314,
'WV03_BAND_S7':1.346,
'WV03_BAND_S8':1.376,
}

#WV Offset band values
OffsetDict = {
'WV02_BAND_P':-2.704,
'WV02_BAND_C':-7.478,
'WV02_BAND_B':-5.736,
'WV02_BAND_G':-3.546,
'WV02_BAND_Y':-3.564,
'WV02_BAND_R':-2.512,
'WV02_BAND_RE':-4.120,
'WV02_BAND_N':-3.300,
'WV02_BAND_N2':-2.891,

'WV03_BAND_P':-3.629,
'WV03_BAND_C':-8.604,
'WV03_BAND_B':-5.809,
'WV03_BAND_G':-4.996,
'WV03_BAND_Y':-3.649,
'WV03_BAND_R':-3.021,
'WV03_BAND_RE':-4.521,
'WV03_BAND_N':-5.522,
'WV03_BAND_N2':-2.992,

'WV03_BAND_S1':-5.546,
'WV03_BAND_S2':-2.600,
'WV03_BAND_S3':-2.309,
'WV03_BAND_S4':-1.676,
'WV03_BAND_S5':-0.705,
'WV03_BAND_S6':-0.669,
'WV03_BAND_S7':-0.512,
'WV03_BAND_S8':-0.372,
}

# WV order (0-based indexing)
OrderDict = {
'WV02_BAND_P':0,
    
'WV02_BAND_C':0,
'WV02_BAND_B':1,
'WV02_BAND_G':2,
'WV02_BAND_Y':3,
'WV02_BAND_R':4,
'WV02_BAND_RE':5,
'WV02_BAND_N':6,
'WV02_BAND_N2':7,

'WV03_BAND_P':0,
    
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

def toa_rad(xml_fn, band):
    """Calculate scaling factor abs/effbw for top-of-atmosphere radiance
    """
    sat = getTag(xml_fn, 'SATID')
    band = band.upper()
    key = '%s_BAND_%s' % (sat, band)
    abscal = np.array((getAllTag(xml_fn, 'ABSCALFACTOR')), dtype=float)
    effbw = np.array((getAllTag(xml_fn, 'EFFECTIVEBANDWIDTH')), dtype=float)
#     print(abscal, effbw)
    #Multiply L1B DN by this to obtain top-of-atmosphere spectral radiance image pixels
    toa_rad_coeff_list = abscal/effbw
    toa_rad_coeff = toa_rad_coeff_list[OrderDict[key]]
    return toa_rad_coeff

def toa_refl(xml_fn, band, data):
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
#     print(sat, key, Esun, gain, offset)
    msunel = float(getTag(xml_fn, 'MEANSUNEL'))
    sunang = 90.0 - msunel
    dt = xml_dt(xml_fn)
    esd = calcEarthSunDist(dt)
#     print(msunel, sunang, dt, esd)
    toa_rad_coeff = toa_rad(xml_fn, band)
#     print("AbsCalFactor/EffBW is ", toa_rad_coeff)
    TOA_arr = (gain * data * toa_rad_coeff + offset) * (esd**2 * np.pi) / (Esun * np.cos(np.radians(sunang)))
    return TOA_arr

def calcEarthSunDist(dt):
    """Calculate Earth-Sun distance"""
    #Astronomical Units (AU), should have a value between 0.983 and 1.017
    year = dt.year
    month = dt.month
    day = dt.day
    hr = dt.hour
    minute = dt.minute
    sec = dt.second
    ut = hr + (minute/60.) + (sec/3600.)
    #print out
    if month <= 2:
        year = year - 1
        month = month + 12
    a = int(year/100.)
    b = 2 - a + int(a/4.)
    jd = int(365.25*(year+4716)) + int(30.6001*(month+1)) + day + (ut/24) + b - 1524.5
    g = 357.529 + 0.98560028 * (jd-2451545.0)
    d = 1.00014 - 0.01671 * np.cos(np.radians(g)) - 0.00014 * np.cos(np.radians(2*g))
#     print("Earth-sun distance", d)
    return d

def get_parser():
    parser = argparse.ArgumentParser(description='GeoTiff WorldView Multispectral Image to TOA Reflection Image Conversion Script')
    parser.add_argument('-in', '--input_file', help='GeoTiff multi band MS image file', required=True)
    parser.add_argument('-in_band', '--input_band', help='GeoTiff multi band', required=True)
    parser.add_argument('-in_x', '--input_xml', help='GeoTiff multi band xml file', required=True)
    parser.add_argument('-out', '--output_file', help='Where TOA reflectance image is to be saved', required=True)
    return parser

def main(in_fn, xml_fn, in_band, out_fn):
    with rio.open(in_fn) as f:
        data=f.read(1)
        ndv=f.nodata
        prof=f.profile

    TOA_arr=toa_refl(xml_fn, in_band, data)
    TOA_arr[data==ndv] = ndv

    with rio.Env():
        profile = prof
        profile.update(
            dtype=rio.float32,
            count=1,
            compress='lzw',
            interleave='band',
            tiled=True,
            blockxsize=512,
            blockysize=512,
            BIGTIFF='YES'
        )

        with rio.open(out_fn, 'w', **profile) as dst:
            dst.write(np.squeeze(TOA_arr).astype(rio.float32), 1)

if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    
    in_fn = args.input_file
    in_band = args.input_band
    xml_fn = args.input_xml
    out_fn = args.output_file
    
    main(in_fn, xml_fn, in_band, out_fn)
