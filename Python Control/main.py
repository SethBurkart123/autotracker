import time
import logging
import threading
from control_interface import SystemState
import uvicorn  # FastAPI server runner

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the system state
system_state = SystemState()

# Function to run the FastAPI server (for the API)
def run_api():
    uvicorn.run("api:app", host="0.0.0.0", port=8000)  # Removed reload=True

# Control loop to handle regular system operations (input control, LED updates, etc.)
def control_loop():
    camera_select_mode = False
    preset_setting_mode = False
    home_mode = False
    fast_mode_active = False

    while True:
        # Check for camera selection mode changes
        if system_state.controller.inputCtrl.camera_select_mode:
            if not camera_select_mode:
                logging.debug("Entering camera select mode")
                camera_select_mode = True
                preset_setting_mode = False
                system_state.controller.update_led_for_camera_select()

        elif system_state.controller.inputCtrl.preset_setting_mode:
            if not preset_setting_mode:
                logging.debug("Entering preset setting mode")
                preset_setting_mode = True
                camera_select_mode = False
                system_state.controller.update_led_for_preset_setting()

        else:
            if camera_select_mode or preset_setting_mode:
                logging.debug("Exiting special modes")
                camera_select_mode = False
                preset_setting_mode = False
                system_state.controller.update_led_for_normal_mode()

        # Check if the camera has changed via the input or API
        if system_state.controller.inputCtrl.camera_changed:
            new_camera_index = system_state.controller.inputCtrl.selected_camera
            logging.info(f"Attempting to switch to camera {new_camera_index}")
            if system_state.connect_to_camera(new_camera_index):
                logging.info(f"Successfully switched to camera {system_state.cameras[new_camera_index]['ip']}")
                system_state.controller.update_camera_function_button()
            else:
                logging.error(f"Failed to switch to camera at index {new_camera_index}")
            system_state.controller.inputCtrl.camera_changed = False

        # Handle preset recalling and saving
        if system_state.controller.inputCtrl.setPreset:
            try:
                preset_number = system_state.controller.inputCtrl.presetNumber
                system_state.save_preset(preset_number + 1)  # Add 1 because presets are 1-indexed
                logging.info(f"Saved preset {preset_number + 1}")
            except Exception as e:
                logging.error(f"Error saving preset: {e}")
            system_state.controller.inputCtrl.setPreset = False

        if system_state.controller.inputCtrl.updatePreset:
            try:
                preset_number = system_state.controller.inputCtrl.presetNumber + 1
                system_state.recall_preset(preset_number)
                logging.info(f"Recalled preset {preset_number}")
            except Exception as e:
                logging.error(f"Error recalling preset: {e}")
            system_state.controller.inputCtrl.updatePreset = False

        # Handle pan/tilt/zoom updates
        if system_state.controller.inputCtrl.pan != system_state.controller.inputCtrl.pan or \
           system_state.controller.inputCtrl.tilt != system_state.controller.inputCtrl.tilt:
            try:
                system_state.pan_tilt(-system_state.controller.inputCtrl.pan, -system_state.controller.inputCtrl.tilt)
            except Exception as e:
                logging.error(f"Error adjusting pan/tilt: {e}")

        if system_state.controller.inputCtrl.zoom != system_state.controller.inputCtrl.zoom:
            try:
                system_state.zoom(system_state.controller.inputCtrl.zoom)
            except Exception as e:
                logging.error(f"Error adjusting zoom: {e}")

        # Handle fast mode toggle
        if system_state.controller.inputCtrl.fast_mode != fast_mode_active:
            fast_mode_active = system_state.controller.inputCtrl.fast_mode
            try:
                system_state.cam.slow_pan_tilt(fast_mode_active)
                system_state.controller.update_fast_mode_led()
            except Exception as e:
                logging.error(f"Error setting fast pan/tilt mode: {e}")

        # Handle home position
        if system_state.controller.inputCtrl.home_bool != home_mode:
            home_mode = system_state.controller.inputCtrl.home_bool
            try:
                system_state.cam.reset_sequence_number()
                system_state.cam.home()
                home_mode = False
            except Exception as e:
                logging.error(f"Error homing: {e}")

        # Sleep briefly to prevent excessive CPU usage
        time.sleep(0.005)


if __name__ == "__main__":
    # Create threads for both the API and control loop
    api_thread = threading.Thread(target=run_api, daemon=True)
    control_thread = threading.Thread(target=control_loop, daemon=True)

    # Start both threads
    api_thread.start()
    control_thread.start()

    # Join the threads to keep the program running
    api_thread.join()
    control_thread.join()
