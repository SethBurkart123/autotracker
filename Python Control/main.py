import time
import AutotrackerKeyboard
from ViscaOverIP import Camera

cam = Camera('192.168.0.75')  # Your camera's IP address or hostname here

Controller = AutotrackerKeyboard.Controller('/dev/cu.usbserial-110')

#cam.info_display(False)

currentPan = 0
currentTilt = 0
currentZoom = 0

while True:
    if (Controller.inputCtrl.updatePreset):
        try:
            cam.info_display(False)
        except:
            pass
        try:
            cam.recall_preset(Controller.inputCtrl.presetNumber)
        except:
            pass
        try:
            cam.info_display(False)
        except:
            pass
        Controller.inputCtrl.updatePreset = False
    
    if (Controller.inputCtrl.setPreset):
        print("save preset")
        try:
            cam.save_preset(Controller.inputCtrl.presetNumber)
        except:
            pass
        Controller.inputCtrl.setPreset = False
    
    if Controller.inputCtrl.pan != currentPan or Controller.inputCtrl.tilt != currentTilt:
        #Controller.inputCtrl.updatePanTilt = False
        try:
            currentPan = Controller.inputCtrl.pan
            currentTilt = Controller.inputCtrl.tilt
            cam.pantilt(pan_speed=Controller.inputCtrl.pan, tilt_speed=Controller.inputCtrl.tilt)
        except:
            pass
        
    
    if Controller.inputCtrl.zoom != currentZoom:
        #Controller.inputCtrl.updateZoom = False
        try:
            currentZoom = Controller.inputCtrl.zoom
            cam.zoom(speed=Controller.inputCtrl.zoom)
        except:
            pass
        
    
    time.sleep(0.005)