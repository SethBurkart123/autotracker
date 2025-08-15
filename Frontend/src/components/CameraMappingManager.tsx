import { useState, useEffect } from 'react'
import type { VirtualCamera, PythonCamera } from '../types/camera'

interface CameraMappingManagerProps {
  virtualCameras: VirtualCamera[]
  pythonCameras: PythonCamera[]
  onUpdateCamera: (id: string, updates: Partial<VirtualCamera>) => void
  autoTrackingActive: boolean
  onToggleAutoTracking: () => void
}

const CameraMappingManager = ({
  virtualCameras,
  pythonCameras,
  onUpdateCamera,
  autoTrackingActive,
  onToggleAutoTracking
}: CameraMappingManagerProps) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Camera Control Mapping</h2>
        <div className="flex items-center space-x-2">
          <span className="text-sm font-medium text-gray-700">Auto Tracking:</span>
          <button
            onClick={onToggleAutoTracking}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 ${
              autoTrackingActive ? 'bg-red-600' : 'bg-gray-200'
            }`}
            role="switch"
            aria-checked={autoTrackingActive}
          >
            <span
              aria-hidden="true"
              className={`pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow transform ring-0 transition duration-200 ease-in-out ${
                autoTrackingActive ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
          <span className={`text-sm font-medium ${autoTrackingActive ? 'text-red-600' : 'text-gray-500'}`}>
            {autoTrackingActive ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      <div className="space-y-4">
        {virtualCameras.map((camera) => (
          <div key={camera.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex-1">
              <h3 className="font-medium text-gray-900">{camera.name}</h3>
              <p className="text-sm text-gray-500">
                Status: {camera.isActive ? 'Active' : 'Inactive'}
                {camera.region && ' • Region defined'}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium text-gray-700">Control Camera:</label>
                <select
                  value={camera.pythonCameraIndex ?? ''}
                  onChange={(e) => {
                    const value = e.target.value
                    onUpdateCamera(camera.id, {
                      pythonCameraIndex: value === '' ? null : parseInt(value)
                    })
                  }}
                  className="block w-40 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="">None</option>
                  {pythonCameras.map((pythonCamera) => (
                    <option key={pythonCamera.index} value={pythonCamera.index}>
                      Camera {pythonCamera.index} ({pythonCamera.ip})
                    </option>
                  ))}
                </select>
              </div>

              {camera.pythonCameraIndex !== null && (
                <div className="flex items-center space-x-2">
                  <div
                    className="w-4 h-4 rounded-full border"
                    style={{
                      backgroundColor: pythonCameras.find(c => c.index === camera.pythonCameraIndex)
                        ? `rgb(${pythonCameras.find(c => c.index === camera.pythonCameraIndex)!.color.join(',')})`
                        : '#gray'
                    }}
                  />
                  <span className="text-xs text-gray-500">Hardware LED Color</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {virtualCameras.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>No virtual cameras configured yet.</p>
          <p className="text-sm">Add some virtual cameras to set up auto tracking control.</p>
        </div>
      )}

      {pythonCameras.length === 0 && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> No Python cameras detected. Make sure the Python control system is running and accessible.
          </p>
        </div>
      )}
    </div>
  )
}

export default CameraMappingManager
