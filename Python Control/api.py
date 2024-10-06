from fastapi import FastAPI
from control_interface import SystemState

app = FastAPI()

# Initialize the system state
state = SystemState()

@app.get("/cameras")
def get_cameras():
    """Return the list of all available cameras"""
    return state.get_camera_list()

@app.get("/camera/current")
def get_current_camera():
    """Return the currently selected camera"""
    return state.get_current_camera()

@app.post("/camera/select/{camera_id}")
def select_camera(camera_id: int):
    """Switch to a specific camera"""
    success = state.connect_to_camera(camera_id)
    if success:
        return {"status": "success", "message": f"Camera {camera_id} selected"}
    else:
        return {"status": "error", "message": f"Unable to select camera {camera_id}"}

@app.post("/camera/pantilt")
def pan_tilt(pan_speed: int, tilt_speed: int):
    """Control the pan and tilt of the current camera"""
    state.pan_tilt(pan_speed, tilt_speed)
    return {"status": "success", "message": f"Pan {pan_speed}, Tilt {tilt_speed} applied"}

@app.post("/camera/zoom/{zoom_speed}")
def zoom_camera(zoom_speed: int):
    """Control the zoom of the current camera"""
    state.zoom(zoom_speed)
    return {"status": "success", "message": f"Zoom {zoom_speed} applied"}

@app.post("/camera/preset/recall/{preset_number}")
def recall_preset(preset_number: int):
    """Recall a preset"""
    state.recall_preset(preset_number)
    return {"status": "success", "message": f"Preset {preset_number} recalled"}

@app.post("/camera/preset/save/{preset_number}")
def save_preset(preset_number: int):
    """Save the current state to a preset"""
    state.save_preset(preset_number)
    return {"status": "success", "message": f"Preset {preset_number} saved"}

@app.get("/led/status")
def get_led_status():
    """Get the status of the LED grid"""
    return {"led_status": state.get_led_status()}

@app.post("/led/update")
def update_led(x: int, y: int, r: int, g: int, b: int):
    """Update the color of a specific LED"""
    state.update_led(x, y, [r, g, b])
    return {"status": "success", "message": f"LED at {x},{y} updated to color {r},{g},{b}"}
