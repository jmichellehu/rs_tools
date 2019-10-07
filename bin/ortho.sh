#! /bin/bash

# Script to identify and NED tiles that intersect with input imagery and orthorectify

# Usage:
# ./ortho.sh img.NTF

### # TODO:
# Need to incorporate handling for multiple dems --> vrt mosaic
# Need to put things into python scripts -- all these steps are unnecessary

set -e

# Input image
img=$1
xml=${img%.*}.xml

echo ./ortho.sh ${img}

# cleanup=true

# Extract geographic coordinates for the input image
utm_file=utm_zone.txt
NED_names=NED.txt

python $HOME/git_dirs/rs_tools/bin/utm_convert.py -in ${img} 2>&1 | tee ${utm_file}

# Extract geographic coordinates for the input image
GCS_file=GCS_coords.txt

python $HOME/git_dirs/NED_download/bin/get_NED.py -in ${img} -NED 13 2>&1 | tee ${GCS_file}

while read NED_filename
do
  NED=$(echo ${NED_filename} | tr "/" "\n" | tail -1)
done < ${GCS_file}

while read z
do
  zone=${z}
done < ${utm_file}

echo ${NED%.*}_${zone}.tif
dem=${NED%.*}_${zone}.tif

# Need to incorporate handling for multiple dems --> vrt mosaic
# dem=${img%.*}.vrt
# gdalbuildvrt -input_file_list ${NED_names}* ${img%.*}.vrt

$HOME/git_dirs/wv3_classification/code/working/wv3_ortho_resample.sh $img $dem "1.24" EPSG:${zone}

if $cleanup ; then
    rm ${utm_file}
fi
