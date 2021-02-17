#!/usr/bin/env python

# Script to calculate Normalized Difference Water Index from WV-3 top-of-atmosphere reflectance imagery (with WV-2 and WV-3 MS band or single-band inputs).
# ***McFeeters version

# USAGE: 
# ndwi.py -in ms_fn.tif -out out_NDWI.tif -m 'mos'
# NDWI = ( green - NIR1 ) / ( green + NIR1 )
    
import argparse
import numpy as np
import rasterio as rio
import sys

def get_parser():
    parser = argparse.ArgumentParser(description='Normalized Difference Water Index Calculation Script')
    parser.add_argument('-in', '--MS_input_file', help='Multiband MS image file', required=False)
    parser.add_argument('-out', '--output_file', help='NDVI output filename', default="ndvi.tif",  required=False)
    parser.add_argument('-g', '--green_band', help='Single-band green input', required=False)
    parser.add_argument('-n', '--nir_band', help='Single-band NIR channel input', required=False)
    parser.add_argument('-res', '--px_res', help='Pixel resolution, default is 1.2m', default="1.2", required=False)
    parser.add_argument('-m', '--mod', help='Modifiers to single band filenames')
    return parser

def read_file(fn):
    with rio.open(fn) as f:
        arr=f.read()
        prf=f.profile
        ndv=f.nodata
    return arr, prf, ndv
    
def calc_ndwi(green_arr, nir1_arr, g_ndv=None, nir1_ndv=None):
    # Calculate NDWI
    ndwi = (green_arr - nir1_arr) / (green_arr + nir1_arr)

    # Create normalized ndwi array from 0-1 for further processing with min-max scaling
    ndwi_norm = (ndwi+1)/2

    if (g_ndv is None) & (nir1_ndv is None):
        ndwi_ndv=9999
    else:
        ndwi_ndv=g_ndv
        
    # Mask with ndv areas from original arrays
    ndwi[green_arr==g_ndv]=g_ndv
    ndwi[nir1_arr==nir1_ndv]=nir1_ndv

    ndwi_norm[green_arr==g_ndv]=g_ndv
    ndwi_norm[nir1_arr==nir1_ndv]=nir1_ndv
    
    return ndwi, ndwi_norm

def run(multi_band_file=None, out_fn=None, 
        nir1_fn=None, green_fn=None, 
        px_res="1.2", modifier=None):
    print(multi_band_file, out_fn, nir1_fn, green_fn, px_res, modifier)
    try:
        if (multi_band_file is not None) & (modifier is not None):
            print(multi_band_file[:-4] + "_b3_" + modifier + "_refl.tif")
            green_arr, prf, g_ndv = read_file(multi_band_file[:-4] + "_b3_" + modifier + "_refl.tif")
            nir1_arr, _, nir1_ndv = read_file(multi_band_file[:-4] + "_b7_" + modifier + "_refl.tif")
        elif (green_fn is not None) & (nir1_fn is not None):
            green_arr, prf, g_ndv = read_file(green_fn)
            nir1_arr, _, nir1_ndv = read_file(nir1_fn)
        else:
            sys.exit("Check input files, missing proper input")

        ndwi, ndwi_norm = calc_ndwi(green_arr, nir1_arr, g_ndv, nir1_ndv)

        # Write NDWI arrays to file
        try:
            with rio.Env():
                prf.update(
                    dtype=rio.float32,
                    count=1,
                    compress='lzw')
                with rio.open(out_fn, 'w', **prf) as dst:
                    dst.write(np.squeeze(ndwi).astype(rio.float32), 1)
                with rio.open(out_fn[:-4]+"_minmax.tif", 'w', **prf) as dst:
                    dst.write(np.squeeze(ndwi_norm).astype(rio.float32), 1)
        except:
            print("Cannot write out calculated NDWI")
    except:
        print("Cannot calculate NDWI, check inputs") 

def main():
    parser = get_parser()
    args = parser.parse_args()
    in_fn = args.MS_input_file
    out_fn = args.output_file
    mod = args.mod

    if out_fn is None:
        out_fn='ndwi.tif'

    nir1_fn=args.nir_band
    green_fn=args.green_band
    px_res=args.px_res

    # Mosaicked handling
    if not mod:
        modifier=px_res[0]+px_res[-1]
    else:
        modifier=mod + "_" + px_res[0]+px_res[-1]

    print(in_fn, out_fn, nir1_fn, green_fn, px_res, modifier)
    
    run(multi_band_file=in_fn, out_fn=out_fn, 
        nir1_fn=nir1_fn, green_fn=green_fn, 
        px_res=px_res, modifier=modifier)
    
if __name__ == "__main__":    
    main()
