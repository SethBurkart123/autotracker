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
        self.updateLed = False
        self.presetNumber = 0
        self.updatePreset = False
        self.setPreset = False
    
    def updateButton(self, x, y, value):
        self.buttonState[x][y] = value
    
    def updateTilt(self, value):
        if self.tilt != value:
            self.tilt = value
    
    def updatePan(self, value):
        if self.pan != value:
            self.pan = value

    def updateZoom(self, value):
        if (self.zoom != value):
            self.zoom = value

    def processPacket(self, case, LED):
        if case[0] == b'0':
            self.updateTilt(int(case[1]))
        elif case[0] == b'1':
            self.updatePan(int(case[1]))
        elif case[0] == b'2':
            #print("UpdateZoom 1")
            self.updateZoom(int(case[1]))
        else: #update button
            if len(case) == 3:
                xloc = int(case[1])-2
                yloc = 4-(int(case[0])-6)
                value = bool(int(case[2]))
                self.updateButton(xloc, yloc, value)
                
                print(xloc, yloc)
                if xloc <= 2: #first 15 buttons (preset buttons)
                    if value: # if button has been pressed down
                        if self.buttonState[3][2]: # Preset Set Button Down
                            self.setPreset = True
                        else:
                            self.updatePreset = True
                        self.presetNumber = self.buttonMap[xloc][yloc]

                if value: # button is pressed down
                    # Turn on led
                    LED.update(xloc, yloc, [255, 0, 255])
                    self.updateLed = True
                else: # button is up
                    # Turn off led
                    LED.update(xloc, yloc, [0, 0, 0])
                    self.updateLed = True