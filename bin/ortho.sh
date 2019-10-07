#! /bin/bash

# Script to identify and NED tiles that intersect with input imagery and orthorectify


### # TODO:
# Need to incorporate handling for multiple dems --> vrt mosaic
# Need to put things into python scripts -- all these steps are unnecessary

# Usage:
# ./ortho.sh img.NTF

set -e

# Input image
img=$1
xml=${img%.*}.xml

# cleanup=true

# Extract geographic coordinates for the input image
utm_file=utm_zone.txt
NED_names=NED.txt

python $HOME/git_dirs/rs_tools/bin/utm_convert.py -in ${img} 2>&1 | tee ${utm_file}

echo ${img}

while read z
do
  zone=${z}
done < ${utm_file}

while read n
do
  NED=${n}
done < ${NED_names}

echo ${NED%.*}_${zone}.tif
dem=${NED%.*}_${zone}.tif

# Need to incorporate handling for multiple dems --> vrt mosaic
# dem=${img%.*}.vrt
# gdalbuildvrt -input_file_list ${NED_names}* ${img%.*}.vrt

$HOME/git_dirs/wv3_classification/code/working/wv3_ortho_resample.sh $img $dem "1.24" EPSG:${zone}

if $cleanup ; then
    rm ${NED_names}
    rm ${utm_file}
fi
