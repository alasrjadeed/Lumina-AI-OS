import { useState } from 'react'
import { Book, Pause, Play, FastForward, Rewind, FileText } from 'lucide-react'

export default function Reader() {
  const [content, setContent] = useState('')
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [inputType, setInputType] = useState<'text' | 'file'>('text')

  const readContent = async () => {
    setLoading(true)
    try {
      const body = inputType === 'text' ? { text: content } : { path: content }
      const res = await fetch('/api/reader/read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      setResult(data)
    } catch (e: any) {
      setResult({ error: e.message })
    } finally {
      setLoading(false)
    }
  }

  const sendCommand = async (command: string) => {
    const res = await fetch('/api/reader/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command }),
    })
    const data = await res.json()
    setResult((prev: any) => ({ ...prev, ...data }))
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <Book className="text-cyan-400" /> Reading Mode
      </h1>

      <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 mb-6">
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setInputType('text')}
            className={`px-4 py-2 rounded-lg text-sm ${inputType === 'text' ? 'bg-cyan-600' : 'bg-gray-800'}`}
          >
            <FileText size={14} className="inline mr-1" /> Text
          </button>
          <button
            onClick={() => setInputType('file')}
            className={`px-4 py-2 rounded-lg text-sm ${inputType === 'file' ? 'bg-cyan-600' : 'bg-gray-800'}`}
          >
            File Path
          </button>
        </div>

        <textarea
          placeholder={inputType === 'text' ? 'Type or paste content to read...' : '/path/to/document.pdf'}
          className="w-full bg-gray-800 rounded-lg px-4 py-3 min-h-[150px] text-sm"
          value={content}
          onChange={e => setContent(e.target.value)}
        />

        <button
          onClick={readContent}
          disabled={loading || !content}
          className="mt-4 bg-cyan-600 hover:bg-cyan-500 px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Read'}
        </button>
      </div>

      {result && !result.error && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-center gap-4 mb-4">
            <button onClick={() => sendCommand('rewind')} className="p-2 hover:bg-gray-800 rounded-lg">
              <Rewind size={20} />
            </button>
            <button onClick={() => sendCommand('pause')} className="p-2 hover:bg-gray-800 rounded-lg">
              <Pause size={20} />
            </button>
            <button onClick={() => sendCommand('continue')} className="p-2 hover:bg-gray-800 rounded-lg">
              <Play size={20} />
            </button>
            <button onClick={() => sendCommand('faster')} className="p-2 hover:bg-gray-800 rounded-lg">
              <FastForward size={20} />
            </button>
            <button onClick={() => sendCommand('slower')} className="p-2 hover:bg-gray-800 rounded-lg">
              <Rewind size={20} className="transform rotate-180" />
            </button>
          </div>
          <div className="text-sm text-gray-400 text-center">
            {result.status} {result.speed ? `| Speed: ${result.speed}x` : ''}
          </div>
        </div>
      )}

      {result?.error && (
        <div className="bg-red-900/30 rounded-xl p-4 border border-red-800 text-red-300 text-sm">{result.error}</div>
      )}
    </div>
  )
}
