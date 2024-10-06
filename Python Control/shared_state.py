# shared_state.py

import json
from ViscaOverIP.camera import Camera

class SharedState:
    def __init__(self, config_file='config.json'):
        # Load camera configuration
        with open(config_file, 'r') as config_file:
            self.config = json.load(config_file)
        
        # Shared state variables
        self.cameras = self.config['cameras']
        self.current_camera_index = 0
        self.cam = None

        self.currentPan = 0
        self.currentTilt = 0
        self.currentZoom = 0

        self.camera_select_mode = False
        self.preset_setting_mode = False

        self.home_mode = False
        self.fast_mode_active = False

    def connect_to_camera(self, index):
        """Connect to a camera based on index from the config."""
        if 0 <= index < len(self.cameras):
            try:
                if self.cam:
                    self.cam.close_connection()
                self.cam = Camera(self.cameras[index]['ip'])
                self.current_camera_index = index
                return True
            except Exception as e:
                print(f"Error connecting to camera at {self.cameras[index]['ip']}: {e}")
        return False

    def reset_camera(self):
        """Resets the camera connection and initializes state."""
        self.cam = None
        self.currentPan = 0
        self.currentTilt = 0
        self.currentZoom = 0
        self.fast_mode_active = False
        self.home_mode = False

    def update_pan_tilt(self, pan, tilt):
        """Update pan and tilt state."""
        self.currentPan = pan
        self.currentTilt = tilt
        if self.cam:
            self.cam.pantilt(pan_speed=-pan, tilt_speed=-tilt)

    def update_zoom(self, zoom):
        """Update zoom state."""
        self.currentZoom = zoom
        if self.cam:
            self.cam.zoom(speed=zoom)

    def home_camera(self):
        """Send the camera to home position."""
        if self.cam:
            self.cam.reset_sequence_number()
            self.cam.home()

    def toggle_fast_mode(self, mode):
        """Enable or disable fast pan/tilt mode."""
        self.fast_mode_active = mode
        if self.cam:
            self.cam.slow_pan_tilt(mode)

