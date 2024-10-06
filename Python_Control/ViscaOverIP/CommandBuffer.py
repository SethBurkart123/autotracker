import time
from queue import Queue
from threading import Thread
import logging

class CommandBuffer:
    def __init__(self, camera, max_rate=10):  # max_rate is commands per second
        self.camera = camera
        self.buffer = Queue()
        self.max_rate = max_rate
        self.min_interval = 1.0 / max_rate
        self.last_send_time = 0
        self.thread = Thread(target=self._dispatch_loop, daemon=True)
        self.thread.start()

    def add_command(self, command_hex: str, query=False):
        self.buffer.put((command_hex, query))

    def _dispatch_loop(self):
        while True:
            if not self.buffer.empty():
                current_time = time.time()
                if current_time - self.last_send_time >= self.min_interval:
                    command_hex, query = self.buffer.get()
                    try:
                        self.camera._send_command(command_hex, query)
                    except Exception as e:
                        logging.error(f"Error dispatching command: {e}")
                    self.last_send_time = time.time()
                else:
                    time.sleep(self.min_interval - (current_time - self.last_send_time))
            else:
                time.sleep(0.01)  # Small sleep to prevent busy-waiting