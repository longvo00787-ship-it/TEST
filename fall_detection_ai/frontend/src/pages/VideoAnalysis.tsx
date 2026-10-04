import { useRef, useState } from 'react'
import { Upload, Loader2, AlertTriangle, Download, Play } from 'lucide-react'
import { api } from '../services/api'
import type { VideoAnalysisResult } from '../types/api'
import clsx from 'clsx'

export default function VideoAnalysis() {
  const fileRef = useRef<HTMLInputElement | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<VideoAnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const onSelect = (f: File | null) => {
    setError(null)
    setResult(null)
    setFile(f)
  }

  const analyze = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.analyzeVideo(file)
      setResult(res)
    } catch (e: any) {
      setError(e.message ?? 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const downloadPath = (p: string | null) => {
    if (!p) return '#'
    return `/api/detect/video/download?path=${encodeURIComponent(p)}`
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">Video Analysis</h2>
        <p className="text-sm text-gray-400 mt-1">
          Upload a video to detect persons, classify postures and identify fall events.
        </p>
      </div>

      <div className="card">
        <div
          className={clsx(
            'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors',
            dragOver ? 'border-cyan-400 bg-cyan-500/5' : 'border-dark-500 hover:border-cyan-500'
          )}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault(); setDragOver(false)
            const f = e.dataTransfer.files[0]
            if (f) onSelect(f)
          }}
          onClick={() => fileRef.current?.click()}
        >
          <Upload className="w-10 h-10 mx-auto text-cyan-400 mb-3" />
          <div className="text-gray-200 font-medium">
            {file ? file.name : 'Click or drag video here'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Supported: .mp4, .avi, .mov
          </div>
          <input
            ref={fileRef}
            type="file"
            accept=".mp4,.avi,.mov,video/*"
            className="hidden"
            onChange={(e) => onSelect(e.target.files?.[0] ?? null)}
          />
        </div>

        {file && (
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-300">
              {file.name} · <span className="text-gray-500">{(file.size / 1_048_576).toFixed(2)} MB</span>
            </div>
            <button
              onClick={analyze}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {loading ? 'Processing…' : 'Process Video'}
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="card border-red-500/40 bg-red-500/5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <div className="text-red-200 text-sm">{error}</div>
          </div>
        </div>
      )}

      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <div className="text-xs uppercase text-gray-400">FPS</div>
              <div className="text-2xl font-bold text-cyan-300 mt-1">
                {result.video_info.fps.toFixed(1)}
              </div>
            </div>
            <div className="card">
              <div className="text-xs uppercase text-gray-400">Frames</div>
              <div className="text-2xl font-bold text-purple-300 mt-1">
                {result.total_frames}
              </div>
            </div>
            <div className="card">
              <div className="text-xs uppercase text-gray-400">Duration</div>
              <div className="text-2xl font-bold text-gray-100 mt-1">
                {result.video_info.duration_s.toFixed(1)}s
              </div>
            </div>
            <div className="card">
              <div className="text-xs uppercase text-gray-400">Fall Events</div>
              <div className="text-2xl font-bold text-red-300 mt-1">
                {result.fall_events.length}
              </div>
            </div>
          </div>

          {result.output_video_path && (
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-200">Annotated Output</h3>
                <a
                  href={downloadPath(result.output_video_path)}
                  download
                  className="btn-secondary text-xs"
                >
                  <Download className="w-3 h-3" /> Download
                </a>
              </div>
              <video
                src={downloadPath(result.output_video_path)}
                controls
                className="w-full rounded-lg border border-dark-600"
              />
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-200 mb-3">Fall Events Timeline</h3>
              {result.fall_events.length === 0 ? (
                <div className="text-sm text-gray-500">No fall events detected in this video.</div>
              ) : (
                <div className="space-y-2 max-h-72 overflow-y-auto">
                  {result.fall_events.map((ev, i) => (
                    <div key={i} className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="text-sm font-semibold text-red-200">
                          Frame {ev.frame} · {ev.time_s.toFixed(2)}s
                        </div>
                        <div className="text-xs text-red-300/80">
                          Person #{ev.person_id}
                        </div>
                      </div>
                      <div className="text-xs text-red-200/70 mt-1">
                        Confidence {(ev.confidence * 100).toFixed(0)}%
                        {ev.latency !== null && ` · Latency ${ev.latency.toFixed(2)}s`}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h3 className="text-sm font-semibold text-gray-200 mb-3">Event Timeline (Sample)</h3>
              {result.timeline.length === 0 ? (
                <div className="text-sm text-gray-500">No timeline data.</div>
              ) : (
                <div className="space-y-1 max-h-72 overflow-y-auto text-xs font-mono">
                  {result.timeline.slice(0, 50).map((t, i) => (
                    <div
                      key={i}
                      className={clsx(
                        'px-3 py-1 rounded',
                        t.fall_probability > 0.5 ? 'bg-red-500/15 text-red-200' : 'text-gray-300'
                      )}
                    >
                      {String(Math.floor(t.time_s / 60)).padStart(2, '0')}:
                      {String(Math.floor(t.time_s % 60)).padStart(2, '0')}.
                      {String(Math.floor((t.time_s * 100) % 100)).padStart(2, '0')}{' '}
                      Person #{t.person_id.toString().padStart(2, '0')} {t.posture.toUpperCase()} ·{' '}
                      Fall {(t.fall_probability * 100).toFixed(0)}%
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}