import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Camera, Video, Database, Cpu, BarChart3,
  AlertTriangle, Settings, Activity,
} from 'lucide-react'
import clsx from 'clsx'

const items = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/realtime', icon: Camera, label: 'Realtime Detection' },
  { to: '/video', icon: Video, label: 'Video Analysis' },
  { to: '/dataset', icon: Database, label: 'Dataset' },
  { to: '/training', icon: Cpu, label: 'Training' },
  { to: '/evaluation', icon: BarChart3, label: 'Evaluation' },
  { to: '/events', icon: AlertTriangle, label: 'Fall Events' },
  { to: '/architecture', icon: Activity, label: 'AI Architecture' },
  { to: '/settings', icon: Settings, label: 'System Settings' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 bg-dark-900/80 backdrop-blur border-r border-dark-700 flex flex-col">
      <div className="px-5 py-5 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center font-bold text-dark-950">
            AI
          </div>
          <div>
            <div className="text-sm font-bold text-gray-100">Smart Home</div>
            <div className="text-xs text-cyan-400">Fall Detection</div>
          </div>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {items.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
                isActive
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-gray-300 hover:bg-dark-700 hover:text-white'
              )
            }
          >
            <Icon className="w-4 h-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="px-5 py-3 border-t border-dark-700 text-xs text-gray-500">
        v1.0.0 · YOLO + Pose + Temporal
      </div>
    </aside>
  )
}