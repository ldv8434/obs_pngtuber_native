from ctypes import *
from ctypes.util import find_library
from types import SimpleNamespace
import obspython as obs
import time
import os.path

image_filter = "All formats (*.bmp *.tga *.png *.jpeg *.jpg *.gif *.psd *.webp);;\
BMP Files (*.bmp);;\
Targa Files (*.tga);;PNG Files (*.png);;\
JPEG Files (*.jpeg *.jpg);;\
GIF Files (*.gif);;PSD Files (*.psd);;\
WebP Files (*.webp);;All Files (*.*);"

def update_pngtuber(db_level):
	global png_active
	global png_inactive
	global threshold
	global hold_time
	global pngtuber_source
	global start_time
	global previous_state

	pngtuber_source_obs = obs.obs_get_source_by_name(pngtuber_source)
	#audio_source_obs = obs.obs_get_source_by_name(str(audio_source))

	# make sure images weren't deleted
	valid_images = False
	if os.path.exists(png_active) and os.path.exists(png_inactive):
		valid_images = True
	else:
		print("invalid path to pngtuber images!!")

	# handle hold time
	now = time.time()
	if time != 0 and ((now - start_time) < hold_time*0.001):
		if db_level > threshold and db_level != 999:
			start_time = time.time()
	elif pngtuber_source_obs is not None and valid_images:
		#print("Settings:")
		settings = obs.obs_source_get_settings(pngtuber_source_obs)
		#print(settings)
		if db_level > threshold and db_level != 999:
			obs.obs_data_set_string(settings, "file", png_active)
			start_time = time.time()
			current_state = "active"
		else:
			obs.obs_data_set_string(settings, "file", png_inactive)
			start_time = 0
			current_state = "inactive"
		if previous_state != current_state:
			obs.obs_source_update(pngtuber_source_obs, settings)
			previous_state = current_state
		obs.obs_data_release(settings)
		obs.obs_source_release(pngtuber_source_obs)

def refresh_pressed(props, prop):
	update_pngtuber(-60)
	G.lock = False
	g_obs_volmeter_remove_callback(G.volmeter, volmeter_callback, None)
	g_obs_volmeter_destroy(G.volmeter)

# ------------------------------------------------------------

def script_description():
	return "PNGtuber script\n\nNote: minimum supported update time is 50ms"

def script_update(settings):
	global png_active
	global png_inactive
	global threshold
	global hold_time
	global pngtuber_source
	global audio_source
	global start_time
	global previous_state

	previous_state = "active"

	png_active = obs.obs_data_get_string(settings, "png_active")
	png_inactive = obs.obs_data_get_string(settings, "png_inactive")
	threshold = obs.obs_data_get_int(settings, "threshold")
	hold_time = obs.obs_data_get_int(settings, "hold_time")
	pngtuber_source = obs.obs_data_get_string(settings, "pngtuber_source")
	audio_source = obs.obs_data_get_string(settings, "audio_source")

	start_time = 0


def script_defaults(settings):
	obs.obs_data_set_default_int(settings, "threshold", -50)
	obs.obs_data_set_default_int(settings, "hold_time", 500)

def script_properties():
	props = obs.obs_properties_create()

	obs.obs_properties_add_path(props,"png_active","PNG (active)",obs.OBS_PATH_FILE,image_filter,None)
	obs.obs_properties_add_path(props,"png_inactive","PNG (inactive)",obs.OBS_PATH_FILE,image_filter,None)

	# get a list of image sources for the user to pick from
	image_source_list_property = obs.obs_properties_add_list(props, "pngtuber_source", "Image Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	sources = obs.obs_enum_sources()
	if sources is not None:
		for source in sources:
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id == "image_source":
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(image_source_list_property, name, name)

		obs.source_list_release(sources)

	obs.obs_properties_add_int_slider(props, "threshold", "Audio Threshold", -60,0,1)
	obs.obs_properties_add_int(props, "hold_time", "Hold Time (ms)", 0,5000,10)

	# get a list of audio sources for the user to pick from
	audio_source_list_property = obs.obs_properties_add_list(props, "audio_source", "Audio Source", obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)
	sources = obs.obs_enum_sources()
	if sources is not None:
		for source in sources:
			source_id = obs.obs_source_get_unversioned_id(source)
			if source_id in ["pulse_input_capture", "pulse_output_capture", "alsa_input_capture", "ffmpeg_source"]:
				name = obs.obs_source_get_name(source)
				obs.obs_property_list_add_string(audio_source_list_property, name, name)

		obs.source_list_release(sources)

	obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
	return props

# ------------------------------------------------------------------
# FROM OBS SCRIPTING CHEAT SHEET EXAMPLES
obsffi = CDLL(find_library("obs"))
G = SimpleNamespace()

def wrap(funcname, restype, argtypes):
	"""Simplify wrapping ctypes functions in obsffi"""
	func = getattr(obsffi, funcname)
	func.restype = restype
	func.argtypes = argtypes
	globals()["g_" + funcname] = func

class Source(Structure):
	pass

class Volmeter(Structure):
	pass

volmeter_callback_t = CFUNCTYPE(
	None, c_void_p, POINTER(c_float), POINTER(c_float), POINTER(c_float)
)
wrap("obs_get_source_by_name", POINTER(Source), argtypes=[c_char_p])
wrap("obs_source_release", None, argtypes=[POINTER(Source)])
wrap("obs_volmeter_create", POINTER(Volmeter), argtypes=[c_int])
wrap("obs_volmeter_destroy", None, argtypes=[POINTER(Volmeter)])
wrap(
	"obs_volmeter_add_callback",
	None,
	argtypes=[POINTER(Volmeter), volmeter_callback_t, c_void_p],
)
wrap(
	"obs_volmeter_remove_callback",
	None,
	argtypes=[POINTER(Volmeter), volmeter_callback_t, c_void_p],
)
wrap(
	"obs_volmeter_attach_source",
	c_bool,
	argtypes=[POINTER(Volmeter), POINTER(Source)],
)

@volmeter_callback_t
def volmeter_callback(data, mag, peak, input):
	G.noise = float(peak[0])


OBS_FADER_LOG = 2
G.lock = False
G.start_delay = 5
G.duration = 0
G.noise = 999
G.tick = 100
G.tick_mili = G.tick * 0.001
G.interval_sec = 0.05
G.tick_acc = 0
G.volmeter = "not yet initialized volmeter instance"
G.callback = update_pngtuber

def event_loop():
	global audio_source
	"""wait n seconds, then execute callback with db volume level within interval"""
	if G.duration > G.start_delay:
		if not G.lock:
			#print("setting volmeter")
			source = g_obs_get_source_by_name(audio_source.encode("utf-8"))
			G.volmeter = g_obs_volmeter_create(OBS_FADER_LOG)
			g_obs_volmeter_add_callback(G.volmeter, volmeter_callback, None)
			if g_obs_volmeter_attach_source(G.volmeter, source):
				g_obs_source_release(source)
				G.lock = True
				print("Attached to source")
				return
		G.tick_acc += G.tick_mili
		if G.tick_acc > G.interval_sec:
			G.callback(G.noise)
			G.tick_acc = 0
	else:
		G.duration += G.tick_mili


def script_unload():
	if G.volmeter != "not yet initialized volmeter instance":
		g_obs_volmeter_remove_callback(G.volmeter, volmeter_callback, None)
		g_obs_volmeter_destroy(G.volmeter)
		#print("Removed volmeter & volmeter_callback")

# register event_loop to run every G.tick (miliseconds)
obs.timer_add(event_loop, G.tick)

### END FROM

# ------------------------------------------------------------
