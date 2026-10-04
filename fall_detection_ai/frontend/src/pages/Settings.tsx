import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Cpu, Info } from 'lucide-react'
import { api } from '../services/api'
import type { ModelInfo } from '../types/api'

export default function Settings() {
  const [info, setInfo] = useState<ModelInfo | null>(null)

  useEffect(() => {
    api.modelInfo().then(setInfo).catch(() => {})
  }, [])

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">System Settings</h2>
        <p className="text-sm text-gray-400 mt-1">
          Model configuration and runtime information.
        </p>
      </div>

      {info && (
        <>
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-cyan-400" /> Model Configuration
            </h3>
            <div className="space-y-3">
              <Row label="Detection model" value={info.detect_model ?? '—'} />
              <Row label="Pose model" value={info.pose_model ?? '—'} />
              <Row label="Trained model path" value={info.trained_model_path} mono />
              <Row label="Trained exists" value={info.trained_model_exists ? 'Yes' : 'No'} accent={info.trained_model_exists ? 'green' : 'yellow'} />
              <Row label="Method" value={info.method} />
            </div>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
              <Info className="w-4 h-4 text-cyan-400" /> Runtime
            </h3>
            <div className="space-y-3">
              <Row label="Device" value={info.device} />
              <Row label="Model loaded" value={info.model_loaded ? 'Yes' : 'No'} accent={info.model_loaded ? 'green' : 'red'} />
              <Row label="Pose loaded" value={info.pose_loaded ? 'Yes' : 'No'} accent={info.pose_loaded ? 'green' : 'red'} />
            </div>
          </div>
        </>
      )}

      <div className="card border-cyan-500/30 bg-cyan-500/5">
        <h3 className="text-sm font-semibold text-cyan-100 mb-2">Switch Database</h3>
        <p className="text-sm text-cyan-200/80 leading-relaxed">
          Database mặc định là SQLite. Để chuyển sang PostgreSQL, set environment variable
          <code className="mx-1 px-2 py-0.5 bg-dark-800 rounded text-cyan-100">DATABASE_URL</code>
          trước khi start backend, ví dụ:
        </p>
        <pre className="mt-3 p-3 bg-dark-900/80 rounded text-xs text-cyan-200 border border-dark-700 overflow-x-auto">
{`export DATABASE_URL="postgresql://user:pass@localhost:5432/falldb"
python -m uvicorn backend.main:app`}
        </pre>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">API Endpoints</h3>
        <ul className="text-sm text-gray-300 space-y-1.5 font-mono">
          <li>GET /api/health</li>
          <li>GET /api/model-info</li>
          <li>POST /api/detect/image</li>
          <li>POST /api/detect/video</li>
          <li>POST /api/detect/webcam/start</li>
          <li>POST /api/detect/webcam/stop</li>
          <li>GET /api/detect/webcam/frame</li>
          <li>GET /api/events</li>
          <li>GET /api/metrics</li>
          <li>POST /api/training/start</li>
          <li>GET /api/training/status</li>
          <li>GET /api/evaluation</li>
          <li>POST /api/evaluation/run-yolo</li>
          <li>GET /api/system/stats</li>
          <li>GET /api/dataset/info</li>
          <li>POST /api/dataset/upload-video</li>
          <li>GET /api/experiments/comparison</li>
        </ul>
      </div>
    </div>
  )
}

function Row({ label, value, mono, accent }: { label: string; value: string; mono?: boolean; accent?: 'green' | 'red' | 'yellow' }) {
  const colorMap = {
    green: 'text-green-300',
    red: 'text-red-300',
    yellow: 'text-yellow-300',
  }
  return (
    <div className="flex items-start justify-between gap-4 py-2 border-b border-dark-700/50 last:border-b-0">
      <div className="text-sm text-gray-400">{label}</div>
      <div className={`text-sm text-right break-all ${mono ? 'font-mono text-xs' : ''} ${accent ? colorMap[accent] : 'text-gray-100'}`}>
        {value}
      </div>
    </div>
  )
}