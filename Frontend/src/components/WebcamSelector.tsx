import type { MediaDeviceInfo } from '../types/camera'

interface WebcamSelectorProps {
  devices: MediaDeviceInfo[]
  selectedDeviceId: string
  onDeviceSelect: (deviceId: string) => void
  loading: boolean
  error: string | null
}

const WebcamSelector = ({
  devices,
  selectedDeviceId,
  onDeviceSelect,
  loading,
  error
}: WebcamSelectorProps) => {
  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 rounded"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-red-600 text-sm">
        <p className="font-semibold">Error accessing cameras:</p>
        <p>{error}</p>
        {error.includes('HTTPS') && (
          <p className="mt-2 text-xs">
            Tip: Camera access requires HTTPS. If testing locally, use https://localhost or use a tunneling service like ngrok.
          </p>
        )}
      </div>
    )
  }

  if (devices.length === 0) {
    return (
      <div className="text-gray-600 text-sm">
        <p>No cameras detected</p>
        <p className="mt-2 text-xs">Please connect a camera and refresh the page</p>
      </div>
    )
  }

  return (
    <div>
      <label htmlFor="webcam-select" className="block text-sm font-medium text-gray-700 mb-2">
        Select Webcam
      </label>
      <select
        id="webcam-select"
        value={selectedDeviceId}
        onChange={(e) => onDeviceSelect(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        {devices.map((device) => (
          <option key={device.deviceId} value={device.deviceId}>
            {device.label || `Camera ${device.deviceId.slice(0, 8)}...`}
          </option>
        ))}
      </select>
      <p className="mt-2 text-xs text-gray-500">
        {devices.length} camera{devices.length !== 1 ? 's' : ''} detected
      </p>
    </div>
  )
}

export default WebcamSelector