import { useEffect, useRef, useState, useCallback } from 'react'
import { PoseLandmarker, FilesetResolver } from '@mediapipe/tasks-vision'
import type { PoseDetectionResult } from '../types/poseDetection'

interface UsePoseDetectionOptions {
  minDetectionConfidence?: number
  minTrackingConfidence?: number
  runningMode?: 'IMAGE' | 'VIDEO'
}

export const usePoseDetection = (options: UsePoseDetectionOptions = {}) => {
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const detectorRef = useRef<PoseLandmarker | null>(null)
  const lastVideoTime = useRef(-1)

  useEffect(() => {
    let cancelled = false

    const initializeDetector = async () => {
      try {
        setIsLoading(true)
        setError(null)

        // Load MediaPipe vision WASM files
        const vision = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
        )

        // Create pose landmarker
        const detector = await PoseLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
            delegate: 'GPU'
          },
          runningMode: options.runningMode || 'VIDEO',
          numPoses: 5, // Track up to 5 people
          minPoseDetectionConfidence: options.minDetectionConfidence || 0.5,
          minTrackingConfidence: options.minTrackingConfidence || 0.5
        })

        if (!cancelled) {
          detectorRef.current = detector
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          console.error('Failed to initialize pose detector:', err)
          setError(err instanceof Error ? err.message : 'Failed to initialize pose detector')
          setIsLoading(false)
        }
      }
    }

    initializeDetector()

    return () => {
      cancelled = true
      if (detectorRef.current) {
        detectorRef.current = null
      }
    }
  }, [options.minDetectionConfidence, options.minTrackingConfidence, options.runningMode])

  const detectPoses = useCallback((
    videoElement: HTMLVideoElement | HTMLCanvasElement,
    timestamp?: number
  ): PoseDetectionResult[] => {
    if (!detectorRef.current || !videoElement) {
      return []
    }

    try {
      // For video mode, we need to provide timestamp
      if (options.runningMode === 'VIDEO' && videoElement instanceof HTMLVideoElement) {
        const videoTimestamp = timestamp || performance.now()
        
        // Skip if we've already processed this frame
        if (videoTimestamp === lastVideoTime.current) {
          return []
        }
        lastVideoTime.current = videoTimestamp

        const results = detectorRef.current.detectForVideo(videoElement, videoTimestamp)
        
        return results.landmarks.map((landmarks, index) => {
          // Calculate bounding box from pose landmarks
          let minX = 1, minY = 1, maxX = 0, maxY = 0
          
          // Use key body points to create a bounding box
          const keyPoints = [
            0, 1, 2, 3, 4, 5, 6,  // Head points
            11, 12, 13, 14, 15, 16,  // Shoulders and arms
            23, 24, 25, 26, 27, 28  // Hips and legs
          ]
          
          keyPoints.forEach(pointIndex => {
            if (pointIndex < landmarks.length) {
              const point = landmarks[pointIndex]
              minX = Math.min(minX, point.x)
              minY = Math.min(minY, point.y)
              maxX = Math.max(maxX, point.x)
              maxY = Math.max(maxY, point.y)
            }
          })
          
          // Add some padding to the bounding box
          const padding = 0.05
          minX = Math.max(0, minX - padding)
          minY = Math.max(0, minY - padding)
          maxX = Math.min(1, maxX + padding)
          maxY = Math.min(1, maxY + padding)
          
          return {
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
            confidence: results.worldLandmarks[index] ? 0.9 : 0.7 // Higher confidence if 3D landmarks available
          }
        })
      } else {
        // For image mode or canvas
        const results = detectorRef.current.detect(videoElement as HTMLCanvasElement)
        
        return results.landmarks.map((landmarks, index) => {
          // Calculate bounding box from pose landmarks
          let minX = 1, minY = 1, maxX = 0, maxY = 0
          
          // Use key body points to create a bounding box
          const keyPoints = [
            0, 1, 2, 3, 4, 5, 6,  // Head points
            11, 12, 13, 14, 15, 16,  // Shoulders and arms
            23, 24, 25, 26, 27, 28  // Hips and legs
          ]
          
          keyPoints.forEach(pointIndex => {
            if (pointIndex < landmarks.length) {
              const point = landmarks[pointIndex]
              minX = Math.min(minX, point.x)
              minY = Math.min(minY, point.y)
              maxX = Math.max(maxX, point.x)
              maxY = Math.max(maxY, point.y)
            }
          })
          
          // Add some padding to the bounding box
          const padding = 0.05
          minX = Math.max(0, minX - padding)
          minY = Math.max(0, minY - padding)
          maxX = Math.min(1, maxX + padding)
          maxY = Math.min(1, maxY + padding)
          
          return {
            x: minX,
            y: minY,
            width: maxX - minX,
            height: maxY - minY,
            confidence: results.worldLandmarks[index] ? 0.9 : 0.7 // Higher confidence if 3D landmarks available
          }
        })
      }
    } catch (err) {
      console.error('Pose detection error:', err)
      return []
    }
  }, [options.runningMode])

  return {
    detectPoses,
    isLoading,
    error
  }
}