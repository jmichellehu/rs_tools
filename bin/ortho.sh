#! /bin/bash

# Script to identify and NED tiles that intersect with input imagery and orthorectify

# Usage:
# ./ortho.sh img.NTF

### # TODO:

set -e

# Input image
img=$1
xml=${img%.*}.xml

echo ./ortho.sh ${img}

# cleanup=true

# Extract geographic coordinates for the input image
GCS_file=GCS_coords.txt
NED_names=NED.txt
utm_file=utm_zone.txt
dem_list=dem_list.txt

# Extract UTM zone epsg code from image center
python $HOME/git_dirs/rs_tools/bin/utm_convert.py -in ${img} | tail -n 1 | tee ${utm_file} 
while read z
do
  zone=${z}
done < ${utm_file}

python $HOME/git_dirs/NED_download/bin/get_NED.py -in ${img} -NED 13 2>&1 | tee ${GCS_file}
while read NED_filename
do
    NED=$(echo ${NED_filename} | tr "/" "\n" | tail -1)
    echo "NED is ${NED}"
    python $HOME/git_dirs/rs_tools/bin/utm_convert.py -in ${NED%.*}.img | tail -n 1 | tee ${utm_file} 

    while read z
    do
      zone=${z}
    done < ${utm_file}
    dem=${NED%.*}-adj_${zone}.tif
    echo ${dem} >> ${dem_list}
    
    if [ ! -f ${dem} ] ; then
        if [ ! -f ${NED%.*}-adj.img ] ; then
            dem_geoid --reverse-adjustment ${NED%.*}.img ; 
        fi
        gdalwarp -co COMPRESS=LZW -co TILED=YES -co BIGTIFF=IF_SAFER -overwrite -r cubic -t_srs EPSG:${zone} -dstnodata -9999 -tr 10 10 ${NED%.*}-adj.tif ${dem}
    
    fi
    
done < ${GCS_file}

# dem_vrt=${img%.*}_NED_13.vrt
# if [ ! -f ${dem_vrt} ]; then
#     echo "Building vrt of dems..."
#     # Build vrt of image
#     gdalbuildvrt -input_file_list ${dem_list} ${dem_vrt}
# else
#     echo "NED vrt already exists"
# fi

# $HOME/git_dirs/wv3_classification/code/working/wv3_ortho_resample.sh $img $dem_vrt "1.24" EPSG:${zone}

# if $cleanup ; then
#     rm ${utm_file} ${GCS_file} ${NED_names} ${utm_file} ${dem_list}
# fi
