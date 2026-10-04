import { useEffect, useState } from 'react'
import { AlertTriangle, Filter, Search } from 'lucide-react'
import { api } from '../services/api'
import type { FallEventRecord } from '../types/api'

export default function FallEvents() {
  const [events, setEvents] = useState<FallEventRecord[]>([])
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState<keyof FallEventRecord>('timestamp')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const refresh = async () => {
    try {
      const r = await api.events(200, sourceFilter || undefined)
      setEvents(r.events)
    } catch {/* */}
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 4000)
    return () => clearInterval(id)
  }, [sourceFilter])

  const filtered = events.filter(e => {
    if (!search) return true
    const s = search.toLowerCase()
    return (
      e.person_id.toString().includes(s) ||
      e.posture.toLowerCase().includes(s) ||
      e.source.toLowerCase().includes(s)
    )
  })

  const sorted = [...filtered].sort((a, b) => {
    const va = a[sortKey]
    const vb = b[sortKey]
    let cmp = 0
    if (va === null && vb === null) cmp = 0
    else if (va === null) cmp = 1
    else if (vb === null) cmp = -1
    else if (typeof va === 'number' && typeof vb === 'number') cmp = va - vb
    else cmp = String(va).localeCompare(String(vb))
    return sortDir === 'asc' ? cmp : -cmp
  })

  const toggleSort = (key: keyof FallEventRecord) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-100">Fall Event History</h2>
          <p className="text-sm text-gray-400 mt-1">
            All detected fall events with timestamps, confidence and alert latency.
          </p>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by person ID, posture, source..."
              className="input pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="input"
            >
              <option value="">All sources</option>
              <option value="webcam">Webcam</option>
              <option value="video">Video</option>
              <option value="image">Image</option>
            </select>
          </div>
        </div>

        {sorted.length === 0 ? (
          <div className="text-sm text-gray-500">
            No events recorded. Use the Realtime or Video Analysis pages to generate fall events.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-gray-400 border-b border-dark-700">
                  <Th onClick={() => toggleSort('timestamp')} active={sortKey === 'timestamp'} dir={sortDir}>Timestamp</Th>
                  <Th onClick={() => toggleSort('person_id')} active={sortKey === 'person_id'} dir={sortDir}>Person</Th>
                  <Th onClick={() => toggleSort('posture')} active={sortKey === 'posture'} dir={sortDir}>Posture</Th>
                  <Th onClick={() => toggleSort('confidence')} active={sortKey === 'confidence'} dir={sortDir}>Confidence</Th>
                  <Th onClick={() => toggleSort('latency')} active={sortKey === 'latency'} dir={sortDir}>Latency</Th>
                  <Th onClick={() => toggleSort('source')} active={sortKey === 'source'} dir={sortDir}>Source</Th>
                </tr>
              </thead>
              <tbody>
                {sorted.map(ev => (
                  <tr key={ev.id} className="border-b border-dark-700/50 hover:bg-dark-800/50 text-gray-200">
                    <td className="py-2 font-mono text-xs">
                      {new Date(ev.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2">
                      <span className="px-2 py-0.5 bg-red-500/15 border border-red-500/30 rounded text-xs">
                        {ev.person_id.toString().padStart(2, '0')}
                      </span>
                    </td>
                    <td className="py-2">{ev.posture.toUpperCase()}</td>
                    <td className="py-2">{(ev.confidence * 100).toFixed(0)}%</td>
                    <td className="py-2">{ev.latency !== null ? `${ev.latency.toFixed(2)}s` : '—'}</td>
                    <td className="py-2 text-gray-400">{ev.source}</td>
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

function Th({ children, onClick, active, dir }: any) {
  return (
    <th
      onClick={onClick}
      className="py-2 cursor-pointer hover:text-cyan-300 select-none"
    >
      {children}
      {active && <span className="ml-1">{dir === 'asc' ? '↑' : '↓'}</span>}
    </th>
  )
}