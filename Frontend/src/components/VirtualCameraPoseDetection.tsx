import { useEffect, useRef, useState, useCallback } from 'react'
import { usePoseDetection } from '../hooks/usePoseDetection'
import type { VirtualCamera } from '../types/camera'
import type { VirtualCameraPoseData } from '../types/poseDetection'

interface VirtualCameraPoseDetectionProps {
  videoElement: HTMLVideoElement | null
  virtualCameras: VirtualCamera[]
  onPoseDetection: (data: VirtualCameraPoseData[]) => void
  detectionInterval?: number
}

const VirtualCameraPoseDetection = ({
  videoElement,
  virtualCameras,
  onPoseDetection,
  detectionInterval = 100 // Run detection every 100ms by default
}: VirtualCameraPoseDetectionProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number>()
  const lastDetectionTime = useRef(0)
  const { detectPoses, isLoading, error } = usePoseDetection({ runningMode: 'IMAGE' })

  const processFrame = useCallback(() => {
    if (!videoElement || !canvasRef.current || isLoading) {
      animationFrameRef.current = requestAnimationFrame(processFrame)
      return
    }

    const now = performance.now()
    if (now - lastDetectionTime.current < detectionInterval) {
      animationFrameRef.current = requestAnimationFrame(processFrame)
      return
    }
    lastDetectionTime.current = now

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) {
      animationFrameRef.current = requestAnimationFrame(processFrame)
      return
    }

    // Process each active virtual camera
    const activeCameras = virtualCameras.filter(cam => cam.isActive && cam.region)
    const poseDataArray: VirtualCameraPoseData[] = []

    for (const camera of activeCameras) {
      if (!camera.region) continue

      // Calculate pixel coordinates from percentage values
      const srcX = (camera.region.x / 100) * videoElement.videoWidth
      const srcY = (camera.region.y / 100) * videoElement.videoHeight
      const srcWidth = (camera.region.width / 100) * videoElement.videoWidth
      const srcHeight = (camera.region.height / 100) * videoElement.videoHeight

      // Set canvas size to match the region
      canvas.width = srcWidth
      canvas.height = srcHeight

      // Draw the region to canvas
      ctx.drawImage(
        videoElement,
        srcX, srcY, srcWidth, srcHeight,
        0, 0, srcWidth, srcHeight
      )

      // Detect poses in this region
      const poses = detectPoses(canvas)
      
      poseDataArray.push({
        cameraId: camera.id,
        poses,
        timestamp: now
      })
    }

    onPoseDetection(poseDataArray)
    animationFrameRef.current = requestAnimationFrame(processFrame)
  }, [videoElement, virtualCameras, detectPoses, isLoading, detectionInterval, onPoseDetection])

  useEffect(() => {
    if (videoElement && !isLoading) {
      // Start processing when video is playing
      const handlePlay = () => {
        animationFrameRef.current = requestAnimationFrame(processFrame)
      }

      const handlePause = () => {
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current)
        }
      }

      videoElement.addEventListener('play', handlePlay)
      videoElement.addEventListener('pause', handlePause)

      // Start immediately if already playing
      if (!videoElement.paused) {
        handlePlay()
      }

      return () => {
        videoElement.removeEventListener('play', handlePlay)
        videoElement.removeEventListener('pause', handlePause)
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current)
        }
      }
    }
  }, [videoElement, isLoading, processFrame])

  if (error) {
    console.error('Pose detection error:', error)
  }

  // Hidden canvas for processing
  return <canvas ref={canvasRef} style={{ display: 'none' }} />
}

export default VirtualCameraPoseDetection