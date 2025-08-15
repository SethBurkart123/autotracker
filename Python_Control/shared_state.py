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

        self.home_mode = False
        self.fast_mode_active = False

        # Auto tracking storage for all cameras
        self.auto_tracking_commands = {}  # {camera_index: {'pan_speed': float, 'tilt_speed': float}}

        self.controller = None  # Add this line
        self.led_manager = None  # Centralised LED state manager

    def connect_to_camera(self, index):
        """Connect to a camera based on index from the config."""
        if 0 <= index < len(self.cameras):
            try:
                if self.cam:
                    self.cam.close_connection()
                self.cam = Camera(self.cameras[index]['ip'])
                self.current_camera_index = index
                self.cam.slow_pan_tilt(True)
                # Disable zoom-triggered autofocus to prevent unwanted movement during zoom
                try:
                    self.cam.set_autofocus_mode('normal')
                except Exception as e:
                    print(f"Warning: Could not set autofocus mode: {e}")
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
        """Update pan and tilt state, combining joystick and auto tracking."""
        self.currentPan = pan
        self.currentTilt = tilt
        
        # Get auto tracking commands for current camera if active
        auto_pan = 0
        auto_tilt = 0
        if (self.controller and self.controller.inputCtrl.auto_tracking_active and 
            self.current_camera_index in self.auto_tracking_commands):
            auto_commands = self.auto_tracking_commands[self.current_camera_index]
            auto_pan = auto_commands.get('pan_speed', 0)
            auto_tilt = auto_commands.get('tilt_speed', 0)
        
        # Combine joystick and auto tracking (additive)
        combined_pan = pan + auto_pan
        combined_tilt = tilt + auto_tilt
        
        # Clamp to valid VISCA range [-24, 24]
        combined_pan = max(-24, min(24, combined_pan))
        combined_tilt = max(-24, min(24, combined_tilt))
        
        if self.cam:
            try:
                self.cam.pantilt(pan_speed=-combined_pan, tilt_speed=-combined_tilt)
            except Exception as e:
                print(f"Error updating pan/tilt: {e}")

    def update_auto_tracking_command(self, camera_index, pan_speed, tilt_speed):
        """Update auto tracking command for a specific camera."""
        self.auto_tracking_commands[camera_index] = {
            'pan_speed': pan_speed,
            'tilt_speed': tilt_speed
        }

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

    def set_controller(self, controller):
        self.controller = controller

    def set_led_manager(self, led_manager):
        """Attach a centralised LED state manager."""
        self.led_manager = led_manager

    def update_leds(self):
        """Delegate LED refresh to the central manager (if attached)."""
        if self.led_manager:
            self.led_manager.update()

    def update_fast_mode_led(self):
        if self.fast_mode_active:
            self.controller.LED.update(3, 4, [0, 0, 0])
        else:
            self.controller.LED.update(3, 4, [0, 255, 0])