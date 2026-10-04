import { useEffect, useState } from 'react'
import { Activity, Cpu, AlertTriangle, Zap } from 'lucide-react'
import { api } from '../services/api'
import type { ModelInfo } from '../types/api'

export default function TopBar() {
  const [info, setInfo] = useState<ModelInfo | null>(null)

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const data = await api.modelInfo()
        setInfo(data)
      } catch (e) {
        console.error(e)
      }
    }
    fetchInfo()
    const id = setInterval(fetchInfo, 5000)
    return () => clearInterval(id)
  }, [])

  const trained = info?.trained_model_exists
  const modelStatus = trained ? 'Trained Model' : 'Pretrained'
  const modelClass = trained ? 'text-accent-green' : 'text-yellow-400'

  return (
    <header className="h-14 bg-dark-900/60 backdrop-blur border-b border-dark-700 px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Activity className="w-5 h-5 text-cyan-400" />
        <h1 className="text-base font-semibold text-gray-100">
          Fall Detection AI Dashboard
        </h1>
      </div>
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-purple-400" />
          <span className="text-gray-400">Device:</span>
          <span className="text-gray-100 font-medium">{info?.device ?? 'cpu'}</span>
        </div>
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-cyan-400" />
          <span className="text-gray-400">Model:</span>
          <span className={`font-medium ${modelClass}`}>{modelStatus}</span>
        </div>
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-yellow-400" />
          <span className="text-gray-400">Pose:</span>
          <span className={info?.pose_loaded ? 'text-accent-green font-medium' : 'text-red-400'}>
            {info?.pose_loaded ? 'Loaded' : 'Unavailable'}
          </span>
        </div>
      </div>
    </header>
  )
}