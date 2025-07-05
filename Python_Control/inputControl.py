import json
import time

class inputController:
    def __init__(self, ser):
        self.ser = ser
        self.pan = 0
        self.tilt = 0
        self.zoom = 0
        self.buttonState = [
            [False, False, False, False, False],
            [False, False, False, False, False],
            [False, False, False, False, False],
            [False, False, False, False, False]
        ]
        self.buttonMap = [
            [0, 1, 2, 3, 4],
            [5, 6, 7, 8, 9],
            [10, 11, 12, 13, 14],
            [15, 16, 17, 18, 19]
        ]
        self.presetNumber = 0
        self.updatePreset = False
        self.setPreset = False

        self.camera_select_mode = True  # Default to camera select mode
        self.preset_setting_mode = False
        self.selected_camera = 0
        self.camera_changed = False
        self.home_bool = False

        # Load camera configuration
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        self.cameras = config['cameras']

        self.vertical_lock_active = False
        self.vertical_lock_changed = False # Flag to indicate state change for LED update

        # Long‑press (home button) handling
        self.home_pressed_time = None     # Start‑time of current press
        self.restart_requested = False    # Flag set after ≥5 s hold
        self.home_short_release = False   # Flag set on short press release

    def updateButton(self, x, y, value):
        self.buttonState[x][y] = value
    
    def apply_deadzone(self, value, deadzone=1):
        """Apply deadzone to eliminate minor drift. Values within ±deadzone become 0,
        values outside just have the deadzone subtracted."""
        if abs(value) <= deadzone:
            return 0
        
        # Simply subtract the deadzone from the absolute value
        if value > 0:
            return value - deadzone
        else:
            return value + deadzone

    def updateTilt(self, value):
        if self.vertical_lock_active:
            # If vertical lock is active, force tilt to 0 (neutral)
            if self.tilt != 0:
                self.tilt = 0
        else:
            processed_value = self.apply_deadzone(value)
            if self.tilt != processed_value:
                self.tilt = processed_value
    
    def updatePan(self, value):
        processed_value = self.apply_deadzone(value)
        if self.pan != processed_value:
            self.pan = processed_value

    def updateZoom(self, value):
        if self.zoom != value:
            self.zoom = value

    def processPacket(self, case, LED):
        if case[0] == b'0':
            self.updateTilt(int(case[1]))
        elif case[0] == b'1':
            self.updatePan(int(case[1]))
        elif case[0] == b'2':
            self.updateZoom(int(case[1]))
        elif case[0] == b'10' and case[1] == b'5':
            pressed = bool(int(case[2]))

            # Track duration of the press
            if pressed:
                if self.home_pressed_time is None:
                    self.home_pressed_time = time.time()
            else:
                if self.home_pressed_time is not None:
                    duration = time.time() - self.home_pressed_time
                    if duration >= 5.0:
                        self.restart_requested = True
                    else:
                        # Short press release: request a home action
                        self.home_short_release = True
                    self.home_pressed_time = None  # Reset timer

            # No immediate homing on press; handled on release
        else:  # update button
            if len(case) == 3:
                xloc = int(case[1])-2
                yloc = 4-(int(case[0])-6)
                value = bool(int(case[2]))
                self.updateButton(xloc, yloc, value)
                
                if xloc == 3 and yloc == 3:  # Preset mode modifier button (swap from camera)
                    self.preset_setting_mode = value
                    self.camera_select_mode = not value  # When preset mode is active, disable camera select mode
                elif xloc == 3 and yloc == 2:  # Maintain camera selection button functionality for compatibility
                    # This button now acts as a toggle between modes
                    if value:  # Only on press down
                        self.camera_select_mode = not self.camera_select_mode
                        self.preset_setting_mode = not self.camera_select_mode
                elif xloc == 3 and yloc == 4:  # Vertical lock toggle button
                    if value: # Toggle only on press down
                        self.vertical_lock_active = not self.vertical_lock_active
                        self.vertical_lock_changed = True # Signal that LED needs update
                        # Force tilt update in case lock was just engaged
                        if self.vertical_lock_active:
                            self.updateTilt(self.tilt) # This will force tilt to 0
                elif self.preset_setting_mode:
                    self.process_preset_setting(xloc, yloc, value)
                elif xloc <= 2:  # first 15 buttons (now used for camera selection by default)
                    self.process_camera_select(xloc, yloc, value)

    def process_camera_select(self, x, y, value):
        if x <= 2 and y <= 4:  # First 15 buttons
            camera_index = x * 5 + y
            if value and camera_index < len(self.cameras):  # Button pressed and camera exists
                self.selected_camera = camera_index
                self.camera_changed = True
                return True  # Indicate that a camera was selected
        return False  # No camera was selected

    def process_preset_setting(self, x, y, value):
        if x <= 2 and y <= 4:  # First 15 buttons
            preset_index = x * 5 + y
            if value:  # Button pressed
                self.setPreset = True
                self.presetNumber = preset_index
                return True  # Indicate that a preset was set
        return False  # No preset was set