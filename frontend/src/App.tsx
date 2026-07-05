import { Routes, Route, Link } from 'react-router-dom'
import { Cpu, LayoutDashboard, ListChecks, Bot, Settings, Sparkles, Book, Database } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Agents from './pages/Agents'
import Memory from './pages/Memory'
import Explain from './pages/Explain'
import Reader from './pages/Reader'
import SettingsPage from './pages/Settings'

function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex">
      <nav className="w-64 bg-gray-900 border-r border-gray-800 p-4 flex flex-col gap-2">
        <div className="flex items-center gap-2 mb-8 px-3">
          <Cpu className="w-8 h-8 text-cyan-400" />
          <span className="text-xl font-bold">Lumina AI</span>
        </div>
        <NavItem to="/" icon={<LayoutDashboard size={18} />} label="Dashboard" />
        <NavItem to="/tasks" icon={<ListChecks size={18} />} label="Tasks" />
        <NavItem to="/agents" icon={<Bot size={18} />} label="Agents" />
        <NavItem to="/explain" icon={<Sparkles size={18} />} label="Explain" />
        <NavItem to="/reader" icon={<Book size={18} />} label="Reader" />
        <NavItem to="/memory" icon={<Database size={18} />} label="Memory" />
        <div className="mt-auto">
          <NavItem to="/settings" icon={<Settings size={18} />} label="Settings" />
        </div>
      </nav>
      <main className="flex-1 p-8 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/explain" element={<Explain />} />
          <Route path="/reader" element={<Reader />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  )
}

function NavItem({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors text-gray-400 hover:text-gray-100"
    >
      {icon}
      <span>{label}</span>
    </Link>
  )
}

export default App
