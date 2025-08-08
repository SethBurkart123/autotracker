import type { VirtualCamera } from '../types/camera'
import type { VirtualCameraPoseData } from '../types/poseDetection'

interface PersonDetectionOverlayProps {
  virtualCameras: VirtualCamera[]
  poseData: VirtualCameraPoseData[]
  selectedCameraId: string | null
}

const PersonDetectionOverlay = ({
  virtualCameras,
  poseData,
  selectedCameraId
}: PersonDetectionOverlayProps) => {
  return (
    <>
      {virtualCameras.map(camera => {
        if (!camera.region || !camera.isActive) return null

        const cameraPoseData = poseData.find(data => data.cameraId === camera.id)
        if (!cameraPoseData || cameraPoseData.poses.length === 0) return null

        const isSelected = camera.id === selectedCameraId

        return (
          <div
            key={`${camera.id}-poses`}
            className="absolute pointer-events-none"
            style={{
              left: `${camera.region.x}%`,
              top: `${camera.region.y}%`,
              width: `${camera.region.width}%`,
              height: `${camera.region.height}%`
            }}
          >
            {cameraPoseData.poses.map((pose, index) => (
              <div
                key={`${camera.id}-pose-${index}`}
                className={`absolute border-2 ${
                  isSelected ? 'border-green-400' : 'border-blue-400'
                }`}
                style={{
                  left: `${pose.x * 100}%`,
                  top: `${pose.y * 100}%`,
                  width: `${pose.width * 100}%`,
                  height: `${pose.height * 100}%`
                }}
              >
                {/* Confidence indicator */}
                <div
                  className={`absolute -top-6 left-0 px-1 py-0.5 text-xs font-medium rounded ${
                    isSelected ? 'bg-green-400 text-black' : 'bg-blue-400 text-white'
                  }`}
                >
                  Person {Math.round(pose.confidence * 100)}%
                </div>
              </div>
            ))}
          </div>
        )
      })}
    </>
  )
}

export default PersonDetectionOverlay