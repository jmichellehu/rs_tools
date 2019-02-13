### Repository for general remote sensing scripts

Includes top-of-atmosphere (TOA) reflectance calculations for Landsat 8 and WorldView-3 input tiffs.  Requires corresponding MTL and XML files.  Most functions in WorldView-3 TOA calculations adapted from dshean's dgtools repo.


#### *Usage:*

- Landsat 8
*(from command line):*
python L8_TOA_refl.py -in --multiband_tiff -in_MTL --MTL_filename -out --output_toa_refl_filename

- WorldView-3
*(from command line):*
python wv3_TOA_refl.py -in --single_band_tiff -in_band --band_code -in_x --XML_filename -out --output_toa_refl_filename


#### Required:
  - gdal (https://www.gdal.org/)
  - geoio (https://github.com/DigitalGlobe/geoio)
