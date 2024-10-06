import time
import AutotrackerKeyboard
from ViscaOverIP import Camera
import logging
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# List of camera IP addresses and colors
cameras = config['cameras']
current_camera_index = 0
cam = None

Controller = AutotrackerKeyboard.Controller('/dev/cu.usbserial-2130')

currentPan = 0
currentTilt = 0
currentZoom = 0

camera_select_mode = False
preset_setting_mode = False  # New variable for preset setting mode

fast_mode_active = False

def connect_to_camera(index):
    global cam
    if 0 <= index < len(cameras):
        try:
            if cam:
                cam.close_connection()
            cam = Camera(cameras[index]['ip'])
            return True
        except Exception as e:
            print(f"Error connecting to camera at {cameras[index]['ip']}: {e}")
    return False

# Try to connect to the first available camera
for i in range(len(cameras)):
    if connect_to_camera(i):
        current_camera_index = i
        break

if cam is None:
    print("No cameras available. Please check your camera IP addresses.")

# Initialize the camera function button color
def update_camera_function_button():
    current_camera_color = cameras[current_camera_index]['color']
    Controller.LED.update(3, 2, current_camera_color)

# Call this function to set the initial state
update_camera_function_button()

def update_led_for_camera_select():
    logging.debug("Updating LEDs for camera select mode")
    Controller.LED.clear_all()
    for i, camera in enumerate(cameras):
        y, x = i % 5, i // 5
        color = camera['color']
        if i == current_camera_index:
            # Keep the selected camera at full brightness
            Controller.LED.update(x, y, color)
        else:
            # Make non-selected cameras much darker (e.g., 30% of original brightness)
            dark_color = [int(c * 0.3) for c in color]
            Controller.LED.update(x, y, dark_color)
    update_camera_function_button()

def update_led_for_normal_mode():
    logging.debug("Updating LEDs for normal mode")
    Controller.LED.clear_all()
    update_camera_function_button()
    update_fast_mode_led()  # Add this line

def update_fast_mode_led():
    if fast_mode_active:
        Controller.LED.update(3, 4, [0, 0, 0])
    else:
        Controller.LED.update(3, 4, [0, 255, 0])

def update_led_for_preset_setting():
    logging.debug("Updating LEDs for preset setting mode")
    Controller.LED.clear_all()
    for i in range(10):  # Assuming 10 preset buttons
        y, x = i % 5, i // 5
        Controller.LED.update(x, y, [0, 0, 255])  # Blue color for preset buttons
    Controller.LED.update(3, 3, [255, 0, 0])  # Red color for preset setting button
    update_camera_function_button()

def update_camera_function_button():
    # Always update the camera function button with the current camera's color
    current_camera_color = cameras[current_camera_index]['color']
    Controller.LED.update(3, 2, current_camera_color)

while True:
    if cam is None:
        time.sleep(1)
        continue

    if Controller.inputCtrl.camera_select_mode:
        if not camera_select_mode:
            logging.debug("Entering camera select mode")
            camera_select_mode = True
            preset_setting_mode = False
            update_led_for_camera_select()
    elif Controller.inputCtrl.preset_setting_mode:  # New condition for preset setting mode
        if not preset_setting_mode:
            logging.debug("Entering preset setting mode")
            preset_setting_mode = True
            camera_select_mode = False
            update_led_for_preset_setting()
    else:
        if camera_select_mode or preset_setting_mode:
            logging.debug("Exiting special modes")
            camera_select_mode = False
            preset_setting_mode = False
            update_led_for_normal_mode()

    if Controller.inputCtrl.camera_changed:
        new_camera_index = Controller.inputCtrl.selected_camera
        if connect_to_camera(new_camera_index):
            current_camera_index = new_camera_index
            logging.debug(f"Switched to camera at {cameras[current_camera_index]['ip']}")
            update_camera_function_button()
        else:
            logging.debug(f"Failed to switch to camera at index {new_camera_index}")
        Controller.inputCtrl.camera_changed = False

    if camera_select_mode:
        continue

    if preset_setting_mode:
        if Controller.inputCtrl.setPreset:
            try:
                preset_number = Controller.inputCtrl.presetNumber
                cam.save_preset(preset_number + 1)  # Add 1 because camera presets are 1-indexed
                print(f"Saved preset {preset_number + 1}")
                y, x = preset_number % 5, preset_number // 5  # Calculate x and y correctly
                Controller.LED.update(x, y, [255, 255, 0])  # Yellow color for set preset
            except Exception as e:
                print(f"Error saving preset: {e}")
            Controller.inputCtrl.setPreset = False
        continue

    if Controller.inputCtrl.updatePreset:
        try:
            preset_number = Controller.inputCtrl.presetNumber + 1
            cam.recall_preset(preset_number)
            print(f"Recalled preset {preset_number}")
        except Exception as e:
            print(f"Error recalling preset: {e}")
        Controller.inputCtrl.updatePreset = False
    
    if Controller.inputCtrl.pan != currentPan or Controller.inputCtrl.tilt != currentTilt:
        try:
            currentPan = -Controller.inputCtrl.pan
            currentTilt = -Controller.inputCtrl.tilt

            cam.pantilt(pan_speed=currentPan, tilt_speed=currentTilt)
        except Exception as e:
            print(f"Error adjusting pan/tilt: {e}")
    
    if Controller.inputCtrl.zoom != currentZoom:
        try:
            currentZoom = Controller.inputCtrl.zoom
            cam.zoom(speed=Controller.inputCtrl.zoom)
        except Exception as e:
            print(f"Error adjusting zoom: {e}")
    
    if Controller.inputCtrl.fast_mode != fast_mode_active:
        fast_mode_active = Controller.inputCtrl.fast_mode
        try:
            cam.slow_pan_tilt(fast_mode_active)
            update_fast_mode_led()
        except Exception as e:
            logging.error(f"Error setting fast pan/tilt mode: {e}")

    time.sleep(0.005)