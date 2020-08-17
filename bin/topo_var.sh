#!/bin/bash

# Script to calculate topographic variability from input digital elevation model

# Usage:
# ./topo_var.sh dem_raster

# input = dem_file
# outputs = dem_slope.tif
        # dem_aspect.tif
        # dem_TRI.tif
        # dem_roughness.tif

set -e

# Base image filenames (.tif)
dem=$1

# Check for correct number of inputs
if [ "$#" -lt 1 ] ; then
  echo "Usage is \`$(basename $0) dem\`"
  exit
fi

echo "Executing: topo_var.sh $1"
echo "Calculating topographic variability dem products"

# Slope map
gdaldem slope $dem ${dem%.*}_slope.tif

# Aspect map
gdaldem aspect $dem ${dem%.*}_aspect.tif

# Terrain Ruggedness Index (TRI): Terrain Ruggedness Index, which is defined as the mean difference between a central pixel and its surrounding cells
gdaldem TRI $dem ${dem%.*}_TRI.tif

# Topographic roughness: 3x3 grid around center pixel (8 pixels in neighborhood) with difference in elevation range indicating degree of roughness
gdaldem roughness $dem ${dem%.*}_roughness.tif
