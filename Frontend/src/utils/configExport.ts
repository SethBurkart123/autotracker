import type { VirtualCamera } from '../types/camera'

export interface CameraConfiguration {
  version: string
  exportDate: string
  virtualCameras: VirtualCamera[]
  selectedWebcamId?: string
}

export const exportCameraConfiguration = (
  virtualCameras: VirtualCamera[], 
  selectedWebcamId?: string
): void => {
  const config: CameraConfiguration = {
    version: '1.0.0',
    exportDate: new Date().toISOString(),
    virtualCameras,
    selectedWebcamId
  }

  const blob = new Blob([JSON.stringify(config, null, 2)], {
    type: 'application/json'
  })

  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `camera-config-${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export const importCameraConfiguration = (file: File): Promise<CameraConfiguration> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string
        const config = JSON.parse(text) as CameraConfiguration
        
        // Basic validation
        if (!config.virtualCameras || !Array.isArray(config.virtualCameras)) {
          throw new Error('Invalid configuration: missing or invalid virtualCameras array')
        }
        
        // Validate each virtual camera
        for (const camera of config.virtualCameras) {
          if (!camera.id || !camera.name || typeof camera.isActive !== 'boolean') {
            throw new Error('Invalid configuration: invalid camera object structure')
          }
          
          if (camera.region) {
            const { x, y, width, height } = camera.region
            if (typeof x !== 'number' || typeof y !== 'number' || 
                typeof width !== 'number' || typeof height !== 'number') {
              throw new Error('Invalid configuration: invalid camera region')
            }
          }
        }
        
        resolve(config)
      } catch (error) {
        reject(new Error(`Failed to parse configuration file: ${error instanceof Error ? error.message : 'Unknown error'}`))
      }
    }
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'))
    }
    
    reader.readAsText(file)
  })
} 