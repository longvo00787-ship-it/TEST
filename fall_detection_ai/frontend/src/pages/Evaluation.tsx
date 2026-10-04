import { useEffect, useState } from 'react'
import { BarChart3, Loader2, Play, AlertTriangle } from 'lucide-react'
import { api } from '../services/api'
import type { EvaluationResult } from '../types/api'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

export default function Evaluation() {
  const [results, setResults] = useState<EvaluationResult[]>([])
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const refresh = async () => {
    try {
      const r = await api.evaluation()
      setResults(r.results)
    } catch {/* */}
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 5000)
    return () => clearInterval(id)
  }, [])

  const runEval = async () => {
    setRunning(true)
    setMsg(null)
    try {
      const r = await api.runYoloEval('auto')
      if (!r.ok) setMsg(r.error ?? 'Cannot run evaluation')
      else setMsg('Evaluation started. Refresh in a moment.')
    } catch (e: any) {
      setMsg(e.message)
    } finally {
      setRunning(false)
      setTimeout(refresh, 3000)
    }
  }

  const latestYolo: EvaluationResult | undefined = results.find(r => r.method === 'yolo')
  const latestRule: EvaluationResult | undefined = results.find(r => r.method === 'rule_based')
  const latestMl: EvaluationResult | undefined = results.find(r => r.method === 'ml_classifier')

  // Comparison chart data
  const compData = []
  if (latestYolo) {
    compData.push({
      method: 'YOLO',
      precision: latestYolo.precision ?? 0,
      recall: latestYolo.recall ?? 0,
      f1: latestYolo.f1_score ?? 0,
    })
  }
  if (latestRule) {
    compData.push({
      method: 'Rule-based',
      precision: latestRule.precision ?? 0,
      recall: latestRule.recall ?? 0,
      f1: latestRule.f1_score ?? 0,
    })
  }
  if (latestMl) {
    compData.push({
      method: 'ML Classifier',
      precision: latestMl.precision ?? 0,
      recall: latestMl.recall ?? 0,
      f1: latestMl.f1_score ?? 0,
    })
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Evaluation</h2>
          <p className="text-sm text-gray-400 mt-1">
            YOLO + Fall detection evaluation metrics from real runs.
          </p>
        </div>
        <button onClick={runEval} disabled={running} className="btn-primary">
          {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {running ? 'Running…' : 'Run YOLO Eval'}
        </button>
      </div>

      {msg && (
        <div className="card border-yellow-500/40 bg-yellow-500/5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <div className="text-yellow-200 text-sm">{msg}</div>
          </div>
        </div>
      )}

      {results.length === 0 ? (
        <div className="card border-yellow-500/40 bg-yellow-500/5">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
            <div>
              <div className="text-yellow-200 font-semibold">
                Model has not been evaluated yet.
              </div>
              <div className="text-yellow-200/80 text-sm mt-1">
                Train your model first, then click "Run YOLO Eval" to compute metrics on the validation set.
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Metric label="Precision" value={latestYolo?.precision} />
            <Metric label="Recall" value={latestYolo?.recall} />
            <Metric label="mAP@50" value={latestYolo?.map50} />
            <Metric label="mAP@50:95" value={latestYolo?.map50_95} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Metric label="F1-score" value={latestYolo?.f1_score} />
            <Metric label="Accuracy (fall)" value={latestRule?.accuracy} />
            <Metric label="FP (fall)" value={latestRule?.false_positive} fmt="int" />
            <Metric label="FN (fall)" value={latestRule?.false_negative} fmt="int" />
          </div>

          {compData.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-200 mb-3">Method Comparison</h3>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={compData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f4470" />
                    <XAxis dataKey="method" stroke="#5a7da8" />
                    <YAxis stroke="#5a7da8" domain={[0, 1]} />
                    <Tooltip contentStyle={{ background: '#091c30', border: '1px solid #1f4470' }} />
                    <Legend />
                    <Bar dataKey="precision" fill="#22d3ee" name="Precision" />
                    <Bar dataKey="recall" fill="#a78bfa" name="Recall" />
                    <Bar dataKey="f1" fill="#22c55e" name="F1" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </>
      )}

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-cyan-400" /> Evaluation History
        </h3>
        {results.length === 0 ? (
          <div className="text-sm text-gray-500">No evaluations recorded.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-dark-700">
                  <th className="py-2">Method</th>
                  <th className="py-2">Model</th>
                  <th className="py-2">Precision</th>
                  <th className="py-2">Recall</th>
                  <th className="py-2">mAP50</th>
                  <th className="py-2">mAP50-95</th>
                  <th className="py-2">F1</th>
                  <th className="py-2">When</th>
                </tr>
              </thead>
              <tbody>
                {results.map(r => (
                  <tr key={r.id} className="border-b border-dark-700/50 text-gray-200">
                    <td className="py-2">{r.method}</td>
                    <td className="py-2">{r.model_name}</td>
                    <td className="py-2">{r.precision !== null ? r.precision.toFixed(3) : '—'}</td>
                    <td className="py-2">{r.recall !== null ? r.recall.toFixed(3) : '—'}</td>
                    <td className="py-2">{r.map50 !== null ? r.map50.toFixed(3) : '—'}</td>
                    <td className="py-2">{r.map50_95 !== null ? r.map50_95.toFixed(3) : '—'}</td>
                    <td className="py-2">{r.f1_score !== null ? r.f1_score.toFixed(3) : '—'}</td>
                    <td className="py-2 text-xs text-gray-400">{new Date(r.timestamp).toLocaleString()}</td>
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

function Metric({ label, value, fmt }: { label: string; value: number | null | undefined; fmt?: 'int' }) {
  let display = '—'
  if (value !== null && value !== undefined) {
    if (fmt === 'int') display = String(value)
    else display = value.toFixed(3)
  }
  return (
    <div className="card">
      <div className="text-xs uppercase text-gray-400">{label}</div>
      <div className="text-2xl font-bold text-cyan-300 mt-1">{display}</div>
    </div>
  )
}