import json
import logging

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

        self.camera_select_mode = False
        self.preset_setting_mode = False  # New attribute for preset setting mode
        self.selected_camera = 0
        self.camera_changed = False
        self.home_bool = False

        # Load camera configuration
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
        self.cameras = config['cameras']

        self.fast_mode = False

    def updateButton(self, x, y, value):
        self.buttonState[x][y] = value
    
    def updateTilt(self, value):
        if self.tilt != value:
            self.tilt = value
    
    def updatePan(self, value):
        if self.pan != value:
            self.pan = value

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
            self.home_bool = bool(int(case[2]))
        else:  # update button
            if len(case) == 3:
                xloc = int(case[1])-2
                yloc = 4-(int(case[0])-6)
                value = bool(int(case[2]))
                self.updateButton(xloc, yloc, value)
                
                if xloc == 3 and yloc == 2:  # Camera select modifier button
                    self.camera_select_mode = value
                    self.preset_setting_mode = False
                elif xloc == 3 and yloc == 3:  # Preset setting modifier button
                    self.preset_setting_mode = value
                    self.camera_select_mode = False
                elif xloc == 3 and yloc == 4:  # Slow mode modifier button
                    self.fast_mode = not value
                elif self.camera_select_mode:
                    self.process_camera_select(xloc, yloc, value)
                elif self.preset_setting_mode:
                    self.process_preset_setting(xloc, yloc, value)
                elif xloc <= 2:  # first 15 buttons (preset buttons)
                    if value:  # if button has been pressed down
                        self.updatePreset = True
                        self.presetNumber = self.buttonMap[xloc][yloc]

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

