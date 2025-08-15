import { useState, useEffect, useCallback } from 'react'
import type { PythonCamera } from '../types/camera'

interface AutoTrackingCommand {
  camera_index: number
  pan_speed: number
  tilt_speed: number
}

interface AutoTrackingStatus {
  auto_tracking_active: boolean
  current_camera_index: number
  auto_tracking_commands: Record<number, { pan_speed: number; tilt_speed: number }>
}

const API_BASE_URL = 'http://localhost:9000/api'

export const useAutoTracking = () => {
  const [pythonCameras, setPythonCameras] = useState<PythonCamera[]>([])
  const [autoTrackingStatus, setAutoTrackingStatus] = useState<AutoTrackingStatus>({
    auto_tracking_active: false,
    current_camera_index: 0,
    auto_tracking_commands: {}
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch Python cameras
  const fetchPythonCameras = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/python-cameras`)
      if (!response.ok) throw new Error('Failed to fetch Python cameras')
      const data = await response.json()
      setPythonCameras(data.cameras)
    } catch (err) {
      console.error('Error fetching Python cameras:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch Python cameras')
    }
  }, [])

  // Fetch auto tracking status
  const fetchAutoTrackingStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/autotrack/status`)
      if (!response.ok) throw new Error('Failed to fetch auto tracking status')
      const data = await response.json()
      setAutoTrackingStatus(data)
    } catch (err) {
      console.error('Error fetching auto tracking status:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch auto tracking status')
    }
  }, [])

  // Toggle auto tracking
  const toggleAutoTracking = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/autotrack/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!response.ok) throw new Error('Failed to toggle auto tracking')
      const data = await response.json()
      setAutoTrackingStatus(prev => ({
        ...prev,
        auto_tracking_active: data.auto_tracking_active
      }))
    } catch (err) {
      console.error('Error toggling auto tracking:', err)
      setError(err instanceof Error ? err.message : 'Failed to toggle auto tracking')
    }
  }, [])

  // Send auto tracking commands (for continuous streaming)
  const sendAutoTrackingCommands = useCallback(async (commands: AutoTrackingCommand[]) => {
    try {
      const response = await fetch(`${API_BASE_URL}/autotrack/commands`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ commands })
      })
      if (!response.ok) throw new Error('Failed to send auto tracking commands')
    } catch (err) {
      // Don't log every command error to avoid spam, but store it
      setError(err instanceof Error ? err.message : 'Failed to send auto tracking commands')
    }
  }, [])

  // Initial data fetch
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true)
      await Promise.all([fetchPythonCameras(), fetchAutoTrackingStatus()])
      setLoading(false)
    }
    
    initializeData()
  }, [fetchPythonCameras, fetchAutoTrackingStatus])

  // Periodic status updates (every 2 seconds)
  useEffect(() => {
    const interval = setInterval(fetchAutoTrackingStatus, 2000)
    return () => clearInterval(interval)
  }, [fetchAutoTrackingStatus])

  return {
    pythonCameras,
    autoTrackingStatus,
    loading,
    error,
    toggleAutoTracking,
    sendAutoTrackingCommands,
    refetchPythonCameras: fetchPythonCameras
  }
}
