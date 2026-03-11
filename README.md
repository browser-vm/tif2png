# tif2png
TIF/TIFF to PNG converter, via an interactive Python script.

## Main Script
If you want to just convert TIFFs to PNGs, install the dependencies via ```pip install -r requirements.txt``` and run ```python tif_converter.py```.

## For Multispectral Images
If you are working with satellite images, like multispectral ones (Sentinel-2, etc.) you will want to run this script to prepare the tif files.
1. First install the dependencies (install the requirements.txt first) with ```pip install rasterio numpy```.
2. Then run ```python multispectral_to_rgb.py```. It will ask for the path to your tif file. It only supports one at a time for now.
3. Move the output tif file to the tifs/ folder, or the folder containing your RGB tif files to convert.
4. Run ```python tif_converter.py``` as normal.

Made with ❤️ by Alex Scott