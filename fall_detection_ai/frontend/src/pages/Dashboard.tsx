import { useEffect, useState } from 'react'
import {
  Activity, Target, AlertTriangle, Gauge, Clock, Cpu,
  TrendingUp, Database,
} from 'lucide-react'
import { api } from '../services/api'
import StatCard from '../components/StatCard'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar,
} from 'recharts'
import type { EngineStats, FallEventRecord } from '../types/api'

export default function Dashboard() {
  const [stats, setStats] = useState<EngineStats | null>(null)
  const [events, setEvents] = useState<FallEventRecord[]>([])
  const [latencyHistory, setLatencyHistory] = useState<{ t: string; latency: number }[]>([])
  const [modelLoaded, setModelLoaded] = useState<boolean | null>(null)

  useEffect(() => {
    const refresh = async () => {
      try {
        const [s, e, info] = await Promise.all([
          api.metrics(),
          api.events(50),
          api.modelInfo(),
        ])
        setStats(s)
        setEvents(e.events)
        setModelLoaded(info.model_loaded)
        const lh = e.events
          .filter(ev => ev.latency !== null)
          .map(ev => ({ t: ev.timestamp, latency: ev.latency as number }))
          .reverse()
        setLatencyHistory(lh)
      } catch (err) {
        console.error(err)
      }
    }
    refresh()
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [])

  if (!stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    )
  }

  const postureCounts = events.reduce((acc: Record<string, number>, ev) => {
    acc[ev.posture] = (acc[ev.posture] || 0) + 1
    return acc
  }, {})

  const postureData = Object.entries(postureCounts).map(([name, value]) => ({ name, value }))

  const sourceCounts = events.reduce((acc: Record<string, number>, ev) => {
    acc[ev.source] = (acc[ev.source] || 0) + 1
    return acc
  }, {})
  const sourceData = Object.entries(sourceCounts).map(([name, value]) => ({ name, value }))

  const avgLat = stats.avg_alert_latency
  const minLat = stats.min_alert_latency
  const maxLat = stats.max_alert_latency

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">System Overview</h2>
        <p className="text-sm text-gray-400 mt-1">
          Real-time metrics from the AI pipeline. All values are computed from live inference.
        </p>
      </div>

      {modelLoaded === false && (
        <div className="card border-yellow-500/40 bg-yellow-500/5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            <div className="text-yellow-200 text-sm">
              Model is loading or unavailable. If it persists, check if YOLO weights exist.
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Detections"
          value={stats.total_detections}
          icon={Target}
          accent="cyan"
          hint="Cumulative across all frames processed"
        />
        <StatCard
          title="Total Fall Events"
          value={stats.total_fall_events}
          icon={AlertTriangle}
          accent="red"
          hint="Confirmed fall events"
        />
        <StatCard
          title="False Alarms"
          value={stats.false_alarms}
          icon={AlertTriangle}
          accent="yellow"
        />
        <StatCard
          title="Avg Confidence"
          value="—"
          icon={Activity}
          accent="green"
          hint="Computed from detection events"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Average Alert Latency"
          value={avgLat !== null ? avgLat.toFixed(2) : '—'}
          unit="s"
          icon={Clock}
          accent="purple"
          hint="Time from fall occurrence to alert"
        />
        <StatCard
          title="Min Latency"
          value={minLat !== null ? minLat.toFixed(2) : '—'}
          unit="s"
          icon={Clock}
          accent="green"
        />
        <StatCard
          title="Max Latency"
          value={maxLat !== null ? maxLat.toFixed(2) : '—'}
          unit="s"
          icon={Clock}
          accent="yellow"
        />
        <StatCard
          title="FPS"
          value={stats.fps.toFixed(1)}
          icon={Gauge}
          accent="cyan"
          hint={`Inference: ${stats.avg_inference_ms.toFixed(0)} ms`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200">Alert Latency Over Time</h3>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="h-64">
            {latencyHistory.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                No fall events yet. Latency will appear here when alerts fire.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={latencyHistory.map((p, i) => ({ i, latency: p.latency }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f4470" />
                  <XAxis dataKey="i" stroke="#5a7da8" />
                  <YAxis stroke="#5a7da8" />
                  <Tooltip
                    contentStyle={{ background: '#091c30', border: '1px solid #1f4470' }}
                    labelStyle={{ color: '#8aa5c5' }}
                  />
                  <Line type="monotone" dataKey="latency" stroke="#22d3ee" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-200">Events by Posture</h3>
            <Database className="w-4 h-4 text-purple-400" />
          </div>
          <div className="h-64">
            {postureData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                No events yet.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={postureData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f4470" />
                  <XAxis dataKey="name" stroke="#5a7da8" />
                  <YAxis stroke="#5a7da8" />
                  <Tooltip contentStyle={{ background: '#091c30', border: '1px solid #1f4470' }} />
                  <Bar dataKey="value" fill="#a78bfa" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">Recent Fall Events</h3>
          {events.length === 0 ? (
            <div className="text-sm text-gray-500">
              No events recorded yet. Start a webcam session or upload a video.
            </div>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {events.slice(0, 10).map(ev => (
                <div key={ev.id} className="flex items-center justify-between p-3 bg-dark-800/60 rounded-lg border border-dark-600">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-red-500/15 border border-red-500/40 flex items-center justify-center text-red-300 font-bold text-sm">
                      #{ev.person_id.toString().padStart(2, '0')}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-100">{ev.posture.toUpperCase()}</div>
                      <div className="text-xs text-gray-400">
                        {new Date(ev.timestamp).toLocaleString()} · {ev.source}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-semibold text-cyan-400">
                      {(ev.confidence * 100).toFixed(0)}%
                    </div>
                    {ev.latency !== null && (
                      <div className="text-xs text-gray-400">
                        Latency: {ev.latency.toFixed(2)}s
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3 className="text-sm font-semibold text-gray-200 mb-3">Events by Source</h3>
          <div className="h-64">
            {sourceData.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-500 text-sm">
                No data.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f4470" />
                  <XAxis dataKey="name" stroke="#5a7da8" />
                  <YAxis stroke="#5a7da8" />
                  <Tooltip contentStyle={{ background: '#091c30', border: '1px solid #1f4470' }} />
                  <Bar dataKey="value" fill="#22d3ee" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="card border-cyan-500/30 bg-cyan-500/5">
        <div className="flex items-start gap-3">
          <Cpu className="w-5 h-5 text-cyan-400 mt-0.5" />
          <div className="text-sm text-cyan-100">
            <div className="font-semibold mb-1">Method: {stats.method}</div>
            <div className="text-cyan-200/80">
              Pipeline: YOLO detect → ByteTrack → Pose estimation → Feature extraction →
              Posture classification → Temporal fall analysis → Alert.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}