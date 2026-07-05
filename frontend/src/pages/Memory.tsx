import { useEffect, useState } from 'react'
import { Database, FolderOpen, Plus } from 'lucide-react'

export default function Memory() {
  const [projects, setProjects] = useState<string[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [projectData, setProjectData] = useState<any>(null)

  useEffect(() => {
    fetch('/api/memory/')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          setProjects(data.map((e: any) => e.key?.replace('project:', '') || '').filter(Boolean))
        }
      })
      .catch(() => {})
  }, [])

  const openProject = async (name: string) => {
    setSelected(name)
    try {
      const res = await fetch(`/api/memory/${encodeURIComponent(`project:${name}`)}`)
      const data = await res.json()
      setProjectData(data)
    } catch { setProjectData(null) }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Database className="text-cyan-400" /> Work Memory
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h2 className="text-sm font-semibold text-gray-400 mb-3">Projects</h2>
          {projects.length === 0 ? (
            <div className="text-gray-500 text-sm text-center py-8">
              <FolderOpen className="mx-auto mb-2" size={24} />
              No projects stored yet
            </div>
          ) : (
            <div className="space-y-1">
              {projects.map(p => (
                <button
                  key={p}
                  onClick={() => openProject(p)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    selected === p ? 'bg-cyan-600/20 text-cyan-300' : 'hover:bg-gray-800 text-gray-300'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2 bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h2 className="text-sm font-semibold text-gray-400 mb-3">
            {selected ? selected : 'Project Context'}
          </h2>
          {projectData ? (
            <pre className="text-sm text-gray-300 whitespace-pre-wrap">{JSON.stringify(projectData, null, 2)}</pre>
          ) : (
            <div className="text-gray-500 text-sm text-center py-8">
              <Plus className="mx-auto mb-2" size={24} />
              {selected ? 'Loading...' : 'Select a project or create one'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
