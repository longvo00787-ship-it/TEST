import { useEffect, useState } from 'react'
import { Cpu, Play, AlertTriangle, Loader2 } from 'lucide-react'
import { api } from '../services/api'
import type { TrainingJob, ModelInfo } from '../types/api'

export default function Training() {
  const [jobs, setJobs] = useState<TrainingJob[]>([])
  const [latest, setLatest] = useState<TrainingJob | null>(null)
  const [info, setInfo] = useState<ModelInfo | null>(null)
  const [epochs, setEpochs] = useState(50)
  const [batch, setBatch] = useState(16)
  const [imgsz, setImgsz] = useState(640)
  const [lr, setLr] = useState(0.001)
  const [device, setDevice] = useState('auto')
  const [starting, setStarting] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const refresh = async () => {
    try {
      const [s, m] = await Promise.all([api.trainingStatus(), api.modelInfo()])
      setJobs(s.jobs)
      setLatest(s.latest)
      setInfo(m)
    } catch {/* */}
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [])

  const start = async () => {
    setStarting(true)
    setMsg(null)
    try {
      const r = await api.startTraining({ epochs, batch, imgsz, lr, device })
      if (r.ok) setMsg('Training job queued. Backend is running it in background.')
      else setMsg('Failed to start.')
    } catch (e: any) {
      setMsg(e.message)
    } finally {
      setStarting(false)
      refresh()
    }
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">Model Training</h2>
        <p className="text-sm text-gray-400 mt-1">
          Configure and launch YOLO training jobs on your dataset.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">Training Parameters</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 uppercase">Epochs</label>
              <input
                type="number"
                value={epochs}
                onChange={(e) => setEpochs(Number(e.target.value))}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Batch size</label>
              <input
                type="number"
                value={batch}
                onChange={(e) => setBatch(Number(e.target.value))}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Image size</label>
              <input
                type="number"
                value={imgsz}
                onChange={(e) => setImgsz(Number(e.target.value))}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Learning rate</label>
              <input
                type="number"
                step="0.0001"
                value={lr}
                onChange={(e) => setLr(Number(e.target.value))}
                className="input mt-1"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Device</label>
              <select
                value={device}
                onChange={(e) => setDevice(e.target.value)}
                className="input mt-1"
              >
                <option value="auto">Auto</option>
                <option value="cpu">CPU</option>
                <option value="cuda">CUDA</option>
                <option value="0">GPU 0</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase">Model</label>
              <input
                type="text"
                value="yolov8n.pt"
                readOnly
                className="input mt-1"
              />
            </div>
          </div>
          <div className="mt-5">
            <button onClick={start} disabled={starting} className="btn-primary">
              {starting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
              {starting ? 'Starting…' : 'Start Training'}
            </button>
            {msg && <div className="text-sm text-cyan-300 mt-3">{msg}</div>}
          </div>
        </div>

        <div className="card">
          <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" /> Current Model
          </h3>
          {info && (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">Detect</span>
                <span className="text-gray-100">{Path.basename(info.detect_model ?? '')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Pose</span>
                <span className="text-gray-100">{Path.basename(info.pose_model ?? '')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Trained exists</span>
                <span className={info.trained_model_exists ? 'text-green-300' : 'text-yellow-300'}>
                  {info.trained_model_exists ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Latest Training Job</h3>
        {!latest ? (
          <div className="text-sm text-gray-500">No training jobs yet.</div>
        ) : (
          <div className="space-y-3">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <div className="text-xs text-gray-400 uppercase">Status</div>
                <div className={`
                  text-sm font-semibold mt-1
                  ${latest.status === 'completed' ? 'text-green-300' :
                    latest.status === 'failed' ? 'text-red-300' : 'text-cyan-300'}
                `}>
                  {latest.status.toUpperCase()}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase">Epochs</div>
                <div className="text-sm font-semibold mt-1 text-gray-100">{latest.epochs}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase">Batch</div>
                <div className="text-sm font-semibold mt-1 text-gray-100">{latest.batch_size}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase">Device</div>
                <div className="text-sm font-semibold mt-1 text-gray-100">{latest.device}</div>
              </div>
            </div>

            {latest.status === 'running' ? (
              <div className="text-sm text-cyan-300 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Training is running in background. Results will appear when it completes.
              </div>
            ) : latest.status === 'failed' ? (
              <div className="text-sm text-red-300 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> Training failed. Check logs.
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2 border-t border-dark-700">
                <Metric label="mAP50" value={latest.final_map50} />
                <Metric label="mAP50-95" value={latest.final_map50_95} />
                <Metric label="Precision" value={latest.final_precision} />
                <Metric label="Recall" value={latest.final_recall} />
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Training Jobs History</h3>
        {jobs.length === 0 ? (
          <div className="text-sm text-gray-500">No training jobs recorded.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-dark-700">
                  <th className="py-2">ID</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Started</th>
                  <th className="py-2">Model</th>
                  <th className="py-2">Epochs</th>
                  <th className="py-2">mAP50</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map(j => (
                  <tr key={j.id} className="border-b border-dark-700/50 text-gray-200">
                    <td className="py-2">#{j.id}</td>
                    <td className="py-2">
                      <span className={`
                        px-2 py-0.5 rounded text-xs
                        ${j.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                          j.status === 'failed' ? 'bg-red-500/20 text-red-300' :
                          'bg-cyan-500/20 text-cyan-300'}
                      `}>
                        {j.status}
                      </span>
                    </td>
                    <td className="py-2">{new Date(j.started_at).toLocaleString()}</td>
                    <td className="py-2">{j.model_name}</td>
                    <td className="py-2">{j.epochs}</td>
                    <td className="py-2">{j.final_map50 !== null ? j.final_map50.toFixed(3) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number | null }) {
  return (
    <div>
      <div className="text-xs text-gray-400 uppercase">{label}</div>
      <div className="text-sm font-semibold mt-1 text-cyan-300">
        {value !== null ? value.toFixed(4) : '—'}
      </div>
    </div>
  )
}

// Inline path basename
const Path = {
  basename: (p: string) => {
    if (!p) return '—'
    return p.replace(/\\/g, '/').split('/').pop()
  },
}