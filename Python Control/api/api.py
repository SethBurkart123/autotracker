import json
import threading
import logging
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG)

class CameraModel(BaseModel):
    ip: str
    color: list

class API:
    def __init__(self, host='0.0.0.0', port=9000, controller=None, shared_state=None):
        self.host = host
        self.port = port
        self.controller = controller  # Controller object
        self.shared_state = shared_state  # SharedState object

        self.app = fastapi.FastAPI()
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )
        
        self.setup_routes()

        # Mount the frontend static files
        self.app.mount("/", StaticFiles(directory="./frontend/dist", html=True), name="frontend")

        self.server = None
        self.thread = None

    def setup_routes(self):
        @self.app.get("/api/config")
        async def get_config():
            return self.shared_state.config

        @self.app.post("/api/config")
        async def update_config(config: dict):
            self.shared_state.config = config
            self.shared_state.cameras = config['cameras']
            self.save_config()
            return {"message": "Configuration updated successfully"}

        @self.app.get("/api/cameras")
        async def get_cameras():
            return self.shared_state.cameras

        @self.app.get("/api/camera/{index}")
        async def get_camera(index: int):
            if 0 <= index < len(self.shared_state.cameras):
                return self.shared_state.cameras[index]
            raise fastapi.HTTPException(status_code=404, detail="Camera not found")

        @self.app.put("/api/camera/{index}")
        async def update_camera(index: int, camera: CameraModel):
            if 0 <= index < len(self.shared_state.cameras):
                self.shared_state.cameras[index] = camera.dict()
                self.shared_state.config['cameras'][index] = camera.dict()
                self.save_config()
                self.shared_state.update_leds()
                return {"message": f"Camera {index} updated successfully"}
            raise fastapi.HTTPException(status_code=404, detail="Camera not found")

        @self.app.post("/api/camera")
        async def add_camera(camera: CameraModel):
            if len(self.shared_state.cameras) >= 15:
                raise fastapi.HTTPException(status_code=400, detail="Maximum number of cameras (15) reached")
            self.shared_state.cameras.append(camera.dict())
            self.shared_state.config['cameras'] = self.shared_state.cameras
            self.save_config()
            self.shared_state.update_leds()
            return {"message": "Camera added successfully"}

        @self.app.delete("/api/camera/{index}")
        async def remove_camera(index: int):
            if 0 <= index < len(self.shared_state.cameras):
                removed_camera = self.shared_state.cameras.pop(index)
                self.shared_state.config['cameras'] = self.shared_state.cameras
                self.save_config()
                self.shared_state.update_leds()
                return {"message": f"Camera at index {index} removed successfully", "removed_camera": removed_camera}
            raise fastapi.HTTPException(status_code=404, detail="Camera not found")

    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.shared_state.config, f, indent=2)

    def start(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.server = uvicorn.Server(uvicorn.Config(self.app, host=self.host, port=self.port))
        self.server.run()

    def stop(self):
        if self.server:
            self.server.should_exit = True
            self.server.force_exit = True
            self.thread.join()