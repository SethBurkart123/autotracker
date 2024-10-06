#include <FastLED.h>
#include <base64.hpp>

FASTLED_USING_NAMESPACE


// Led Config
#define DATA_PIN 11
#define LED_TYPE SK6812
#define COLOR_ORDER GRB
#define NUM_LEDS 18
CRGB leds[NUM_LEDS];

#define BRIGHTNESS 255
#define FRAMES_PER_SECOND 120

byte buffer[54];  // Buffer to store incoming binary data

// Button matrix
#define COLS 4
#define ROWS 5

// initialise variables
int buttonState[COLS][ROWS] = {
  { 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0 },
  { 0, 0, 0, 0, 0 }
};

int center_pan, center_tilt, center_zoom;
int pan_value, tilt_value, zoom_value;
int oldPan, oldTilt, oldZoom;
int tempVal;

void calibrateJoystick() {
  // Read the initial values of the joystick
  center_pan = analogRead(A6);
  center_tilt = analogRead(A5);
  center_zoom = analogRead(A7);
}

int panTiltZoom(int value, int steps) {
  if (value >= 0) {
    tempVal = map(-1 * value, 0, 1023 - center_pan, 0, -steps - 1);
  } else {
    tempVal = map(value, 0, center_pan, 0, steps + 1);
  }
  if (abs(tempVal) <= steps) {
    return tempVal;
  } 
  if (tempVal > steps) {
    return steps;
  }
  return -steps;
}

void setup() {
  // set digital pins as output - button rows
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);

  // set digital pins as input - button columns
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  pinMode(4, INPUT);
  pinMode(5, INPUT);

  // calibrate joystick
  calibrateJoystick();

  // start serial output
  Serial.begin(2000000);

  // tell FastLED about the LED strip configuration
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS).setCorrection(TypicalLEDStrip);

  // set master brightness control
  FastLED.setBrightness(BRIGHTNESS);
}

void loop() {
  //handle buttons
  for (int row = 6; row <= 10; row++) { // loop through all output rows (for buttons)
    digitalWrite(row, HIGH);

    // loop through all input columns (for buttons)
    for (int col = 2; col <= 5; col++) {

      // check if button has changed state
      if (int(buttonState[col - 2][row - 6]) != int(digitalRead(col))) {
        Serial.println(String(row) + "," + String(col) + "," + String(digitalRead(col)));
        
        // update button array on button change
        buttonState[col - 2][row - 6] = int(digitalRead(col));
      }
    }

    digitalWrite(row, LOW);
  }

  // Your main code goes here
  pan_value = panTiltZoom(analogRead(A6) - center_pan, 24);
  tilt_value = panTiltZoom(analogRead(A5) - center_tilt, 24);
  zoom_value = panTiltZoom(analogRead(A7) - center_zoom, 7);

  // Print out the initial values
  /*Serial.print(pan_value);
  Serial.print(",");
  Serial.print(tilt_value);
  Serial.print(",");
  Serial.println(zoom_value);*/

  
  if (oldPan != pan_value || random(0, 100) == 1) {
    Serial.print(0);
    Serial.print(",");
    Serial.println(pan_value);
    oldPan = pan_value;
  }

  if (oldTilt != tilt_value || random(0, 100) == 1) {
    Serial.print(1);
    Serial.print(",");
    Serial.println(-1*tilt_value);
    oldTilt = tilt_value;
  }

  if (oldZoom != zoom_value || random(0, 100) == 1) {
    Serial.print(2);
    Serial.print(",");
    Serial.println(zoom_value);
    oldZoom = zoom_value;
  }

  // if fifty four bytes of data are available on the serial port
  if (Serial.available() >= 54) {
    // Read last fifty four bytes of binary data from the serial port
    Serial.readBytes(buffer, 54);

    // Clear the serial buffer
    Serial.flush();

    for (int i = 0; i < NUM_LEDS; i++) {
      leds[i] = CRGB(buffer[i * 3], buffer[i * 3 + 1], buffer[i * 3 + 2]);
    }

    // send the 'leds' array out to the actual LED strip
    FastLED.show();

    // Print success message
    Serial.println("ok");
  };

}
