import serial
import ledControl
import inputControl

import time
import threading

class Controller:
  def __init__(self, port):
    # Open up Serial connection with AutoTracker
    self.ser = serial.Serial(port, 2000000)
    self.LED = ledControl.LedController(self.ser)
    self.inputCtrl = inputControl.inputController(self.ser)

    # Flag to indicate when to stop the thread
    self.stop_serial_thread = False
    self.stop_led_thread = False

    time.sleep(0.1)

    # Create a new thread to read from the serial port
    self.serial_thread = threading.Thread(target=self.read_from_port, args=())
    self.serial_thread.start()

    # Create a new thread to update LEDs
    self.led_thread = threading.Thread(target=self.update_led, args=())
    self.led_thread.start()

  # Function to read incoming data from the serial port and keep all variables updated
  def read_from_port(self):
    while not self.stop_serial_thread:
      try:
        data = self.ser.readline()[:-2].split(b',')
        if (data != b''): 
          self.inputCtrl.processPacket(data, self.LED)
      except:
        time.sleep(0.01)

  def update_led(self):
    while not self.stop_led_thread:
      try:
        self.LED.show()
      except Exception as e:
        print(f"Error updating LEDs: {e}")
      time.sleep(0.01)

  def close(self):
    # Stop the serial_thread at the end of the program
    self.stop_serial_thread = True
    self.serial_thread.join()

    # Stop the led_thread at the end of the program
    self.stop_led_thread = True
    self.led_thread.join()

    #Close Serial Connection with autotracker
    self.ser.close()

  def are_threads_alive(self):
    return self.serial_thread.is_alive() and self.led_thread.is_alive()