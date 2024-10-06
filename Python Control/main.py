import time
import AutotrackerKeyboard
from shared_state import SharedState
import logging
import subprocess
from api.api import API  # Import the API class

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize shared state
state = SharedState()

# Create the controller (with serial connection)
usb_devices = subprocess.check_output(['ls', '/dev/ttyUSB*'], stderr=subprocess.STDOUT).decode().strip().split('\n')
Controller = AutotrackerKeyboard.Controller(usb_devices[0])
state.set_controller(Controller)  # Add this line

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

        # **Preset Recall Handling**
        if Controller.inputCtrl.updatePreset:
            try:
                preset_number = Controller.inputCtrl.presetNumber + 1
                y, x = (preset_number - 1) % 5, (preset_number - 1) // 5

                Controller.LED.update(x, y, [255, 255, 0])
                Controller.LED.add_fade_to_black_animation(x, y, duration=0.5)

                logging.debug(f"Attempting to recall preset {preset_number}")
                state.cam.recall_preset(preset_number)

                print(f"Recalled preset {preset_number}")
            except Exception as e:
                print(f"Error recalling preset: {e}")
            Controller.inputCtrl.updatePreset = False

        # **Preset Save Handling (Add this block)**
        if Controller.inputCtrl.setPreset:
            try:
                preset_number = Controller.inputCtrl.presetNumber
                logging.debug(f"Attempting to save preset {preset_number + 1}")
                state.cam.save_preset(preset_number + 1)  # Save the preset in the camera
                print(f"Saved preset {preset_number + 1}")

                # Calculate LED x and y based on the preset number
                y, x = preset_number % 5, preset_number // 5

                # Light up the selected preset button in yellow
                Controller.LED.update(x, y, [255, 255, 0])  # Yellow for preset selection
                
                # Trigger the fade-to-black animation
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
except KeyboardInterrupt:
    print("Shutting down...")
    api_server.stop()
    Controller.close()
    print('Closed')