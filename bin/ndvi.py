#!/usr/bin/env python

# Script to calculate Normalized Difference Vegetation Index from input imagery (with WV-2 and WV-3 MS band or single-band inputs).
# NDVI = (red - nir) / (red + nir)
    
import argparse
import numpy as np
import rasterio as rio
import sys

def read_file(fn):
    with rio.open(fn) as f:
        arr=f.read()
        prf=f.profile
        ndv=f.nodata
    return arr, prf, ndv
    
def calc_ndvi(red_arr, nir1_arr, r_ndv=None, nir1_ndv=None):
    # Calculate NDVI
    ndvi = (nir1_arr - red_arr) / (nir1_arr + red_arr)

    # Create normalized ndvi array from 0-1 for further processing with min-max scaling
    ndvi_norm = (ndvi+1)/2

    if (r_ndv is None) & (nir1_ndv is None):
        ndsi_ndv=9999
    else:
        ndsi_ndv=r_ndv
        
    # Mask with ndv areas from original arrays
    ndvi[red_arr==r_ndv]=r_ndv
    ndvi[nir1_arr==nir1_ndv]=nir1_ndv

    ndvi_norm[red_arr==r_ndv]=r_ndv
    ndvi_norm[nir1_arr==nir1_ndv]=nir1_ndv
    
    return ndvi, ndvi_norm

def run(multi_band_file, out_fn, nir1_fn, red_fn, px_res, modifier):
    try:
        if (multi_band_file is not None) & (modifier is not None):
            red_arr, prf, r_ndv = read_file(multi_band_file[:-4] + "_b5_" + modifier + "_refl.tif")
            RE_arr, _, RE_ndv = read_file(multi_band_file[:-4] + "_b6_" + modifier + "_refl.tif")        
            nir1_arr, _, nir1_ndv = read_file(multi_band_file[:-4] + "_b7_" + modifier + "_refl.tif")
        elif (red_fn is not None) & (nir1_fn is not None):
            red_arr, prf, r_ndv = read_file(red_fn)
            nir1_arr, _, nir1_ndv = read_file(nir1_fn)
        else:
            sys.exit("Check input files, missing proper input")
    
        ndvi, ndvi_norm = calc_ndvi(red_arr, nir1_arr, r_ndv, nir1_ndv)
        ndvi_RE, ndvi_norm_RE = calc_ndvi(RE_arr, nir1_arr, RE_ndv, nir1_ndv)

        # Write NDVI arrays to file
        try:
            with rio.Env():
                prf.update(
                    dtype=rio.float32,
                    count=1,
                    compress='lzw')
                with rio.open(out_fn, 'w', **prf) as dst:
                    dst.write(np.squeeze(ndvi).astype(rio.float32), 1)
                with rio.open(out_fn[:-4]+"_minmax.tif", 'w', **prf) as dst:
                    dst.write(np.squeeze(ndvi_norm).astype(rio.float32), 1)

                with rio.open(out_fn[:-4]+"_RE.tif", 'w', **prf) as dst:
                    dst.write(np.squeeze(ndvi_RE).astype(rio.float32), 1)
                with rio.open(out_fn[:-4]+"_RE_minmax.tif", 'w', **prf) as dst:
                    dst.write(np.squeeze(ndvi_norm_RE).astype(rio.float32), 1)
        except:
            print("Cannot write out calculated NDVI")
    except:
        print("Cannot calculate NDVI, check inputs") 

def get_parser():
    parser = argparse.ArgumentParser(description='Normalized Difference Vegetation Index Calculation Script')
    parser.add_argument('-in', '--MS_input_file', help='Multiband MS image file', required=False)
    parser.add_argument('-out', '--output_file', help='NDVI output filename', default="ndvi.tif",  required=False)
    parser.add_argument('-r', '--red_band', help='Single-band red input', required=False)
    parser.add_argument('-n', '--nir_band', help='Single-band NIR channel input', required=False)
    parser.add_argument('-res', '--px_res', help='Pixel resolution, default is 1.2m', default="1.2", required=False)
    parser.add_argument('-m', '--mod', help='Modifiers to single band filenames')
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    in_fn = args.MS_input_file
    out_fn = args.output_file

    if out_fn is None:
        out_fn='ndvi.tif'

    nir1_fn=args.nir_band
    red_fn=args.red_band
    px_res=args.px_res

    # Mosaicked handling
    if (args.mod == "None") | (args.mod is None):
        modifier=px_res[0]+px_res[-1]
    else:
        modifier=args.mod + "_" + px_res[0]+px_res[-1]

#     print(in_fn, out_fn, nir1_fn, red_fn, px_res, modifier)
    run(in_fn, out_fn, nir1_fn, red_fn, px_res, modifier)
    
if __name__ == "__main__":    
    main()