import clsx from 'clsx'

interface StatCardProps {
  title: string
  value: string | number
  unit?: string
  icon?: React.ComponentType<{ className?: string }>
  trend?: 'up' | 'down' | 'neutral'
  accent?: 'cyan' | 'purple' | 'green' | 'red' | 'yellow'
  hint?: string
}

export default function StatCard({
  title, value, unit, icon: I, accent = 'cyan', hint,
}: StatCardProps) {
  const accentMap = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
    purple: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
    green: 'text-green-400 bg-green-500/10 border-green-500/30',
    red: 'text-red-400 bg-red-500/10 border-red-500/30',
    yellow: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
  }
  return (
    <div className="card flex flex-col gap-2 hover:border-cyan-500/40 transition-colors">
      <div className="flex items-start justify-between">
        <div className="text-xs uppercase tracking-wider text-gray-400">{title}</div>
        {I && (
          <div className={clsx('p-2 rounded-lg border', accentMap[accent])}>
            <I className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-1">
        <div className="text-3xl font-bold text-gray-100">{value}</div>
        {unit && <div className="text-sm text-gray-400">{unit}</div>}
      </div>
      {hint && <div className="text-xs text-gray-500">{hint}</div>}
    </div>
  )
}