import { useState, useEffect } from 'react'
import WebcamSelector from './WebcamSelector'
import CameraView from './CameraView'
import CameraRegionManager from './CameraRegionManager'
import VirtualCameraPreview from './VirtualCameraPreview'
import CameraMappingManager from './CameraMappingManager'
import { useCameraDevices } from '../hooks/useCameraDevices'
import { useVirtualCameras } from '../hooks/useVirtualCameras'
import { useAutoTracking } from '../hooks/useAutoTracking'

const Dashboard = () => {
  const { devices, loading, error } = useCameraDevices()
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('')
  const [isSelectionMode, setIsSelectionMode] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [enablePersonDetection, setEnablePersonDetection] = useState(true)
  
  const {
    virtualCameras,
    selectedCameraId,
    setSelectedCameraId,
    addVirtualCamera,
    updateVirtualCamera,
    deleteVirtualCamera,
    setRegion,
    toggleCamera,
    importConfiguration
  } = useVirtualCameras()

  const {
    pythonCameras,
    autoTrackingStatus,
    loading: autoTrackingLoading,
    error: autoTrackingError,
    toggleAutoTracking,
    sendAutoTrackingCommands
  } = useAutoTracking()

  // Load saved device ID from localStorage on mount
  useEffect(() => {
    const savedDeviceId = localStorage.getItem('selectedWebcamId')
    if (savedDeviceId) {
      setSelectedDeviceId(savedDeviceId)
    }
  }, [])

  // Save device ID to localStorage when it changes
  useEffect(() => {
    if (selectedDeviceId) {
      localStorage.setItem('selectedWebcamId', selectedDeviceId)
    }
  }, [selectedDeviceId])

  // Auto-select first device if none selected and devices are available
  useEffect(() => {
    if (!selectedDeviceId && devices.length > 0) {
      setSelectedDeviceId(devices[0].deviceId)
    }
  }, [devices, selectedDeviceId])

  const handleRegionSelected = (region: any) => {
    if (selectedCameraId) {
      setRegion(selectedCameraId, region)
      setIsSelectionMode(false)
    }
  }

  const selectedCamera = virtualCameras.find(cam => cam.id === selectedCameraId)

  return (
    <div className="container mx-auto">

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Input Source</h2>
            
            <WebcamSelector
              devices={devices}
              selectedDeviceId={selectedDeviceId}
              onDeviceSelect={setSelectedDeviceId}
              loading={loading}
              error={error}
            />
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <CameraRegionManager
              virtualCameras={virtualCameras}
              selectedCameraId={selectedCameraId}
              selectedWebcamId={selectedDeviceId}
              onSelectCamera={setSelectedCameraId}
              onAddCamera={addVirtualCamera}
              onUpdateCamera={updateVirtualCamera}
              onDeleteCamera={deleteVirtualCamera}
              onToggleCamera={toggleCamera}
              onImportConfiguration={importConfiguration}
            />
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <CameraMappingManager
              virtualCameras={virtualCameras}
              pythonCameras={pythonCameras}
              onUpdateCamera={updateVirtualCamera}
              autoTrackingActive={autoTrackingStatus.auto_tracking_active}
              onToggleAutoTracking={toggleAutoTracking}
            />
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Camera View</h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setEnablePersonDetection(!enablePersonDetection)}
                  className={`px-4 py-2 rounded-lg transition-colors flex items-center space-x-2 ${
                    enablePersonDetection
                      ? 'bg-green-500 text-white hover:bg-green-600'
                      : 'bg-gray-400 text-white hover:bg-gray-500'
                  }`}
                  title={enablePersonDetection ? 'Person detection is ON' : 'Person detection is OFF'}
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                  <span>Person Detection</span>
                </button>
                {selectedCameraId && (
                  <button
                    onClick={() => setIsSelectionMode(!isSelectionMode)}
                    className={`px-4 py-2 rounded-lg transition-colors ${
                      isSelectionMode
                        ? 'bg-red-500 text-white hover:bg-red-600'
                        : 'bg-blue-500 text-white hover:bg-blue-600'
                    }`}
                  >
                    {isSelectionMode ? 'Cancel Selection' : 'Select Region'}
                  </button>
                )}
              </div>
            </div>
            
            <CameraView
              deviceId={selectedDeviceId}
              virtualCameras={virtualCameras}
              selectedCameraId={selectedCameraId}
              isSelectionMode={isSelectionMode}
              onRegionSelected={handleRegionSelected}
              enablePersonDetection={enablePersonDetection}
              sendAutoTrackingCommands={sendAutoTrackingCommands}
            />
          </div>

          {/* Camera info */}
          {selectedCamera && (
            <div className="mt-6 bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Selected Camera: {selectedCamera.name}</h3>
                {selectedCamera.region && (
                  <button
                    onClick={() => setShowPreview(true)}
                    className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors flex items-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <span>Preview Camera</span>
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className="font-medium">{selectedCamera.isActive ? 'Active' : 'Inactive'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Region</p>
                  <p className="font-medium">
                    {selectedCamera.region
                      ? `${Math.round(selectedCamera.region.width)}% × ${Math.round(selectedCamera.region.height)}%`
                      : 'Not defined'
                    }
                  </p>
                </div>
              </div>
              {!selectedCamera.region && (
                <p className="mt-4 text-sm text-gray-500">
                  Click "Select Region" above to define the camera area
                </p>
              )}
            </div>
          )}

          {/* Instructions */}
          {virtualCameras.length === 0 && (
            <div className="mt-6 bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Getting Started</h3>
              <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
                <li>Click the + button in the Virtual Cameras panel to add a new camera</li>
                <li>Give your camera a name (e.g., "Camera 1", "Host", "Guest")</li>
                <li>Select the camera from the list</li>
                <li>Click "Select Region" and drag a rectangle over the desired area</li>
                <li>Repeat for each camera view in your multiview preview</li>
              </ol>
            </div>
          )}
        </div>
      </div>

      {/* Virtual Camera Preview Modal */}
      {showPreview && selectedCamera && selectedCamera.region && (
        <VirtualCameraPreview
          deviceId={selectedDeviceId}
          virtualCamera={selectedCamera}
          onClose={() => setShowPreview(false)}
        />
      )}
    </div>
  )
}

export default Dashboard