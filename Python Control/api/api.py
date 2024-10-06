import json
import threading
import logging
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.DEBUG)

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

        self.server = None
        self.thread = None

    def setup_routes(self):
        @self.app.get("/config")
        async def get_config():
            return self.shared_state.config

        @self.app.post("/config")
        async def update_config(config: dict):
            self.shared_state.config = config
            self.shared_state.cameras = config['cameras']
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            return {"message": "Configuration updated successfully"}

        @self.app.get("/camera/{index}")
        async def get_camera(index: int):
            if 0 <= index < len(self.shared_state.cameras):
                return self.shared_state.cameras[index]
            raise fastapi.HTTPException(status_code=404, detail="Camera not found")

        @self.app.put("/camera/{index}")
        async def update_camera(index: int, camera: dict):
            if 0 <= index < len(self.shared_state.cameras):
                self.shared_state.cameras[index] = camera
                self.shared_state.config['cameras'][index] = camera
                with open('config.json', 'w') as f:
                    json.dump(self.shared_state.config, f, indent=2)
                # Trigger LED update
                self.shared_state.update_leds()
                return {"message": f"Camera {index} updated successfully"}
            raise fastapi.HTTPException(status_code=404, detail="Camera not found")

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