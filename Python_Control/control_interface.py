from AutotrackerKeyboard import Controller
from ViscaOverIP.camera import Camera
import json

class SystemState:
    def __init__(self):
        self.controller = None
        self.current_camera_index = 0
        self.cameras = []
        self.cam = None
        self.load_config()

    def load_config(self):
        # Load camera configuration
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        self.cameras = config['cameras']

    def connect_to_camera(self, index):
        """Switch to a different camera"""
        if 0 <= index < len(self.cameras):
            try:
                if self.cam:
                    self.cam.close_connection()  # Close previous camera connection
                self.cam = Camera(self.cameras[index]['ip'])
                self.current_camera_index = index
                return True
            except Exception as e:
                print(f"Error connecting to camera {self.cameras[index]['ip']}: {e}")
        return False

    def pan_tilt(self, pan_speed, tilt_speed):
        """Control the pan and tilt of the current camera"""
        if self.cam:
            self.cam.pantilt(pan_speed, tilt_speed)

    def zoom(self, zoom_speed):
        """Control the zoom of the current camera"""
        if self.cam:
            self.cam.zoom(zoom_speed)

    def recall_preset(self, preset_number):
        """Recall a preset for the current camera"""
        if self.cam:
            self.cam.recall_preset(preset_number)

    def save_preset(self, preset_number):
        """Save the current camera state to a preset"""
        if self.cam:
            self.cam.save_preset(preset_number)

    def get_current_camera(self):
        """Get the current camera information"""
        if self.cam:
            return self.cameras[self.current_camera_index]

    def get_camera_list(self):
        """Get the list of all configured cameras"""
        return self.cameras

    def get_led_status(self):
        """Get the status of the LEDs"""
        return self.controller.LED.LED_STATE

    def update_led(self, x, y, rgb):
        """Update a specific LED's color"""
        self.controller.LED.update(x, y, rgb)
        self.controller.LED.show()  # Apply the change
