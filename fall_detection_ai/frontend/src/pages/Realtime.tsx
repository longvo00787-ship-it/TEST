import { useEffect, useRef, useState } from 'react'
import { Camera, CameraOff, RefreshCw, AlertTriangle, Users } from 'lucide-react'
import { api } from '../services/api'
import type { ProcessResult } from '../types/api'
import clsx from 'clsx'

export default function Realtime() {
  const [active, setActive] = useState(false)
  const [result, setResult] = useState<ProcessResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [cameraIndex, setCameraIndex] = useState(0)
  const [imgError, setImgError] = useState(false)
  const pollRef = useRef<number | null>(null)
  const imgRef = useRef<HTMLImageElement | null>(null)

  const start = async () => {
    setError(null)
    setImgError(false)
    try {
      const res = await api.startWebcam(cameraIndex)
      setActive(true)
      // begin poll
      pollRef.current = window.setInterval(async () => {
        try {
          const r = await api.webcamLatest()
          if (r.active && r.result) setResult(r.result)
        } catch {/* */}
      }, 500)
    } catch (e: any) {
      setError(e.message ?? 'Cannot start webcam')
    }
  }

  const stop = async () => {
    try {
      await api.stopWebcam()
    } catch {/* */}
    setActive(false)
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
      // try to stop webcam on unmount
      api.stopWebcam().catch(() => {})
    }
  }, [])

  // Refresh image by changing key
  const [imgKey, setImgKey] = useState(0)
  useEffect(() => {
    if (!active) return
    const id = window.setInterval(() => setImgKey(k => k + 1), 200) // ~5 FPS UI refresh
    return () => clearInterval(id)
  }, [active])

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Realtime Monitoring</h2>
          <p className="text-sm text-gray-400 mt-1">
            Live webcam stream with person tracking, posture classification and fall detection.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={cameraIndex}
            onChange={(e) => setCameraIndex(Number(e.target.value))}
            disabled={active}
            className="input max-w-[140px]"
          >
            <option value={0}>Camera 0</option>
            <option value={1}>Camera 1</option>
          </select>
          {!active ? (
            <button onClick={start} className="btn-primary">
              <Camera className="w-4 h-4" /> Start Camera
            </button>
          ) : (
            <button onClick={stop} className="btn-danger">
              <CameraOff className="w-4 h-4" /> Stop Camera
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="card border-red-500/40 bg-red-500/5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <div className="text-red-200 text-sm">{error}</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200">Live Stream</h3>
            <div className="flex items-center gap-4 text-xs text-gray-400">
              {result && (
                <>
                  <span>FPS: <b className="text-cyan-300">{result.fps.toFixed(1)}</b></span>
                  <span>Inference: <b className="text-cyan-300">{result.inference_ms.toFixed(0)} ms</b></span>
                </>
              )}
            </div>
          </div>
          <div className="aspect-video bg-dark-950 rounded-lg border border-dark-700 flex items-center justify-center overflow-hidden relative">
            {active && !imgError ? (
              <img
                key={imgKey}
                ref={imgRef}
                src={api.webcamFrameUrl()}
                alt="webcam"
                className="w-full h-full object-contain"
                onError={() => setImgError(true)}
              />
            ) : (
              <div className="text-center text-gray-500">
                <Camera className="w-12 h-12 mx-auto mb-2 opacity-30" />
                <div className="text-sm">
                  {active ? (imgError ? 'Cannot read frames. Try another camera.' : 'Waiting for frames…') : 'Camera is off. Press Start.'}
                </div>
              </div>
            )}
            {result?.fall_event && (
              <div className="absolute top-4 left-4 right-4 alert-pulse">
                <div className="bg-red-500 text-white font-bold text-center py-3 rounded-lg glow-red">
                  ⚠ FALL DETECTED — Alerting...
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-semibold text-gray-200">Detected Persons</h3>
            </div>
            {result && result.detections.length > 0 ? (
              <div className="space-y-2">
                {result.detections.map(d => (
                  <div
                    key={d.person_id}
                    className={clsx(
                      'p-3 rounded-lg border',
                      d.fall_event
                        ? 'bg-red-500/10 border-red-500/40'
                        : 'bg-dark-800 border-dark-600'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={clsx(
                          'w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold',
                          d.fall_event ? 'bg-red-500/30 text-red-200' : 'bg-cyan-500/20 text-cyan-200'
                        )}>
                          #{d.person_id.toString().padStart(2, '0')}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-100">{d.posture.toUpperCase()}</div>
                          <div className="text-xs text-gray-400">
                            Conf: {(d.confidence * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-gray-400">Fall prob</div>
                        <div className={clsx(
                          'text-sm font-bold',
                          d.fall_probability > 0.65 ? 'text-red-400' : 'text-cyan-300'
                        )}>
                          {(d.fall_probability * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                    {d.fall_event && d.alert_latency !== null && (
                      <div className="mt-2 text-xs text-red-200">
                        Alert latency: {d.alert_latency.toFixed(2)}s
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                {active ? 'Scanning for persons…' : 'Camera is off.'}
              </div>
            )}
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-gray-200 mb-3">Pipeline</h3>
            <ol className="text-xs text-gray-400 space-y-1 list-decimal pl-4">
              <li>YOLO Person Detect (ByteTrack)</li>
              <li>Pose estimation (17 keypoints)</li>
              <li>Feature extraction</li>
              <li>Posture classification</li>
              <li>Temporal fall analysis</li>
              <li>Alert + DB log</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}