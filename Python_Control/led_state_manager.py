import logging
from typing import List


class LedStateManager:
    """
    Centralised manager that converts high‑level application state into the
    low‑level RGB array consumed by `LedController`.  Call `update()` whenever
    SharedState or InputController flags change.
    """

    def __init__(self, led_controller, shared_state, input_controller):
        self.led = led_controller
        self.state = shared_state
        self.input = input_controller

    # Public API -------------------------------------------------------------

    def update(self) -> None:
        """Recompute every LED based on the latest application state."""
        self._render_camera_select()

        # Always‑present indicators
        self._render_vertical_lock()

    # Internal helpers -------------------------------------------------------

    def _render_camera_select(self) -> None:
        """Palette of cameras with the current one highlighted."""
        self.led.clear_all()
        for idx, cam in enumerate(self.state.cameras):
            y, x = idx % 5, idx // 5
            colour: List[int] = cam["color"]
            if idx == self.state.current_camera_index:
                self.led.update(x, y, colour)
            else:
                self.led.update(x, y, [int(c * 0.3) for c in colour])

    # Preset setting rendering removed

    def _render_vertical_lock(self) -> None:
        colour = [255, 0, 0] if self.input.vertical_lock_active else [0, 255, 0]
        self.led.update(3, 4, colour)

    def _render_camera_function_button(self) -> None:
        cam_colour = self.state.cameras[self.state.current_camera_index]["color"]
        dimmed = [int(c * 0.7) for c in cam_colour]
        self.led.update(3, 2, dimmed)