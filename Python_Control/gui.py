import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QLabel, QLineEdit, QGroupBox, QGridLayout,
    QSpinBox, QTabWidget, QMessageBox, QColorDialog, QCheckBox, QInputDialog,
    QSlider, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from ViscaOverIP.camera import Camera  # Ensure this path matches your project structure

CONFIG_FILE = 'config.json'

class CameraController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera Control Application")
        self.cameras = []
        self.current_camera = None
        self.camera_objects = {}
        self.load_config()
        self.init_ui()

    def load_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.cameras = data.get('cameras', [])
        except FileNotFoundError:
            self.cameras = []

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'cameras': self.cameras}, f, indent=2)

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # Camera selection layout
        camera_select_layout = QHBoxLayout()
        self.camera_dropdown = QComboBox()
        self.update_camera_dropdown()
        self.camera_dropdown.currentIndexChanged.connect(self.select_camera)

        add_camera_btn = QPushButton("Add Camera")
        add_camera_btn.clicked.connect(self.add_camera)

        delete_camera_btn = QPushButton("Delete Camera")
        delete_camera_btn.clicked.connect(self.delete_camera)

        camera_select_layout.addWidget(QLabel("Select Camera:"))
        camera_select_layout.addWidget(self.camera_dropdown)
        camera_select_layout.addWidget(add_camera_btn)
        camera_select_layout.addWidget(delete_camera_btn)

        main_layout.addLayout(camera_select_layout)

        # Tabs for different control sections
        self.tabs = QTabWidget()
        self.tabs.addTab(self.power_display_tab(), "Power & Display")
        self.tabs.addTab(self.pan_tilt_tab(), "Pan/Tilt")
        self.tabs.addTab(self.zoom_tab(), "Zoom")
        self.tabs.addTab(self.focus_tab(), "Focus")
        self.tabs.addTab(self.white_balance_tab(), "White Balance")
        self.tabs.addTab(self.exposure_tab(), "Exposure")
        self.tabs.addTab(self.image_flip_tab(), "Image Flip")
        self.tabs.addTab(self.defog_tab(), "Defog")
        self.tabs.addTab(self.presets_tab(), "Presets")

        main_layout.addWidget(self.tabs)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def update_camera_dropdown(self):
        self.camera_dropdown.clear()
        for cam in self.cameras:
            self.camera_dropdown.addItem(cam['ip'])
        if self.cameras:
            self.camera_dropdown.setCurrentIndex(0)
            self.select_camera(0)

    def select_camera(self, index):
        if index < 0 or index >= len(self.cameras):
            self.current_camera = None
            return
        cam_info = self.cameras[index]
        ip = cam_info['ip']
        if ip not in self.camera_objects:
            try:
                self.camera_objects[ip] = Camera(ip)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to connect to camera {ip}: {e}")
                return
        self.current_camera = self.camera_objects[ip]

    def add_camera(self):
        ip, ok = QInputDialog.getText(self, 'Add Camera', 'Enter Camera IP:')
        if ok and ip:
            color = QColorDialog.getColor()
            if color.isValid():
                color_rgb = [color.red(), color.green(), color.blue()]
                self.cameras.append({'ip': ip, 'color': color_rgb})
                self.save_config()
                self.update_camera_dropdown()

    def delete_camera(self):
        index = self.camera_dropdown.currentIndex()
        if index >= 0:
            ip = self.cameras[index]['ip']
            reply = QMessageBox.question(self, 'Delete Camera',
                                         f"Are you sure you want to delete camera {ip}?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.cameras.pop(index)
                if ip in self.camera_objects:
                    del self.camera_objects[ip]
                self.save_config()
                self.update_camera_dropdown()

    # Power and Display Tab
    def power_display_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        power_group = QGroupBox("Power Control")
        power_layout = QHBoxLayout()
        power_on_btn = QPushButton("Power On")
        power_on_btn.clicked.connect(self.power_on)
        power_off_btn = QPushButton("Power Off")
        power_off_btn.clicked.connect(self.power_off)
        power_layout.addWidget(power_on_btn)
        power_layout.addWidget(power_off_btn)
        power_group.setLayout(power_layout)

        display_group = QGroupBox("Display Control")
        display_layout = QHBoxLayout()
        display_on_btn = QPushButton("Display On")
        display_on_btn.clicked.connect(self.display_on)
        display_off_btn = QPushButton("Display Off")
        display_off_btn.clicked.connect(self.display_off)
        display_layout.addWidget(display_on_btn)
        display_layout.addWidget(display_off_btn)
        display_group.setLayout(display_layout)

        layout.addWidget(power_group)
        layout.addWidget(display_group)
        tab.setLayout(layout)
        return tab

    def power_on(self):
        if self.current_camera:
            try:
                self.current_camera.set_power(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to power on: {e}")

    def power_off(self):
        if self.current_camera:
            try:
                self.current_camera.set_power(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to power off: {e}")

    def display_on(self):
        if self.current_camera:
            try:
                self.current_camera.info_display(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to turn on display: {e}")

    def display_off(self):
        if self.current_camera:
            try:
                self.current_camera.info_display(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to turn off display: {e}")

    # Pan/Tilt Tab
    def pan_tilt_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        pan_tilt_group = QGroupBox("Pan/Tilt Control")
        pan_tilt_layout = QGridLayout()

        # Pan control
        pan_label = QLabel("Pan:")
        self.pan_slider = QSlider(Qt.Horizontal)
        self.pan_slider.setRange(-24, 24)
        self.pan_slider.valueChanged.connect(self.pan_tilt_changed)
        self.pan_value_label = QLabel("0")

        # Tilt control
        tilt_label = QLabel("Tilt:")
        self.tilt_slider = QSlider(Qt.Vertical)
        self.tilt_slider.setRange(-24, 24)
        self.tilt_slider.valueChanged.connect(self.pan_tilt_changed)
        self.tilt_value_label = QLabel("0")

        home_btn = QPushButton("Go Home")
        home_btn.clicked.connect(self.go_home)

        reset_btn = QPushButton("Reset Pan/Tilt")
        reset_btn.clicked.connect(self.reset_pan_tilt)

        pan_tilt_layout.addWidget(pan_label, 0, 0)
        pan_tilt_layout.addWidget(self.pan_slider, 0, 1)
        pan_tilt_layout.addWidget(self.pan_value_label, 0, 2)
        pan_tilt_layout.addWidget(tilt_label, 1, 0)
        pan_tilt_layout.addWidget(self.tilt_slider, 1, 1)
        pan_tilt_layout.addWidget(self.tilt_value_label, 2, 1)
        pan_tilt_layout.addWidget(home_btn, 3, 0)
        pan_tilt_layout.addWidget(reset_btn, 3, 1)
        pan_tilt_group.setLayout(pan_tilt_layout)

        layout.addWidget(pan_tilt_group)
        tab.setLayout(layout)
        return tab

    def pan_tilt_changed(self):
        pan_speed = self.pan_slider.value()
        tilt_speed = self.tilt_slider.value()
        self.pan_value_label.setText(str(pan_speed))
        self.tilt_value_label.setText(str(tilt_speed))
        if self.current_camera:
            try:
                self.current_camera.pantilt(pan_speed, tilt_speed)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to move pan/tilt: {e}")

    def go_home(self):
        if self.current_camera:
            try:
                self.current_camera.pantilt_home()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to go home: {e}")

    def reset_pan_tilt(self):
        if self.current_camera:
            try:
                self.current_camera.pantilt_reset()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset pan/tilt: {e}")

    # Zoom Tab
    def zoom_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        zoom_group = QGroupBox("Zoom Control")
        zoom_layout = QVBoxLayout()

        # Zoom slider
        zoom_slider_layout = QHBoxLayout()
        zoom_slider_label = QLabel("Zoom:")
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(0, 100)
        self.zoom_slider.valueChanged.connect(self.zoom_slider_changed)
        self.zoom_value_label = QLabel("0%")
        
        zoom_slider_layout.addWidget(zoom_slider_label)
        zoom_slider_layout.addWidget(self.zoom_slider)
        zoom_slider_layout.addWidget(self.zoom_value_label)

        # Zoom speed control
        zoom_speed_layout = QHBoxLayout()
        zoom_speed_label = QLabel("Zoom Speed:")
        self.zoom_speed_slider = QSlider(Qt.Horizontal)
        self.zoom_speed_slider.setRange(-7, 7)
        self.zoom_speed_slider.valueChanged.connect(self.zoom_speed_changed)
        self.zoom_speed_value_label = QLabel("0")

        zoom_speed_layout.addWidget(zoom_speed_label)
        zoom_speed_layout.addWidget(self.zoom_speed_slider)
        zoom_speed_layout.addWidget(self.zoom_speed_value_label)

        zoom_layout.addLayout(zoom_slider_layout)
        zoom_layout.addLayout(zoom_speed_layout)
        zoom_group.setLayout(zoom_layout)

        layout.addWidget(zoom_group)
        tab.setLayout(layout)
        return tab

    def zoom_slider_changed(self):
        value = self.zoom_slider.value()
        self.zoom_value_label.setText(f"{value}%")
        if self.current_camera:
            try:
                self.current_camera.zoom_to(value / 100)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to zoom: {e}")

    def zoom_speed_changed(self):
        value = self.zoom_speed_slider.value()
        self.zoom_speed_value_label.setText(str(value))
        if self.current_camera:
            try:
                self.current_camera.zoom(value)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set zoom speed: {e}")

    # Focus Tab
    def focus_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        focus_mode_group = QGroupBox("Focus Mode")
        focus_mode_layout = QHBoxLayout()

        self.focus_mode_combo = QComboBox()
        self.focus_mode_combo.addItems(["Auto", "Manual", "Auto/Manual", "One Push Trigger", "Infinity"])
        focus_mode_btn = QPushButton("Set Focus Mode")
        focus_mode_btn.clicked.connect(self.set_focus_mode)

        focus_mode_layout.addWidget(self.focus_mode_combo)
        focus_mode_layout.addWidget(focus_mode_btn)
        focus_mode_group.setLayout(focus_mode_layout)

        manual_focus_group = QGroupBox("Manual Focus")
        manual_focus_layout = QVBoxLayout()

        focus_slider_layout = QHBoxLayout()
        focus_slider_label = QLabel("Focus:")
        self.focus_slider = QSlider(Qt.Horizontal)
        self.focus_slider.setRange(-7, 7)
        self.focus_slider.valueChanged.connect(self.focus_changed)
        self.focus_value_label = QLabel("0")

        focus_slider_layout.addWidget(focus_slider_label)
        focus_slider_layout.addWidget(self.focus_slider)
        focus_slider_layout.addWidget(self.focus_value_label)

        manual_focus_layout.addLayout(focus_slider_layout)
        manual_focus_group.setLayout(manual_focus_layout)

        layout.addWidget(focus_mode_group)
        layout.addWidget(manual_focus_group)
        tab.setLayout(layout)
        return tab

    def set_focus_mode(self):
        if self.current_camera:
            mode = self.focus_mode_combo.currentText().lower()
            try:
                self.current_camera.set_focus_mode(mode)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set focus mode: {e}")

    def focus_changed(self):
        value = self.focus_slider.value()
        self.focus_value_label.setText(str(value))
        if self.current_camera:
            try:
                self.current_camera.manual_focus(value)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to adjust focus: {e}")

    # White Balance Tab
    def white_balance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        wb_mode_group = QGroupBox("White Balance Mode")
        wb_mode_layout = QHBoxLayout()

        self.wb_mode_combo = QComboBox()
        self.wb_mode_combo.addItems(["Auto", "Indoor", "Outdoor", "One Push", "Auto Tracing", "Manual", "Color Temperature", "One Push Trigger"])
        wb_mode_btn = QPushButton("Set WB Mode")
        wb_mode_btn.clicked.connect(self.set_wb_mode)

        wb_mode_layout.addWidget(self.wb_mode_combo)
        wb_mode_layout.addWidget(wb_mode_btn)
        wb_mode_group.setLayout(wb_mode_layout)

        gain_group = QGroupBox("Gain Control")
        gain_layout = QGridLayout()

        red_gain_label = QLabel("Red Gain (0-255):")
        self.red_gain_spin = QSpinBox()
        self.red_gain_spin.setRange(0, 255)
        red_gain_btn = QPushButton("Set Red Gain")
        red_gain_btn.clicked.connect(self.set_red_gain)

        blue_gain_label = QLabel("Blue Gain (0-255):")
        self.blue_gain_spin = QSpinBox()
        self.blue_gain_spin.setRange(0, 255)
        blue_gain_btn = QPushButton("Set Blue Gain")
        blue_gain_btn.clicked.connect(self.set_blue_gain)

        gain_layout.addWidget(red_gain_label, 0, 0)
        gain_layout.addWidget(self.red_gain_spin, 0, 1)
        gain_layout.addWidget(red_gain_btn, 0, 2)
        gain_layout.addWidget(blue_gain_label, 1, 0)
        gain_layout.addWidget(self.blue_gain_spin, 1, 1)
        gain_layout.addWidget(blue_gain_btn, 1, 2)
        gain_group.setLayout(gain_layout)

        layout.addWidget(wb_mode_group)
        layout.addWidget(gain_group)
        tab.setLayout(layout)
        return tab

    def set_wb_mode(self):
        if self.current_camera:
            mode = self.wb_mode_combo.currentText().lower()
            try:
                self.current_camera.white_balance_mode(mode)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set white balance mode: {e}")

    def set_red_gain(self):
        if self.current_camera:
            gain = self.red_gain_spin.value()
            try:
                self.current_camera.set_red_gain(gain)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set red gain: {e}")

    def set_blue_gain(self):
        if self.current_camera:
            gain = self.blue_gain_spin.value()
            try:
                self.current_camera.set_blue_gain(gain)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set blue gain: {e}")

    # Exposure Tab
    def exposure_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        exposure_mode_group = QGroupBox("Exposure Mode")
        exposure_mode_layout = QHBoxLayout()

        self.exposure_mode_combo = QComboBox()
        self.exposure_mode_combo.addItems(["Auto", "Manual", "Shutter Priority", "Iris Priority", "Bright"])
        exposure_mode_btn = QPushButton("Set Exposure Mode")
        exposure_mode_btn.clicked.connect(self.set_exposure_mode)

        exposure_mode_layout.addWidget(self.exposure_mode_combo)
        exposure_mode_layout.addWidget(exposure_mode_btn)
        exposure_mode_group.setLayout(exposure_mode_layout)

        manual_exposure_group = QGroupBox("Manual Exposure Controls")
        manual_exposure_layout = QVBoxLayout()

        # Gain control
        gain_layout = QHBoxLayout()
        gain_label = QLabel("Gain:")
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 255)
        self.gain_slider.valueChanged.connect(self.gain_changed)
        self.gain_value_label = QLabel("0")

        gain_layout.addWidget(gain_label)
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.gain_value_label)

        # Shutter control
        shutter_layout = QHBoxLayout()
        shutter_label = QLabel("Shutter:")
        self.shutter_slider = QSlider(Qt.Horizontal)
        self.shutter_slider.setRange(0, 21)
        self.shutter_slider.valueChanged.connect(self.shutter_changed)
        self.shutter_value_label = QLabel("0")

        shutter_layout.addWidget(shutter_label)
        shutter_layout.addWidget(self.shutter_slider)
        shutter_layout.addWidget(self.shutter_value_label)

        # Iris control
        iris_layout = QHBoxLayout()
        iris_label = QLabel("Iris:")
        self.iris_slider = QSlider(Qt.Horizontal)
        self.iris_slider.setRange(0, 17)
        self.iris_slider.valueChanged.connect(self.iris_changed)
        self.iris_value_label = QLabel("0")

        iris_layout.addWidget(iris_label)
        iris_layout.addWidget(self.iris_slider)
        iris_layout.addWidget(self.iris_value_label)

        manual_exposure_layout.addLayout(gain_layout)
        manual_exposure_layout.addLayout(shutter_layout)
        manual_exposure_layout.addLayout(iris_layout)
        manual_exposure_group.setLayout(manual_exposure_layout)

        layout.addWidget(exposure_mode_group)
        layout.addWidget(manual_exposure_group)
        tab.setLayout(layout)
        return tab

    def set_exposure_mode(self):
        if self.current_camera:
            mode = self.exposure_mode_combo.currentText().lower()
            try:
                self.current_camera.autoexposure_mode(mode)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set exposure mode: {e}")

    def gain_changed(self):
        value = self.gain_slider.value()
        self.gain_value_label.setText(str(value))
        if self.current_camera:
            try:
                self.current_camera.set_gain(value)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set gain: {e}")

    def shutter_changed(self):
        value = self.shutter_slider.value()
        self.shutter_value_label.setText(str(value))
        if self.current_camera:
            try:
                self.current_camera.set_shutter(value)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set shutter: {e}")

    def iris_changed(self):
        value = self.iris_slider.value()
        self.iris_value_label.setText(str(value))
        if self.current_camera:
            try:
                self.current_camera.set_iris(value)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set iris: {e}")

    # Image Flip Tab
    def image_flip_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        flip_group = QGroupBox("Image Flip Control")
        flip_layout = QHBoxLayout()

        self.flip_horizontal_checkbox = QCheckBox("Horizontal Flip")
        self.flip_vertical_checkbox = QCheckBox("Vertical Flip")

        flip_btn = QPushButton("Set Flip Mode")
        flip_btn.clicked.connect(self.set_flip_mode)

        flip_layout.addWidget(self.flip_horizontal_checkbox)
        flip_layout.addWidget(self.flip_vertical_checkbox)
        flip_layout.addWidget(flip_btn)
        flip_group.setLayout(flip_layout)

        layout.addWidget(flip_group)
        tab.setLayout(layout)
        return tab

    def set_flip_mode(self):
        if self.current_camera:
            horizontal = self.flip_horizontal_checkbox.isChecked()
            vertical = self.flip_vertical_checkbox.isChecked()
            try:
                self.current_camera.flip(horizontal, vertical)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set flip mode: {e}")

    # Defog Tab
    def defog_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        defog_group = QGroupBox("Defog Control")
        defog_layout = QHBoxLayout()

        self.defog_checkbox = QCheckBox("Defog Mode")
        defog_btn = QPushButton("Set Defog Mode")
        defog_btn.clicked.connect(self.set_defog_mode)

        defog_layout.addWidget(self.defog_checkbox)
        defog_layout.addWidget(defog_btn)
        defog_group.setLayout(defog_layout)

        layout.addWidget(defog_group)
        tab.setLayout(layout)
        return tab

    def set_defog_mode(self):
        if self.current_camera:
            mode = self.defog_checkbox.isChecked()
            try:
                self.current_camera.defog(mode)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set defog mode: {e}")

    # Presets Tab
    def presets_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        save_preset_group = QGroupBox("Save Preset")
        save_preset_layout = QHBoxLayout()

        save_preset_label = QLabel("Preset Number (0-15):")
        self.save_preset_spin = QSpinBox()
        self.save_preset_spin.setRange(0, 15)
        save_preset_btn = QPushButton("Save Preset")
        save_preset_btn.clicked.connect(self.save_preset)

        save_preset_layout.addWidget(save_preset_label)
        save_preset_layout.addWidget(self.save_preset_spin)
        save_preset_layout.addWidget(save_preset_btn)
        save_preset_group.setLayout(save_preset_layout)

        recall_preset_group = QGroupBox("Recall Preset")
        recall_preset_layout = QHBoxLayout()

        recall_preset_label = QLabel("Preset Number (0-15):")
        self.recall_preset_spin = QSpinBox()
        self.recall_preset_spin.setRange(0, 15)
        recall_preset_btn = QPushButton("Recall Preset")
        recall_preset_btn.clicked.connect(self.recall_preset)

        recall_preset_layout.addWidget(recall_preset_label)
        recall_preset_layout.addWidget(self.recall_preset_spin)
        recall_preset_layout.addWidget(recall_preset_btn)
        recall_preset_group.setLayout(recall_preset_layout)

        layout.addWidget(save_preset_group)
        layout.addWidget(recall_preset_group)
        tab.setLayout(layout)
        return tab

    def save_preset(self):
        if self.current_camera:
            preset_num = self.save_preset_spin.value()
            try:
                self.current_camera.save_preset(preset_num)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save preset: {e}")

    def recall_preset(self):
        if self.current_camera:
            preset_num = self.recall_preset_spin.value()
            try:
                self.current_camera.recall_preset(preset_num)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to recall preset: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CameraController()
    window.show()
    sys.exit(app.exec_())