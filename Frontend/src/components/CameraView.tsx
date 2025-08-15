import { useRef, useEffect, useState, type MouseEvent } from 'react'
import type { VirtualCamera, SelectionState, CameraRegion } from '../types/camera'
import type { VirtualCameraPoseData } from '../types/poseDetection'
import VirtualCameraPoseDetection from './VirtualCameraPoseDetection'
import usePtzTracker from '../hooks/usePtzTracker'
import PersonDetectionOverlay from './PersonDetectionOverlay'

interface CameraViewProps {
  deviceId: string
  virtualCameras: VirtualCamera[]
  selectedCameraId: string | null
  isSelectionMode: boolean
  onRegionSelected: (region: CameraRegion) => void
  enablePersonDetection?: boolean
  sendAutoTrackingCommands?: (commands: Array<{camera_index: number, pan_speed: number, tilt_speed: number}>) => void
}

const CameraView = ({
  deviceId,
  virtualCameras,
  selectedCameraId,
  isSelectionMode,
  onRegionSelected,
  enablePersonDetection = true,
  sendAutoTrackingCommands
}: CameraViewProps) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [poseData, setPoseData] = useState<VirtualCameraPoseData[]>([])
  // PTZ tracker (sends commands to API when enabled)
  usePtzTracker({
    enabled: enablePersonDetection && isStreaming,
    virtualCameras,
    selectedCameraId,
    poseData,
    sendAutoTrackingCommands
  })
  const [selection, setSelection] = useState<SelectionState>({
    isSelecting: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0
  })

  useEffect(() => {
    let stream: MediaStream | null = null

    const startStream = async () => {
      if (!deviceId || !videoRef.current) return

      try {
        // Check if mediaDevices API is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('Camera access is not available. Please ensure you are using HTTPS and a supported browser.')
        }

        // Stop any existing stream
        if (stream) {
          stream.getTracks().forEach(track => track.stop())
        }

        setError(null)
        setIsStreaming(false)

        // Request new stream with selected device
        const newStream = await navigator.mediaDevices.getUserMedia({
          video: {
            deviceId: { exact: deviceId },
            width: { ideal: 1280 },
            height: { ideal: 720 }
          }
        })

        stream = newStream
        videoRef.current.srcObject = newStream
        setIsStreaming(true)
      } catch (err) {
        console.error('Error accessing camera:', err)
        setError(err instanceof Error ? err.message : 'Failed to access camera')
        setIsStreaming(false)
      }
    }

    startStream()

    // Cleanup function
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [deviceId])

  const getRelativeCoordinates = (e: MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current || !videoRef.current) return { x: 0, y: 0 }
    
    const videoRect = videoRef.current.getBoundingClientRect()
    
    // Calculate the actual displayed video dimensions (considering aspect ratio)
    const x = ((e.clientX - videoRect.left) / videoRect.width) * 100
    const y = ((e.clientY - videoRect.top) / videoRect.height) * 100
    
    return { x: Math.max(0, Math.min(100, x)), y: Math.max(0, Math.min(100, y)) }
  }

  const handleMouseDown = (e: MouseEvent<HTMLDivElement>) => {
    if (!isSelectionMode || !selectedCameraId) return
    
    const coords = getRelativeCoordinates(e)
    setSelection({
      isSelecting: true,
      startX: coords.x,
      startY: coords.y,
      currentX: coords.x,
      currentY: coords.y
    })
  }

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!selection.isSelecting) return
    
    const coords = getRelativeCoordinates(e)
    setSelection(prev => ({
      ...prev,
      currentX: coords.x,
      currentY: coords.y
    }))
  }

  const handleMouseUp = () => {
    if (!selection.isSelecting) return
    
    const region: CameraRegion = {
      x: Math.min(selection.startX, selection.currentX),
      y: Math.min(selection.startY, selection.currentY),
      width: Math.abs(selection.currentX - selection.startX),
      height: Math.abs(selection.currentY - selection.startY)
    }
    
    if (region.width > 2 && region.height > 2) {
      onRegionSelected(region)
    }
    
    setSelection({
      isSelecting: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0
    })
  }

  const getSelectionStyle = () => {
    if (!selection.isSelecting) return {}
    
    return {
      left: `${Math.min(selection.startX, selection.currentX)}%`,
      top: `${Math.min(selection.startY, selection.currentY)}%`,
      width: `${Math.abs(selection.currentX - selection.startX)}%`,
      height: `${Math.abs(selection.currentY - selection.startY)}%`
    }
  }

  if (!deviceId) {
    return (
      <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">No camera selected</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="aspect-video bg-red-50 rounded-lg flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-red-600 font-semibold">Camera Error</p>
          <p className="text-red-500 text-sm mt-2">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative">
      <div
        ref={containerRef}
        className={`relative ${isSelectionMode && selectedCameraId ? 'cursor-crosshair' : ''}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full aspect-video bg-black rounded-lg"
        />
        
        {/* Virtual camera regions */}
        {virtualCameras.map(camera => {
          if (!camera.region || !camera.isActive) return null
          
          const isSelected = camera.id === selectedCameraId
          
          return (
            <div
              key={camera.id}
              className={`absolute border-2 ${
                isSelected ? 'border-blue-500 shadow-lg' : 'border-green-500'
              } pointer-events-none`}
              style={{
                left: `${camera.region.x}%`,
                top: `${camera.region.y}%`,
                width: `${camera.region.width}%`,
                height: `${camera.region.height}%`
              }}
            >
              <div className={`absolute -top-6 left-0 px-2 py-1 text-xs font-medium rounded ${
                isSelected ? 'bg-blue-500 text-white' : 'bg-green-500 text-white'
              }`}>
                {camera.name}
              </div>
            </div>
          )
        })}
        
        {/* Selection overlay */}
        {selection.isSelecting && (
          <div
            className="absolute border-2 border-blue-500 bg-blue-500 bg-opacity-20"
            style={getSelectionStyle()}
          />
        )}
        
        {/* Person detection overlays */}
        {enablePersonDetection && isStreaming && (
          <PersonDetectionOverlay
            virtualCameras={virtualCameras}
            poseData={poseData}
            selectedCameraId={selectedCameraId}
          />
        )}
        
        {!isStreaming && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50 rounded-lg">
            <div className="text-white text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto"></div>
              <p className="mt-4">Connecting to camera...</p>
            </div>
          </div>
        )}
      </div>

      {/* Person detection processor */}
      {enablePersonDetection && isStreaming && videoRef.current && (
        <VirtualCameraPoseDetection
          videoElement={videoRef.current}
          virtualCameras={virtualCameras}
          onPoseDetection={setPoseData}
          detectionInterval={100}
        />
      )}

      {/* Status indicator */}
      <div className="absolute top-4 right-4">
        <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
          isStreaming ? 'bg-green-500 text-white' : 'bg-gray-500 text-white'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            isStreaming ? 'bg-white animate-pulse' : 'bg-gray-300'
          }`}></div>
          <span>{isStreaming ? 'Live' : 'Connecting'}</span>
        </div>
      </div>
    </div>
  )
}

export default CameraView