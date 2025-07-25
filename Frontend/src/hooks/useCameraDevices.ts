import { useState, useEffect } from 'react'
import type { MediaDeviceInfo } from '../types/camera'

export const useCameraDevices = () => {
  const [devices, setDevices] = useState<MediaDeviceInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getDevices = async () => {
      try {
        setLoading(true)
        setError(null)

        // Check if mediaDevices API is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('Camera access is not available. Please ensure you are using HTTPS and a supported browser.')
        }

        // Request camera permissions first
        await navigator.mediaDevices.getUserMedia({ video: true })

        // Get all video input devices
        const allDevices = await navigator.mediaDevices.enumerateDevices()
        const videoDevices = allDevices.filter(device => device.kind === 'videoinput')

        setDevices(videoDevices)
      } catch (err) {
        console.error('Error getting camera devices:', err)
        setError(err instanceof Error ? err.message : 'Failed to get camera devices')
      } finally {
        setLoading(false)
      }
    }

    getDevices()

    // Listen for device changes (only if mediaDevices is available)
    const handleDeviceChange = () => {
      getDevices()
    }

    if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
      navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange)
    }

    return () => {
      if (navigator.mediaDevices && navigator.mediaDevices.removeEventListener) {
        navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange)
      }
    }
  }, [])

  return { devices, loading, error }
}