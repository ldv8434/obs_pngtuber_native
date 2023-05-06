# obs_pngtuber_native
A script to implement PNGtuber-like functions into OBS without a browser source. 

This script will monitor an audio source and modify an image source if that audio source is above a certain threshold. The primary purpose for this is to act as a PNGtuber talking indicator, though you can use it for other purposes as well. "Blinking" part of the script, but can be implemented by using a .gif file as the source image (despite the label that says it's a PNG).

Features a menu that allows you to configure audio source, image source, images, audio threshhold, and image hold time (for breaks in speech).  

## Credits
The heavy lifting of detecting audio levels is taken from upgradeQ's examples, available here: [https://github.com/upgradeQ/OBS-Studio-Python-Scripting-Cheatsheet-obspython-Examples-of-API/blob/master/src/volmeter_via_ffi.py](https://github.com/upgradeQ/OBS-Studio-Python-Scripting-Cheatsheet-obspython-Examples-of-API/blob/master/src/volmeter_via_ffi.py)
