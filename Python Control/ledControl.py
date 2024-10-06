import time
import threading
import logging

class LedController:
    def __init__(self, ser):
        self.ser = ser
        self.LED_LUT = [
            [4, 3, 2, 1, 0],
            [9, 8, 7, 6, 5],
            [14, 13, 12, 11, 10],
            [None, None, 17, 16, 15]
        ]
        self.LED_STATE = [
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]],
            [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]]
        ]
        self.LED_TEMP = [[0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0], [0,0,0]]

        # Thread control for animations
        self.animations = []
        self.animation_lock = threading.Lock()  # Lock for thread-safe operations
        self.led_state_lock = threading.Lock()  # Lock for LED_STATE
        self.animation_thread = threading.Thread(target=self.run_animations)
        self.animation_thread.start()

        self.max_retries = 3
        self.retry_delay = 0.1

    def show(self):
        retries = 0
        while retries < self.max_retries:
            try:
                with self.led_state_lock:
                    temp_list = []
                    for y in range(4):
                        for x in range(5):
                            if self.LED_LUT[y][x] is not None:
                                temp_list.extend(self.LED_STATE[y][x])
                
                binary_data = bytes(temp_list)
                logging.debug(f"Sending LED data: {binary_data.hex()}")
                
                self.ser.write(binary_data)
                self.ser.flush()  # Ensure all data is sent
                
                logging.debug("LED data sent successfully")
                return
            except IOError as e:
                logging.warning(f"I/O error while updating LEDs (attempt {retries + 1}): {e}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    logging.error(f"Failed to update LEDs after {self.max_retries} attempts")

    def clear_presets(self):
        with self.led_state_lock:
            for x in range(3):
                for y in range(5):
                    self.LED_STATE[x][y] = [0, 0, 0]

    def clear_all(self):
        with self.led_state_lock:
            for x in range(4):
                for y in range(5):
                    self.LED_STATE[x][y] = [0, 0, 0]
    
    def update(self, x, y, rgb):
        with self.led_state_lock:
            self.LED_STATE[x][y] = rgb
        self.show()  # Attempt to update LEDs immediately

    def fade_to_black(self, x, y, duration=1.0):
        """Fade the LED at (x, y) to black over `duration` seconds."""
        start_rgb = self.LED_STATE[x][y]
        start_time = time.time()
        end_time = start_time + duration

        def animation_step():
            now = time.time()
            progress = min(1.0, (now - start_time) / duration)
            new_rgb = [
                int(start_rgb[0] * (1 - progress)),
                int(start_rgb[1] * (1 - progress)),
                int(start_rgb[2] * (1 - progress))
            ]
            self.update(x, y, new_rgb)
            return now >= end_time  # Return True when animation is complete

        return animation_step

    def fade_to_color(self, x, y, color, duration=1.0):
        """Fade the LED at (x, y) to the specified color over `duration` seconds."""
        start_rgb = self.LED_STATE[x][y]
        start_time = time.time()
        end_time = start_time + duration

        def animation_step():
            now = time.time()
            progress = min(1.0, (now - start_time) / duration)
            new_rgb = [
                int(start_rgb[0] * (1 - progress) + color[0] * progress),
                int(start_rgb[1] * (1 - progress) + color[1] * progress),
                int(start_rgb[2] * (1 - progress) + color[2] * progress)
            ]
            self.update(x, y, new_rgb)
            return now >= end_time  # Return True when animation is complete

        return animation_step
    
    def run_animations(self):
        """Continuously run animations in a separate thread."""
        while True:
            with self.animation_lock:
                completed_animations = []
                for animation in self.animations:
                    if animation():  # If animation is complete
                        completed_animations.append(animation)
                # Remove completed animations
                for animation in completed_animations:
                    self.animations.remove(animation)
            time.sleep(0.01)  # Control loop speed

    def add_fade_to_black_animation(self, x, y, duration=1.0):
        """Add a fade-to-black animation for the LED at (x, y)."""
        with self.animation_lock:
            self.animations.append(self.fade_to_black(x, y, duration))

    def add_fade_to_color_animation(self, x, y, color, duration=1.0):
        """Add a fade-to-color animation for the LED at (x, y)."""
        with self.animation_lock:
            self.animations.append(self.fade_to_color(x, y, color, duration))
