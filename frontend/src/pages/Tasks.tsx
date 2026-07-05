import { AlertCircle } from 'lucide-react'

export default function Tasks() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Tasks</h1>
      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 text-center text-gray-400">
        <AlertCircle className="mx-auto mb-2" size={24} />
        <p>No tasks yet. Tell Lumina what to do.</p>
      </div>
    </div>
  )
}
