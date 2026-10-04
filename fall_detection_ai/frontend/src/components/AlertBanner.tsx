import { useEffect, useState } from 'react'
import { AlertTriangle, X } from 'lucide-react'
import { api } from '../services/api'
import type { FallEventRecord } from '../types/api'

export default function AlertBanner() {
  const [latest, setLatest] = useState<FallEventRecord | null>(null)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    let lastId = -1
    const fetchEvents = async () => {
      try {
        const res = await api.events(5)
        if (res.events.length > 0 && res.events[0].id !== lastId) {
          lastId = res.events[0].id
          if (!dismissed || Date.now() - new Date(res.events[0].timestamp).getTime() > 60_000) {
            setLatest(res.events[0])
            setDismissed(false)
          }
        }
      } catch (e) {
        // silent
      }
    }
    fetchEvents()
    const id = setInterval(fetchEvents, 3000)
    return () => clearInterval(id)
  }, [dismissed])

  if (!latest) return null

  const secondsAgo = Math.max(0, Math.floor((Date.now() - new Date(latest.timestamp).getTime()) / 1000))
  if (secondsAgo > 60) return null

  return (
    <div className="fixed top-16 right-4 z-50 alert-pulse">
      <div className="bg-red-500/15 backdrop-blur border-2 border-red-500 rounded-xl p-4 glow-red max-w-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="text-red-300 font-bold text-lg">FALL DETECTED</div>
            <div className="text-sm text-red-200/80 mt-1">
              Person #{String(latest.person_id).padStart(2, '0')} · {latest.posture.toUpperCase()}
            </div>
            <div className="text-xs text-red-200/60 mt-2 space-y-0.5">
              <div>Confidence: {(latest.confidence * 100).toFixed(0)}%</div>
              {latest.latency !== null && (
                <div>Alert latency: {latest.latency.toFixed(2)}s</div>
              )}
              <div>Source: {latest.source}</div>
              <div>{secondsAgo}s ago</div>
            </div>
          </div>
          <button
            onClick={() => setDismissed(true)}
            className="text-red-300/60 hover:text-red-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}