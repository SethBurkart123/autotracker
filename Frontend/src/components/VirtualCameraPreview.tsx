import { useRef, useEffect, useState, type MouseEvent as ReactMouseEvent } from 'react'
import type { VirtualCamera } from '../types/camera'

interface VirtualCameraPreviewProps {
  deviceId: string
  virtualCamera: VirtualCamera
  onClose: () => void
}

const VirtualCameraPreview = ({ deviceId, virtualCamera, onClose }: VirtualCameraPreviewProps) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const animationFrameRef = useRef<number>()
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [position, setPosition] = useState({ x: window.innerWidth / 2 - 320, y: window.innerHeight / 2 - 180 })
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  useEffect(() => {
    let stream: MediaStream | null = null

    const startStream = async () => {
      if (!deviceId || !videoRef.current || !virtualCamera.region) return

      try {
        setError(null)
        setIsStreaming(false)

        const newStream = await navigator.mediaDevices.getUserMedia({
          video: {
            deviceId: { exact: deviceId },
            width: { ideal: 1920 },
            height: { ideal: 1080 }
          }
        })

        stream = newStream
        videoRef.current.srcObject = newStream
        
        // Wait for video to be ready
        videoRef.current.onloadedmetadata = () => {
          videoRef.current!.play()
          setIsStreaming(true)
          drawFrame()
        }
      } catch (err) {
        console.error('Error accessing camera for preview:', err)
        setError(err instanceof Error ? err.message : 'Failed to access camera')
        setIsStreaming(false)
      }
    }

    const drawFrame = () => {
      if (!videoRef.current || !canvasRef.current || !virtualCamera.region) return

      const video = videoRef.current
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      // Check if video is ready
      if (video.readyState === video.HAVE_ENOUGH_DATA) {
        const { x, y, width, height } = virtualCamera.region

        // Calculate source rectangle from video
        const sourceX = (video.videoWidth * x) / 100
        const sourceY = (video.videoHeight * y) / 100
        const sourceWidth = (video.videoWidth * width) / 100
        const sourceHeight = (video.videoHeight * height) / 100

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height)

        // Draw the cropped portion of the video
        try {
          ctx.drawImage(
            video,
            sourceX, sourceY, sourceWidth, sourceHeight,  // Source rectangle
            0, 0, canvas.width, canvas.height             // Destination rectangle
          )
        } catch (e) {
          console.error('Error drawing frame:', e)
        }
      }

      // Continue drawing
      animationFrameRef.current = requestAnimationFrame(drawFrame)
    }

    startStream()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [deviceId, virtualCamera.region])

  const handleMouseDown = (e: ReactMouseEvent) => {
    if ((e.target as HTMLElement).closest('button')) return
    setIsDragging(true)
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y })
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging) return
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, dragStart])

  if (!virtualCamera.region) return null

  const { x, y, width, height } = virtualCamera.region

  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      <div
        ref={containerRef}
        className="absolute bg-white rounded-lg shadow-2xl pointer-events-auto"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
          width: '640px',
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
        onMouseDown={handleMouseDown}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold">{virtualCamera.name} Preview</h3>
            {isStreaming && (
              <div className="flex items-center space-x-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live</span>
              </div>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            title="Close preview"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Video Container */}
        <div className="relative bg-black" style={{ height: '360px' }}>
          {/* Hidden video element */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{ display: 'none' }}
          />
          
          {error ? (
            <div className="absolute inset-0 flex items-center justify-center p-4">
              <div className="text-center">
                <p className="text-red-400 font-semibold">Preview Error</p>
                <p className="text-red-300 text-sm mt-2">{error}</p>
              </div>
            </div>
          ) : (
            <div className="relative w-full h-full">
              <canvas
                ref={canvasRef}
                width={640}
                height={360}
                className="w-full h-full"
              />
              {!isStreaming && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-50">
                  <div className="text-white text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto"></div>
                    <p className="mt-2 text-sm">Loading preview...</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>Region: {Math.round(width)}% × {Math.round(height)}%</span>
            <span>Position: ({Math.round(x)}%, {Math.round(y)}%)</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VirtualCameraPreview