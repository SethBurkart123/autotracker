# AutoTracker Frontend

A web application for creating virtual camera regions and detecting faces in each region using MediaPipe.

## Features

- Select webcam input source
- Create multiple virtual camera regions
- Face detection for each virtual camera region
- Export/import camera configurations
- Real-time face tracking with bounding boxes

## Setup

1. Install dependencies:
```
npm install
```

2. Start the development server:
```
npm run dev
```

3. Open your browser to the URL shown (typically http://localhost:5173)

## Face Detection

The app uses MediaPipe Face Detection to identify faces in each virtual camera region. Each region runs its own face detection independently, providing:

- Face bounding boxes with confidence scores
- Real-time tracking at ~10 FPS per region
- GPU acceleration when available

## Usage

1. Select your webcam from the dropdown
2. Click the + button to add virtual cameras
3. Select a camera and click "Select Region" to define its area
4. Toggle "Face Detection" to see face bounding boxes
5. Export your configuration to save your setup

## Requirements

- Modern web browser with WebRTC support
- HTTPS connection (or localhost) for camera access
- Webcam or virtual camera device