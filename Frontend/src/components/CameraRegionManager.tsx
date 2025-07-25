import { useState, useRef } from 'react'
import type { VirtualCamera } from '../types/camera'
import type { CameraConfiguration } from '../utils/configExport'
import { exportCameraConfiguration, importCameraConfiguration } from '../utils/configExport'

interface CameraRegionManagerProps {
  virtualCameras: VirtualCamera[]
  selectedCameraId: string | null
  selectedWebcamId: string
  onSelectCamera: (id: string | null) => void
  onAddCamera: (name: string) => void
  onUpdateCamera: (id: string, updates: Partial<VirtualCamera>) => void
  onDeleteCamera: (id: string) => void
  onToggleCamera: (id: string) => void
  onImportConfiguration: (config: CameraConfiguration, replaceExisting?: boolean) => void
}

const CameraRegionManager = ({
  virtualCameras,
  selectedCameraId,
  selectedWebcamId,
  onSelectCamera,
  onAddCamera,
  onUpdateCamera,
  onDeleteCamera,
  onToggleCamera,
  onImportConfiguration
}: CameraRegionManagerProps) => {
  const [isAdding, setIsAdding] = useState(false)
  const [newCameraName, setNewCameraName] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editingName, setEditingName] = useState('')
  const [importError, setImportError] = useState<string | null>(null)
  const [showImportOptions, setShowImportOptions] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleAddCamera = () => {
    if (newCameraName.trim()) {
      onAddCamera(newCameraName.trim())
      setNewCameraName('')
      setIsAdding(false)
    }
  }

  const handleStartEdit = (camera: VirtualCamera) => {
    setEditingId(camera.id)
    setEditingName(camera.name)
  }

  const handleSaveEdit = () => {
    if (editingId && editingName.trim()) {
      onUpdateCamera(editingId, { name: editingName.trim() })
      setEditingId(null)
      setEditingName('')
    }
  }

  const handleCancelEdit = () => {
    setEditingId(null)
    setEditingName('')
  }

  const handleExport = () => {
    exportCameraConfiguration(virtualCameras, selectedWebcamId)
  }

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setImportError(null)
      const config = await importCameraConfiguration(file)
      setShowImportOptions(true)
      
      // Store the config temporarily for the import options dialog
      ;(window as any).tempImportConfig = config
    } catch (error) {
      setImportError(error instanceof Error ? error.message : 'Failed to import configuration')
    }
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleImportOption = (replaceExisting: boolean) => {
    const config = (window as any).tempImportConfig
    if (config) {
      onImportConfiguration(config, replaceExisting)
      delete (window as any).tempImportConfig
    }
    setShowImportOptions(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Virtual Cameras</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleExport}
            className="p-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
            title="Export configuration"
            disabled={virtualCameras.length === 0}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </button>
          <button
            onClick={handleImportClick}
            className="p-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
            title="Import configuration"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
            </svg>
          </button>
          <button
            onClick={() => setIsAdding(true)}
            className="p-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            title="Add new camera"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      <div className="space-y-2">
        {virtualCameras.length === 0 && !isAdding && (
          <p className="text-gray-500 text-sm text-center py-4">
            No virtual cameras yet. Click + to add one.
          </p>
        )}

        {virtualCameras.map((camera) => (
          <div
            key={camera.id}
            className={`p-3 rounded-lg border transition-all cursor-pointer ${
              selectedCameraId === camera.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => onSelectCamera(camera.id)}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                {editingId === camera.id ? (
                  <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="text"
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleSaveEdit()
                        if (e.key === 'Escape') handleCancelEdit()
                      }}
                      className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      autoFocus
                    />
                    <button
                      onClick={handleSaveEdit}
                      className="p-1 text-green-600 hover:bg-green-50 rounded"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <span className="font-medium">{camera.name}</span>
                    {camera.region && (
                      <span className="text-xs text-gray-500">
                        ({Math.round(camera.region.width)}x{Math.round(camera.region.height)})
                      </span>
                    )}
                  </div>
                )}
                {!camera.region && !editingId && (
                  <p className="text-xs text-gray-500 mt-1">Click "Select Region" to define area</p>
                )}
              </div>

              <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => onToggleCamera(camera.id)}
                  className={`p-1 rounded ${
                    camera.isActive ? 'text-green-600 hover:bg-green-50' : 'text-gray-400 hover:bg-gray-50'
                  }`}
                  title={camera.isActive ? 'Active' : 'Inactive'}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d={camera.isActive ? "M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" : "M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"}
                    />
                  </svg>
                </button>
                <button
                  onClick={() => handleStartEdit(camera)}
                  className="p-1 text-gray-600 hover:bg-gray-50 rounded"
                  title="Edit name"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => onDeleteCamera(camera.id)}
                  className="p-1 text-red-600 hover:bg-red-50 rounded"
                  title="Delete camera"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        ))}

        {isAdding && (
          <div className="p-3 rounded-lg border border-blue-300 bg-blue-50">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={newCameraName}
                onChange={(e) => setNewCameraName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddCamera()
                  if (e.key === 'Escape') {
                    setIsAdding(false)
                    setNewCameraName('')
                  }
                }}
                placeholder="Camera name..."
                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
              <button
                onClick={handleAddCamera}
                className="p-1 text-green-600 hover:bg-green-50 rounded"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </button>
              <button
                onClick={() => {
                  setIsAdding(false)
                  setNewCameraName('')
                }}
                className="p-1 text-red-600 hover:bg-red-50 rounded"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Import Error Message */}
      {importError && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-700">{importError}</p>
          </div>
          <button
            onClick={() => setImportError(null)}
            className="mt-2 text-sm text-red-600 hover:text-red-800"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Import Options Dialog */}
      {showImportOptions && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h4 className="text-lg font-semibold mb-4">Import Configuration</h4>
            <p className="text-gray-600 mb-6">
              How would you like to import the configuration?
            </p>
            <div className="flex flex-col space-y-3">
              <button
                onClick={() => handleImportOption(false)}
                className="px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-left"
              >
                <div className="font-medium">Merge with existing</div>
                <div className="text-sm text-blue-100">Add imported cameras to current setup</div>
              </button>
              <button
                onClick={() => handleImportOption(true)}
                className="px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-left"
              >
                <div className="font-medium">Replace all cameras</div>
                <div className="text-sm text-red-100">Remove existing cameras and use imported ones</div>
              </button>
              <button
                onClick={() => setShowImportOptions(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CameraRegionManager