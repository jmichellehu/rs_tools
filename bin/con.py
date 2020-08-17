#!/usr/bin/env python
# requires gdal, uses and modifies functions created by dshean (dgtools repo)

# This script calculates TOA reflectance for WorldView-2 and -3 Level 1-B imagery using user input XML file.  Calibration factors (irradiance, gain, and offset) are obtained from DG_ABSCALVAL_2016v0 - https://dg-cms-uploads-production.s3.amazonaws.com/uploads/document/file/209/ABSRADCAL_FLEET_2016v0_Rel20170606.pdf

# import libraries
import rasterio
import sys
import concurrent.futures
from itertools import islice

# Have user define input bands and output filename
# parser = argparse.ArgumentParser(description='GeoTiff WorldView Multispectral Image to TOA Reflection Image Conversion Script')
# parser.add_argument('in', '--input_file', help='GeoTiff multi band MS image file')
# args = parser.parse_args()

# in_fn = args.input_file
# in_band = "C"

# in_dir="/"
# in_dir=in_dir.join(in_fn.split("/")[:-1])

# xml_fn = in_dir + "/" + in_fn.split("/")[-1][:-10]+".xml"
# out_fn = in_dir + "/" + in_fn.split("/")[-1][:-4]+"toa_concurrent.tif"

CHUNK = 100


def chunkify(iterable, chunk=CHUNK):
    it = iter(iterable)
    while True:
        piece = list(islice(it, chunk))
        if piece:
            yield piece
        else:
            return


def compute(path, window):
    """Simulates an expensive computation
    Gets source data for a window, sleeps, reverses bands.
    Note: Numpy ufuncs release GIL and are parallelizable.
    """
    with rasterio.open(path) as src:
        data = src.read(window=window)
#         fake_toa=data*10
        
    return data[::-1]


def main(infile, outfile, max_workers=1):

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

        with rasterio.open(infile) as src:

            with rasterio.open(outfile, "w", **src.profile) as dst:

                windows = [window for ij, window in dst.block_windows()]
                
                for chunk in [windows]:  # chunkify(windows):
                    print(chunk)

                    future_to_window = dict()

                    for window in chunk:
                        print(window)

                        future = executor.submit(compute, infile, window)
                        future_to_window[future] = window
                        
                    for future in concurrent.futures.as_completed(future_to_window):
                        window = future_to_window[future]
                        result = future.result()
                        dst.write(result, window=window)


if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser(description='GeoTiff WorldView Multispectral Image to TOA Reflection Image Conversion Script')
    parser.add_argument('input_file', help='GeoTiff multi band MS image file')
    parser.add_argument('-n', '--number', help='Number of workers', required=False)
    args = parser.parse_args()
    
    in_fn = args.input_file
    num = args.number
    
    if num is None:
        num = 4
    
    in_band = "C"
    in_dir="/"
    in_dir=in_dir.join(in_fn.split("/")[:-1])

    xml_fn = in_dir + "/" + in_fn.split("/")[-1][:-10]+".xml"
    out_fn = in_dir + "/" + in_fn.split("/")[-1][:-4]+"_toa_concurrent.tif"
    
    main(in_fn, out_fn, max_workers=int(num))
