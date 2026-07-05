import { useState } from 'react'
import { Sparkles, Code, FileText, Globe, BarChart, BookOpen } from 'lucide-react'

type ExplainTab = 'text' | 'code' | 'document' | 'website' | 'report'

export default function Explain() {
  const [tab, setTab] = useState<ExplainTab>('text')
  const [topic, setTopic] = useState('')
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('')
  const [level, setLevel] = useState('intermediate')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  const tabs = [
    { id: 'text' as ExplainTab, label: 'Text', icon: <BookOpen size={16} /> },
    { id: 'code' as ExplainTab, label: 'Code', icon: <Code size={16} /> },
    { id: 'document' as ExplainTab, label: 'Document', icon: <FileText size={16} /> },
    { id: 'website' as ExplainTab, label: 'Website', icon: <Globe size={16} /> },
    { id: 'report' as ExplainTab, label: 'Report', icon: <BarChart size={16} /> },
  ]

  const explain = async () => {
    setLoading(true)
    setResult('')
    try {
      let endpoint = '/api/explain/text'
      let body: any = { level }

      if (tab === 'text') { endpoint = '/api/explain/text'; body.topic = topic }
      else if (tab === 'code') { endpoint = '/api/explain/code'; body.code = code; body.language = language }
      else if (tab === 'document') { endpoint = '/api/explain/document'; body.content = topic; body.filename = 'document' }
      else if (tab === 'website') { endpoint = '/api/explain/website'; body.url = topic; body.page_content = topic }
      else if (tab === 'report') { endpoint = '/api/explain/report'; body.report_type = 'general'; body.report_data = topic }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      setResult(data.explanation || data.content || JSON.stringify(data))
    } catch (e: any) {
      setResult(`Error: ${e.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Sparkles className="text-cyan-400" /> Explain Mode
      </h1>

      <div className="flex gap-2 mb-6">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1 px-4 py-2 rounded-lg text-sm transition-colors ${
              tab === t.id ? 'bg-cyan-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 mb-6">
        <div className="flex gap-2 mb-4">
          {['beginner', 'intermediate', 'expert'].map(l => (
            <button
              key={l}
              onClick={() => setLevel(l)}
              className={`px-3 py-1 text-xs rounded-full ${
                level === l ? 'bg-cyan-600 text-white' : 'bg-gray-800 text-gray-400'
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        {tab === 'code' ? (
          <>
            <input
              type="text"
              placeholder="Language (e.g. Python)"
              className="w-full bg-gray-800 rounded-lg px-4 py-2 mb-3 text-sm"
              value={language}
              onChange={e => setLanguage(e.target.value)}
            />
            <textarea
              placeholder="Paste your code here..."
              className="w-full bg-gray-800 rounded-lg px-4 py-3 min-h-[200px] font-mono text-sm"
              value={code}
              onChange={e => setCode(e.target.value)}
            />
          </>
        ) : (
          <textarea
            placeholder={tab === 'text' ? 'What do you want explained?' : 'Enter content...'}
            className="w-full bg-gray-800 rounded-lg px-4 py-3 min-h-[200px] text-sm"
            value={topic}
            onChange={e => setTopic(e.target.value)}
          />
        )}

        <button
          onClick={explain}
          disabled={loading}
          className="mt-4 bg-cyan-600 hover:bg-cyan-500 px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {loading ? 'Explaining...' : 'Explain'}
        </button>
      </div>

      {result && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h3 className="text-sm font-semibold text-gray-400 mb-3">Explanation</h3>
          <div className="text-gray-200 whitespace-pre-wrap text-sm leading-relaxed">{result}</div>
        </div>
      )}
    </div>
  )
}
