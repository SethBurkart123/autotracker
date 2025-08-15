import { useEffect, useMemo, useRef } from 'react'
import type { VirtualCamera } from '../types/camera'
import type { PoseDetectionResult, VirtualCameraPoseData } from '../types/poseDetection'

export type TrackerStatePhase = 'idle' | 'tracking' | 'lost' | 'stationary' | 'constant' | 'accelerating' | 'decelerating'

export interface PtzTrackerConfig {
  smoothingAlpha: number
  smoothingAlphaAccel: number
  lookaheadSeconds: number
  deadZoneWidth: number
  deadZoneHeight: number
  normalZoneWidth: number
  normalZoneHeight: number
  urgentZoneWidth: number
  urgentZoneHeight: number
  criticalZoneWidth: number
  criticalZoneHeight: number
  kpNormal: number
  kdNormal: number
  kpUrgent: number
  kdUrgent: number
  kpCritical: number
  kdCritical: number
  maxVelocity: number // normalized screen units per second
  maxAcceleration: number // per second^2
  maxJerk: number // per second^3
  noDetectionHoldMs: number
  velocityDecayPerSecond: number // when lost, decay camera velocity toward 0
  velocityNoiseFloor: number // below this, treat as zero
}

export interface PtzTrackerDebug {
  phase: TrackerStatePhase
  subjectCenter: { x: number; y: number } | null
  predictedCenter: { x: number; y: number } | null
  errorFromCenter: { x: number; y: number } | null
  apparentVelocity: { x: number; y: number }
  worldVelocity: { x: number; y: number }
  cameraVelocity: { x: number; y: number }
  acceleration: { x: number; y: number }
  zone: 'dead' | 'normal' | 'urgent' | 'critical' | 'none'
}

const DEFAULTS: PtzTrackerConfig = {
  smoothingAlpha: 0.3,
  smoothingAlphaAccel: 0.3,
  lookaheadSeconds: 0.4,
  deadZoneWidth: 0.3,
  deadZoneHeight: 0.3,
  normalZoneWidth: 0.6,
  normalZoneHeight: 0.6,
  urgentZoneWidth: 0.8,
  urgentZoneHeight: 0.8,
  criticalZoneWidth: 0.98,
  criticalZoneHeight: 0.98,
  kpNormal: 0.8,
  kdNormal: 0.2,
  kpUrgent: 1.5,
  kdUrgent: 0.4,
  kpCritical: 3.0,
  kdCritical: 0.8,
  maxVelocity: 1.2,
  maxAcceleration: 2.5,
  maxJerk: 15,
  noDetectionHoldMs: 400,
  velocityDecayPerSecond: 0.9,
  velocityNoiseFloor: 0.005
}

interface UsePtzTrackerArgs {
  enabled: boolean
  virtualCameras: VirtualCamera[]
  selectedCameraId: string | null
  poseData: VirtualCameraPoseData[]
  config?: Partial<PtzTrackerConfig>
  sendAutoTrackingCommands?: (commands: Array<{camera_index: number, pan_speed: number, tilt_speed: number}>) => void
}

export const usePtzTracker = ({
  enabled,
  virtualCameras,
  selectedCameraId,
  poseData,
  config,
  sendAutoTrackingCommands
}: UsePtzTrackerArgs) => {
  const cfg: PtzTrackerConfig = useMemo(() => ({ ...DEFAULTS, ...(config || {}) }), [config])

  // Persistent state across frames
  const lastTimestampRef = useRef<number | null>(null)
  const lastSubjectPosRef = useRef<{ x: number; y: number } | null>(null)
  const cameraVelRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const accelRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const vApparentRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const aRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 })
  const lastErrorRef = useRef<{ x: number; y: number } | null>(null)
  const lastDetectionAtRef = useRef<number | null>(null)
  const phaseRef = useRef<TrackerStatePhase>('idle')

  const getSelectedCameraRegion = (): VirtualCamera | null => {
    if (!selectedCameraId) return null
    const cam = virtualCameras.find(c => c.id === selectedCameraId) || null
    if (!cam || !cam.region || !cam.isActive) return null
    return cam
  }

  const selectSubject = (
    detections: PoseDetectionResult[],
    lastPos: { x: number; y: number } | null
  ): { x: number; y: number } | null => {
    if (!detections || detections.length === 0) return null
    // Prefer closest to previous position; fallback to highest confidence
    if (lastPos) {
      let bestIdx = 0
      let bestDist = Number.POSITIVE_INFINITY
      for (let i = 0; i < detections.length; i++) {
        const d = detections[i]
        const cx = d.x + d.width / 2
        const cy = d.y + d.height / 2
        const dx = cx - lastPos.x
        const dy = cy - lastPos.y
        const dist = dx * dx + dy * dy
        if (dist < bestDist) {
          bestDist = dist
          bestIdx = i
        }
      }
      const s = detections[bestIdx]
      return { x: s.x + s.width / 2, y: s.y + s.height / 2 }
    }
    // No lastPos
    const best = detections.reduce((acc, d) => (d.confidence > acc.confidence ? d : acc), detections[0])
    return { x: best.x + best.width / 2, y: best.y + best.height / 2 }
  }

  const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value))

  const applyJerkLimitedAccel = (
    currentVel: { x: number; y: number },
    targetVel: { x: number; y: number },
    currentAccel: { x: number; y: number },
    dt: number
  ) => {
    const desiredAccel = {
      x: clamp((targetVel.x - currentVel.x) / dt, -cfg.maxAcceleration, cfg.maxAcceleration),
      y: clamp((targetVel.y - currentVel.y) / dt, -cfg.maxAcceleration, cfg.maxAcceleration)
    }
    const maxDeltaA = cfg.maxJerk * dt
    const deltaAx = clamp(desiredAccel.x - currentAccel.x, -maxDeltaA, maxDeltaA)
    const deltaAy = clamp(desiredAccel.y - currentAccel.y, -maxDeltaA, maxDeltaA)
    const newAccel = { x: currentAccel.x + deltaAx, y: currentAccel.y + deltaAy }
    const newVel = {
      x: clamp(currentVel.x + newAccel.x * dt, -cfg.maxVelocity, cfg.maxVelocity),
      y: clamp(currentVel.y + newAccel.y * dt, -cfg.maxVelocity, cfg.maxVelocity)
    }
    return { newVel, newAccel }
  }

  const computeZoneAndGains = (errX: number, errY: number) => {
    const absX = Math.abs(errX)
    const absY = Math.abs(errY)

    const inside = (w: number, h: number) => absX <= w / 2 && absY <= h / 2

    if (inside(cfg.deadZoneWidth, cfg.deadZoneHeight)) {
      return { zone: 'dead' as const, kp: 0, kd: 0 }
    }
    if (inside(cfg.normalZoneWidth, cfg.normalZoneHeight)) {
      return { zone: 'normal' as const, kp: cfg.kpNormal, kd: cfg.kdNormal }
    }
    if (inside(cfg.urgentZoneWidth, cfg.urgentZoneHeight)) {
      return { zone: 'urgent' as const, kp: cfg.kpUrgent, kd: cfg.kdUrgent }
    }
    if (inside(cfg.criticalZoneWidth, cfg.criticalZoneHeight)) {
      return { zone: 'critical' as const, kp: cfg.kpCritical, kd: cfg.kdCritical }
    }
    return { zone: 'none' as const, kp: cfg.kpCritical, kd: cfg.kdCritical }
  }

  const decayTowardZero = (v: number, dt: number) => {
    const decayFactor = Math.pow(clamp(1 - cfg.velocityDecayPerSecond, 0, 0.999), dt)
    const nv = Math.abs(v) < cfg.velocityNoiseFloor ? 0 : v * decayFactor
    return nv
  }

  const computePhase = (speed: number, accelMag: number): TrackerStatePhase => {
    const vTol = 0.02
    const aTol = 0.05
    if (speed < vTol) return 'stationary'
    if (Math.abs(accelMag) < aTol) return 'constant'
    return accelMag > 0 ? 'accelerating' : 'decelerating'
  }

  useEffect(() => {
    if (!enabled) return
    const cam = getSelectedCameraRegion()
    if (!cam) return

    const pd = poseData.find(p => p.cameraId === cam.id)
    if (!pd) return

    const nowTs = pd.timestamp
    const lastTs = lastTimestampRef.current
    const dt = lastTs ? Math.max((nowTs - lastTs) / 1000, 0.001) : 0

    const lastPos = lastSubjectPosRef.current
    const subjectCenter = selectSubject(pd.poses, lastPos)

    if (subjectCenter) {
      lastDetectionAtRef.current = nowTs
    }

    // Time since last detection
    const timeSinceDetection = lastDetectionAtRef.current ? nowTs - lastDetectionAtRef.current : Number.POSITIVE_INFINITY

    // Update apparent velocity
    if (subjectCenter && lastPos && dt > 0) {
      const measured = {
        x: (subjectCenter.x - lastPos.x) / dt,
        y: (subjectCenter.y - lastPos.y) / dt
      }
      vApparentRef.current = {
        x: cfg.smoothingAlpha * measured.x + (1 - cfg.smoothingAlpha) * vApparentRef.current.x,
        y: cfg.smoothingAlpha * measured.y + (1 - cfg.smoothingAlpha) * vApparentRef.current.y
      }
      const aMeasured = {
        x: (vApparentRef.current.x - (vApparentRef.current.x - cfg.smoothingAlpha * (vApparentRef.current.x - measured.x))) / dt,
        y: (vApparentRef.current.y - (vApparentRef.current.y - cfg.smoothingAlpha * (vApparentRef.current.y - measured.y))) / dt
      }
      aRef.current = {
        x: cfg.smoothingAlphaAccel * aMeasured.x + (1 - cfg.smoothingAlphaAccel) * aRef.current.x,
        y: cfg.smoothingAlphaAccel * aMeasured.y + (1 - cfg.smoothingAlphaAccel) * aRef.current.y
      }
    } else if (!subjectCenter && timeSinceDetection > cfg.noDetectionHoldMs) {
      // No detection for a while; slowly decay apparent velocity toward zero
      vApparentRef.current = {
        x: decayTowardZero(vApparentRef.current.x, dt || 0.016),
        y: decayTowardZero(vApparentRef.current.y, dt || 0.016)
      }
    }

    // Update world velocity estimate: v_world = v_camera + v_apparent
    const vCamera = cameraVelRef.current
    const vApp = vApparentRef.current
    const vWorld = { x: vCamera.x + vApp.x, y: vCamera.y + vApp.y }

    // Predict future screen position using v_apparent = v_world - v_camera
    const a = aRef.current
    const currentPos = subjectCenter || lastPos || { x: 0.5, y: 0.5 }
    const vAppForPrediction = { x: vWorld.x - vCamera.x, y: vWorld.y - vCamera.y }
    const t = cfg.lookaheadSeconds
    const predicted = {
      x: currentPos.x + vAppForPrediction.x * t + 0.5 * a.x * t * t,
      y: currentPos.y + vAppForPrediction.y * t + 0.5 * a.y * t * t
    }

    // Error from center (0.5, 0.5)
    // Scale error from center; interpret zone widths/heights as fractions of full frame
    const error = { x: predicted.x - 0.5, y: predicted.y - 0.5 }
    const { zone, kp, kd } = computeZoneAndGains(error.x, error.y)

    // Derivative on error (D term)
    const lastErr = lastErrorRef.current
    const derr = lastErr && dt > 0 ? { x: (error.x - lastErr.x) / dt, y: (error.y - lastErr.y) / dt } : { x: 0, y: 0 }

    // Feedback correction (in screen units/s)
    const vFeedback = zone === 'dead'
      ? { x: 0, y: 0 }
      : { x: -(kp * error.x + kd * derr.x), y: -(kp * error.y + kd * derr.y) }

    // Feedforward: maintain tracking velocity when centered (dead zone)
    const vFeedforward = zone === 'dead' ? vWorld : vCamera

    // Combine and clamp
    const targetVel = {
      x: clamp(vFeedforward.x + vFeedback.x, -cfg.maxVelocity, cfg.maxVelocity),
      y: clamp(vFeedforward.y + vFeedback.y, -cfg.maxVelocity, cfg.maxVelocity)
    }

    // Apply jerk/accel limits
    if (lastTs != null) {
      const { newVel, newAccel } = applyJerkLimitedAccel(vCamera, targetVel, accelRef.current, dt || 0.016)
      cameraVelRef.current = newVel
      accelRef.current = newAccel
    }

    // When no detection for a while, decay camera velocity smoothly
    if (!subjectCenter && timeSinceDetection > cfg.noDetectionHoldMs) {
      const dtUse = dt || 0.016
      cameraVelRef.current = {
        x: decayTowardZero(cameraVelRef.current.x, dtUse),
        y: decayTowardZero(cameraVelRef.current.y, dtUse)
      }
    }

    // Phase estimation for debug/tuning
    const speed = Math.hypot(vWorld.x, vWorld.y)
    const accelMag = Math.hypot(a.x, a.y)
    phaseRef.current = subjectCenter ? computePhase(speed, accelMag) : timeSinceDetection <= cfg.noDetectionHoldMs ? 'tracking' : 'lost'

    // Send commands to API if available and camera has Python mapping
    // Map normalized velocity to VISCA speed scale [-24, 24]
    const panSpeed = Math.round(cameraVelRef.current.x * 24)
    const tiltSpeed = Math.round(cameraVelRef.current.y * 24)
    
    if (sendAutoTrackingCommands && cam.pythonCameraIndex !== null) {
      sendAutoTrackingCommands([{
        camera_index: cam.pythonCameraIndex,
        pan_speed: panSpeed,
        tilt_speed: tiltSpeed
      }])
    }
    
    // Debug logging
    if (Math.abs(panSpeed) + Math.abs(tiltSpeed) > 0) {
      // eslint-disable-next-line no-console
      console.log('[PTZ]', {
        cameraId: cam.id,
        pythonCameraIndex: cam.pythonCameraIndex,
        zone,
        phase: phaseRef.current,
        panSpeed,
        tiltSpeed,
        cameraVelocity: { ...cameraVelRef.current }
      })
    }

    // Update refs for next tick
    if (subjectCenter) {
      lastSubjectPosRef.current = subjectCenter
    }
    lastErrorRef.current = error
    lastTimestampRef.current = nowTs
  }, [enabled, virtualCameras, selectedCameraId, poseData, cfg])

  const debug: PtzTrackerDebug = {
    phase: phaseRef.current,
    subjectCenter: lastSubjectPosRef.current,
    predictedCenter: null, // can be filled if needed in future UI
    errorFromCenter: lastErrorRef.current,
    apparentVelocity: { ...vApparentRef.current },
    worldVelocity: {
      x: cameraVelRef.current.x + vApparentRef.current.x,
      y: cameraVelRef.current.y + vApparentRef.current.y
    },
    cameraVelocity: { ...cameraVelRef.current },
    acceleration: { ...accelRef.current },
    zone: 'none'
  }

  return { debug }
}

export default usePtzTracker


