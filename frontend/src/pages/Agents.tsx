import { Bot, AlertCircle } from 'lucide-react'

export default function Agents() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">AI Agents</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {defaultAgents.map(agent => (
          <div key={agent.name} className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <div className="flex items-center gap-3 mb-3">
              <Bot className="text-cyan-400" size={24} />
              <div>
                <div className="font-semibold">{agent.name}</div>
                <div className="text-sm text-gray-400">{agent.role}</div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {agent.capabilities.map((cap: string) => (
                <span key={cap} className="px-2 py-1 text-xs bg-gray-800 rounded-md text-gray-300">
                  {cap}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

const defaultAgents = [
  { name: "CEO AI", role: "Master Orchestrator", capabilities: ["planning", "coordination", "delegation"] },
  { name: "Software Engineer AI", role: "Development", capabilities: ["coding", "debugging", "architecture"] },
  { name: "Explain AI", role: "Explanation Specialist", capabilities: ["text", "code", "document", "website", "report"] },
  { name: "Reader AI", role: "Document Reader", capabilities: ["pdf", "docx", "epub", "txt", "web pages"] },
  { name: "Business Manager AI", role: "Business Operations", capabilities: ["crm", "invoicing", "proposals"] },
  { name: "Marketing AI", role: "Marketing", capabilities: ["seo", "content", "analytics"] },
  { name: "Browser Operator AI", role: "Web Automation", capabilities: ["browsing", "data extraction", "testing"] },
  { name: "Desktop Operator AI", role: "OS Automation", capabilities: ["file management", "app control", "monitoring"] },
]
