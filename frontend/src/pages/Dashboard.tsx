import { useEffect, useState } from 'react'
import { Activity, CheckCircle, AlertCircle, Clock, Bot, Cpu } from 'lucide-react'

interface DashboardData {
  status: string
  agents_active: number
  tasks_pending: number
  tasks_completed_today: number
  memory_usage: string
  uptime: string
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)

  useEffect(() => {
    fetch('/api/dashboard/')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard icon={<Bot size={24} />} label="Active Agents" value={data?.agents_active ?? 0} color="text-cyan-400" />
        <StatCard icon={<Clock size={24} />} label="Pending Tasks" value={data?.tasks_pending ?? 0} color="text-yellow-400" />
        <StatCard icon={<CheckCircle size={24} />} label="Completed Today" value={data?.tasks_completed_today ?? 0} color="text-green-400" />
        <StatCard icon={<Cpu size={24} />} label="Memory Usage" value={data?.memory_usage ?? "0 MB"} color="text-purple-400" />
      </div>
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Activity className="text-cyan-400" size={20} />
          System Status
        </h2>
        <div className="space-y-3">
          <StatusRow label="Kernel" status={data?.status ?? "initializing"} />
          <StatusRow label="Database" status="connected" />
          <StatusRow label="Memory" status="active" />
          <StatusRow label="AI Engine" status="ready" />
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string | number; color: string }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <div className={`${color} mb-2`}>{icon}</div>
      <div className="text-2xl font-bold mb-1">{value}</div>
      <div className="text-sm text-gray-400">{label}</div>
    </div>
  )
}

function StatusRow({ label, status }: { label: string; status: string }) {
  const isOk = status === "running" || status === "connected" || status === "active" || status === "ready"
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-400">{label}</span>
      <span className={`flex items-center gap-1 ${isOk ? "text-green-400" : "text-yellow-400"}`}>
        <AlertCircle size={14} />
        {status}
      </span>
    </div>
  )
}
