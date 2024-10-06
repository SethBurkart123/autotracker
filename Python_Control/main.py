import glob
import os
import time
import AutotrackerKeyboard
from shared_state import SharedState
import logging
import subprocess
from api.api import API  # Import the API class
import sys

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize shared state
state = SharedState()

def find_usb_device():
    # Try ttyUSB* first
    usb_devices = glob.glob('/dev/ttyUSB*')
    if usb_devices:
        return usb_devices[0]
    
    mac_devices = glob.glob('/dev/cu.usbserial*')
    if mac_devices:
        return mac_devices[0]
    
    # If no ttyUSB* found, try ttyACM*
    acm_devices = glob.glob('/dev/ttyACM*')
    if acm_devices:
        return acm_devices[0]
    
    # If still no device found, check if we're on a Raspberry Pi
    if os.path.exists('/dev/serial0'):
        return '/dev/serial0'
    
    # No suitable device found
    return None

usb_device = find_usb_device()

if usb_device is None:
    print("No suitable USB device found. Please check your connections.")
    print("Available tty devices:")
    os.system('ls -l /dev/tty*')
    sys.exit(1)

try:
    Controller = AutotrackerKeyboard.Controller(usb_device)
    state.set_controller(Controller)
except Exception as e:
    print(f"Error initializing controller with device {usb_device}: {e}")
    print("Available tty devices:")
    os.system('ls -l /dev/tty*')
    sys.exit(1)

print(f"Successfully connected to {usb_device}")

# Attempt to connect to the first available camera
for i in range(len(state.cameras)):
    if state.connect_to_camera(i):
        break

if state.cam is None:
    print("No cameras available. Please check your camera IP addresses.")

# Initialize the API server
api_server = API(host='0.0.0.0', port=9000, controller=Controller, shared_state=state)
api_server.start()

# Initialize the camera function button color
def update_camera_function_button():
    current_camera_color = state.cameras[state.current_camera_index]['color']
    Controller.LED.update(3, 2, current_camera_color)

# Call this function to set the initial state
update_camera_function_button()

def update_led_for_camera_select():
    logging.debug("Updating LEDs for camera select mode")
    Controller.LED.clear_all()
    for i, camera in enumerate(state.cameras):
        y, x = i % 5, i // 5
        color = camera['color']
        if i == state.current_camera_index:
            Controller.LED.update(x, y, color)  # Full brightness
        else:
            dark_color = [int(c * 0.3) for c in color]  # 30% brightness for non-selected cameras
            Controller.LED.update(x, y, dark_color)
    update_camera_function_button()

def update_led_for_normal_mode():
    logging.debug("Updating LEDs for normal mode")
    Controller.LED.clear_all()
    update_camera_function_button()
    update_fast_mode_led()

def update_fast_mode_led():
    if state.fast_mode_active:
        Controller.LED.update(3, 4, [0, 0, 0])  # Black for fast mode
    else:
        Controller.LED.update(3, 4, [0, 255, 0])  # Green for normal mode

def update_led_for_preset_setting():
    logging.debug("Updating LEDs for preset setting mode")
    Controller.LED.clear_all()
    for i in range(10):  # Assuming 10 preset buttons
        y, x = i % 5, i // 5
        Controller.LED.update(x, y, [0, 0, 255])  # Blue color for preset buttons
    Controller.LED.update(3, 3, [255, 0, 0])  # Red color for preset setting button
    update_camera_function_button()

try:
    while True:
        if state.cam is None:
            time.sleep(1)
            continue

        if not Controller.are_threads_alive():
            print("One or more threads have crashed. Shutting down...")
            break

        # Camera select mode
        if Controller.inputCtrl.camera_select_mode:
            if not state.camera_select_mode:
                logging.debug("Entering camera select mode")
                state.camera_select_mode = True
                state.preset_setting_mode = False
                state.update_leds()
        elif Controller.inputCtrl.preset_setting_mode:
            if not state.preset_setting_mode:
                logging.debug("Entering preset setting mode")
                state.preset_setting_mode = True
                state.camera_select_mode = False
                state.update_leds()
        else:
            if state.camera_select_mode or state.preset_setting_mode:
                logging.debug("Exiting special modes")
                state.camera_select_mode = False
                state.preset_setting_mode = False
                state.update_leds()

        # Camera change handling
        if Controller.inputCtrl.camera_changed:
            new_camera_index = Controller.inputCtrl.selected_camera
            logging.info(f"Attempting to switch to camera {new_camera_index}")
            if state.connect_to_camera(new_camera_index):
                logging.info(f"Successfully switched to camera at {state.cameras[state.current_camera_index]['ip']}")
                state.update_leds()
            else:
                logging.error(f"Failed to switch to camera at index {new_camera_index}")
            Controller.inputCtrl.camera_changed = False

        # Preset Recall Handling
        if Controller.inputCtrl.updatePreset:
            try:
                preset_number = Controller.inputCtrl.presetNumber + 1
                y, x = (preset_number - 1) % 5, (preset_number - 1) // 5

                Controller.LED.update(x, y, [255, 255, 0])
                Controller.LED.add_fade_to_black_animation(x, y, duration=0.5)

                state.cam.recall_preset(preset_number)

                print(f"Recalled preset {preset_number}")
            except Exception as e:
                print(f"Error recalling preset: {e}")
            Controller.inputCtrl.updatePreset = False

        # Preset Save Handling
        if Controller.inputCtrl.setPreset:
            try:
                preset_number = Controller.inputCtrl.presetNumber
                state.cam.save_preset(preset_number + 1)
                print(f"Saved preset {preset_number + 1}")

                y, x = preset_number % 5, preset_number // 5
                Controller.LED.update(x, y, [255, 255, 0])
                Controller.LED.add_fade_to_color_animation(x, y, [0, 0, 255], duration=1.0)

                logging.debug(f"Updated LED at ({x},{y}) to yellow for saved preset, fading out.")
            except Exception as e:
                print(f"Error saving preset: {e}")
            Controller.inputCtrl.setPreset = False

        # Pan/tilt updates
        if Controller.inputCtrl.pan != state.currentPan or Controller.inputCtrl.tilt != state.currentTilt:
            state.update_pan_tilt(Controller.inputCtrl.pan, Controller.inputCtrl.tilt)

        # Zoom updates
        if Controller.inputCtrl.zoom != state.currentZoom:
            state.update_zoom(Controller.inputCtrl.zoom)

        # Fast mode toggle
        if Controller.inputCtrl.fast_mode != state.fast_mode_active:
            state.toggle_fast_mode(Controller.inputCtrl.fast_mode)
            update_fast_mode_led()

        # Home command
        if Controller.inputCtrl.home_bool != state.home_mode:
            state.home_mode = Controller.inputCtrl.home_bool
            if state.home_mode:
                state.home_camera()

        time.sleep(0.005)
except Exception as e:
    print(f"An error occurred in the main loop: {e}")
finally:
    print("Shutting down...")
    api_server.stop()
    Controller.close()
    print('Closed')
    os._exit(0)