# tif2png
TIF/TIFF to PNG converter, via an interactive Python script. I created it for converting satellite/arial imagery to more compatible, smaller files.

## Main Script
If you want to just convert TIFFs to PNGs, install the dependencies via ```pip install -r requirements.txt``` and run ```python tif_converter.py```.

## For Multispectral Images
If you are working with satellite images, like multispectral ones (Sentinel-2, etc.) you will want to run this script to prepare the tif files.
1. First install the dependencies (install the requirements.txt first) with ```pip install rasterio numpy```.
2. Then run ```python multispectral_to_rgb.py```. It will ask for the path to your tif file. It only supports one at a time for now.
3. Move the output tif file to the tifs/ folder, or the folder containing your RGB tif files to convert.
4. Run ```python tif_converter.py``` as normal.

## For SAR Images
1. First install the dependencies, they are mostly the same as multispectral images. If you installed those, then the only dependency you need is scipy, which you can install with ```pip install scipy```.
2. Then run sar_to_rgb.py.
3. Same steps as 3 and 4 in the multispectral steps.

Made with ❤️ by Alex Scott