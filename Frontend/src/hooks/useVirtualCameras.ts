import { useState, useEffect } from 'react'
import type { VirtualCamera, CameraRegion } from '../types/camera'
import type { CameraConfiguration } from '../utils/configExport'

const STORAGE_KEY = 'virtualCameras'

// Helper function to load cameras from localStorage
const loadCamerasFromStorage = (): VirtualCamera[] => {
  try {
    const savedCameras = localStorage.getItem(STORAGE_KEY)
    if (savedCameras) {
      return JSON.parse(savedCameras)
    }
  } catch (error) {
    console.error('Failed to load virtual cameras:', error)
  }
  return []
}

export const useVirtualCameras = () => {
  // Initialize state directly from localStorage - no race condition!
  const [virtualCameras, setVirtualCameras] = useState<VirtualCamera[]>(loadCamerasFromStorage)
  const [selectedCameraId, setSelectedCameraId] = useState<string | null>(null)

  // Save to localStorage whenever cameras change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(virtualCameras))
  }, [virtualCameras])

  const addVirtualCamera = (name: string) => {
    const newCamera: VirtualCamera = {
      id: Date.now().toString(),
      name,
      region: null,
      isActive: true
    }
    setVirtualCameras(prev => [...prev, newCamera])
    return newCamera.id
  }

  const updateVirtualCamera = (id: string, updates: Partial<VirtualCamera>) => {
    setVirtualCameras(prev =>
      prev.map(camera =>
        camera.id === id ? { ...camera, ...updates } : camera
      )
    )
  }

  const deleteVirtualCamera = (id: string) => {
    setVirtualCameras(prev => prev.filter(camera => camera.id !== id))
    if (selectedCameraId === id) {
      setSelectedCameraId(null)
    }
  }

  const setRegion = (id: string, region: CameraRegion) => {
    updateVirtualCamera(id, { region })
  }

  const toggleCamera = (id: string) => {
    setVirtualCameras(prev =>
      prev.map(camera =>
        camera.id === id ? { ...camera, isActive: !camera.isActive } : camera
      )
    )
  }

  const importConfiguration = (config: CameraConfiguration, replaceExisting: boolean = false) => {
    if (replaceExisting) {
      setVirtualCameras(config.virtualCameras)
      setSelectedCameraId(null)
    } else {
      // Merge with existing cameras, ensuring unique IDs
      const existingIds = new Set(virtualCameras.map(cam => cam.id))
      const importedCameras = config.virtualCameras.map(camera => {
        let newId = camera.id
        let counter = 1
        while (existingIds.has(newId)) {
          newId = `${camera.id}_${counter}`
          counter++
        }
        return { ...camera, id: newId }
      })
      setVirtualCameras(prev => [...prev, ...importedCameras])
    }
  }

  return {
    virtualCameras,
    selectedCameraId,
    setSelectedCameraId,
    addVirtualCamera,
    updateVirtualCamera,
    deleteVirtualCamera,
    setRegion,
    toggleCamera,
    importConfiguration
  }
}