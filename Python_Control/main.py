import glob
import os
import time
import AutotrackerKeyboard
from shared_state import SharedState
import logging
from api.api import API  # Import the API class
import sys
from led_state_manager import LedStateManager

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize shared state
state = SharedState()

def find_usb_device():
    print("1")
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

# Initialise central LED manager
led_manager = LedStateManager(Controller.LED, state, Controller.inputCtrl)
state.set_led_manager(led_manager)
led_manager.update()

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
    # Show the camera button with a different color (more subtle) as it's now a toggle
    dimmed_color = [int(c * 0.7) for c in current_camera_color]
    Controller.LED.update(3, 2, dimmed_color)
    
    # Update the preset mode button to show its new role
    if Controller.inputCtrl.preset_setting_mode:
        Controller.LED.update(3, 3, [255, 0, 0])  # Bright red when active
    else:
        Controller.LED.update(3, 3, [100, 0, 0])  # Dim red when inactive

# Initial LED render via the central manager
led_manager.update()

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
    logging.debug("Updating LEDs for normal mode (camera selection)")
    # Now normal mode shows camera selection options
    update_led_for_camera_select()
    update_vertical_lock_led() # Renamed function

# Renamed and modified function
def update_vertical_lock_led():
    if Controller.inputCtrl.vertical_lock_active:
        Controller.LED.update(3, 4, [255, 0, 0])  # Red when vertical lock is ON
    else:
        Controller.LED.update(3, 4, [0, 255, 0])  # Green when vertical lock is OFF

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

        # Update the state based on controller input
        if Controller.inputCtrl.camera_select_mode != state.camera_select_mode:
            state.camera_select_mode = Controller.inputCtrl.camera_select_mode
            logging.debug(f"Camera select mode: {state.camera_select_mode}")
            state.update_leds()
            
        if Controller.inputCtrl.preset_setting_mode != state.preset_setting_mode:
            state.preset_setting_mode = Controller.inputCtrl.preset_setting_mode
            logging.debug(f"Preset setting mode: {state.preset_setting_mode}")
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

        # Vertical Lock LED update
        if Controller.inputCtrl.vertical_lock_changed:
            state.update_leds()
            Controller.inputCtrl.vertical_lock_changed = False

        # Home camera on short press release (long press restart handled elsewhere)
        if Controller.inputCtrl.home_short_release:
            state.home_camera()
            Controller.inputCtrl.home_short_release = False

        # Restart the script when a ≥5 s long‑press on the home button is detected
        if Controller.inputCtrl.restart_requested:
            logging.info("Long press detected (>5 s). Restarting script…")

            # Best‑effort cleanup
            try:
                api_server.stop()
            except Exception:
                pass
            try:
                Controller.close()
            except Exception:
                pass

            # Re‑exec the current Python program
            os.execv(sys.executable, ['python'] + sys.argv)

        time.sleep(0.005)
except Exception as e:
    print(f"An error occurred in the main loop: {e}")
finally:
    print("Shutting down...")
    api_server.stop()
    Controller.close()
    print('Closed')
    os._exit(0)