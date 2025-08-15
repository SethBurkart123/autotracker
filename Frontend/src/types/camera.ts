export interface MediaDeviceInfo {
  deviceId: string
  groupId: string
  kind: string
  label: string
}

export interface CameraState {
  isActive: boolean
  deviceId: string | null
  error: string | null
}

export interface TrackingData {
  x: number
  y: number
  width: number
  height: number
  confidence: number
}

export interface TrackerConfig {
  modelPath?: string
  maxFaces?: number
  minConfidence?: number
  updateInterval?: number
}

export interface CameraRegion {
  x: number
  y: number
  width: number
  height: number
}

export interface VirtualCamera {
  id: string
  name: string
  region: CameraRegion | null
  isActive: boolean
  pythonCameraIndex: number | null // Maps to Python camera index for control
}

export interface SelectionState {
  isSelecting: boolean
  startX: number
  startY: number
  currentX: number
  currentY: number
}

export interface PythonCamera {
  index: number
  ip: string
  color: number[]
}