export interface PoseDetectionResult {
  x: number // Relative X position (0-1)
  y: number // Relative Y position (0-1)
  width: number // Relative width (0-1)
  height: number // Relative height (0-1)
  confidence: number
}

export interface VirtualCameraPoseData {
  cameraId: string
  poses: PoseDetectionResult[]
  timestamp: number
}