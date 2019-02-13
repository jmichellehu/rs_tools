#### Repository for general remote sensing scripts

Includes top-of-atmosphere (TOA) reflectance calculations for Landsat 8 (currently requires user input from included MTL, XML files, data scraping code in the future) and WorldView-3 input tiffs. Most functions in WorldView-3 TOA calculations adapted from dshean's dgtools repo.


##### *Usage:*

- Landsat 8
***from command line***
python L8_TOA_refl.py -in --multiband_tiff -M --reflectance_multiplication_value -A --reflectance_addition_value -sun --sun_elevation -out --output_toa_refl_filename

- WorldView-3
***from command line***
python wv3_TOA_refl.py -in --single_band_tiff -in_band --band_code -in_x --XML_filename -out --output_toa_refl_filename


##### Required:
  - gdal (https://www.gdal.org/)
  - geoio (https://github.com/DigitalGlobe/geoio)
