import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Save } from 'lucide-react'

export default function Settings() {
  const [settings, setSettings] = useState<any>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetch('/api/settings/')
      .then(r => r.json())
      .then(data => { setSettings(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const save = async () => {
    setSaving(true)
    await fetch('/api/settings/', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    })
    setSaving(false)
  }

  if (loading) return <div className="text-gray-400">Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <SettingsIcon className="text-cyan-400" /> Settings
      </h1>

      <div className="max-w-2xl space-y-6">
        <Section title="General">
          <Field label="App Name" value={settings.app_name} readOnly />
          <Field label="Version" value={settings.app_version} readOnly />
          <Field label="Environment" value={settings.environment} readOnly />
        </Section>

        <Section title="AI Provider">
          <select
            className="w-full bg-gray-800 rounded-lg px-4 py-2 text-sm"
            value={settings.ai_provider || 'ollama'}
            onChange={e => setSettings({ ...settings, ai_provider: e.target.value })}
          >
            <option value="ollama">Ollama (Local)</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="openrouter">OpenRouter</option>
          </select>
          <Field label="Local AI URL" value={settings.local_ai_url} onChange={v => setSettings({ ...settings, local_ai_url: v })} />
          <Field label="Model" value={settings.local_ai_model} onChange={v => setSettings({ ...settings, local_ai_model: v })} />
        </Section>

        <Section title="Voice">
          <Toggle label="Voice Enabled" checked={settings.voice_enabled !== false} onChange={v => setSettings({ ...settings, voice_enabled: v })} />
          <Field label="Voice Speed" value={settings.voice_speed || 1.0} onChange={v => setSettings({ ...settings, voice_speed: parseFloat(v) })} />
        </Section>

        <Section title="Developer">
          <Toggle label="Auto-Index Code" checked={settings.auto_index !== false} onChange={v => setSettings({ ...settings, auto_index: v })} />
          <Field label="Max Tokens" value={settings.max_tokens || 4096} onChange={v => setSettings({ ...settings, max_tokens: parseInt(v) })} />
          <Field label="Temperature" value={settings.llm_temperature || 0.7} onChange={v => setSettings({ ...settings, llm_temperature: parseFloat(v) })} />
        </Section>

        <button
          onClick={save}
          disabled={saving}
          className="bg-cyan-600 hover:bg-cyan-500 px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          <Save size={18} /> {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
      <h2 className="text-sm font-semibold text-gray-400 mb-4">{title}</h2>
      <div className="space-y-3">{children}</div>
    </div>
  )
}

function Field({ label, value, onChange, readOnly }: { label: string; value: any; onChange?: (v: string) => void; readOnly?: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-400">{label}</span>
      {readOnly ? (
        <span className="text-sm text-gray-200">{value}</span>
      ) : (
        <input
          className="bg-gray-800 rounded-lg px-3 py-1.5 text-sm w-48 text-right"
          value={value}
          onChange={e => onChange?.(e.target.value)}
        />
      )}
    </div>
  )
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-400">{label}</span>
      <button
        onClick={() => onChange(!checked)}
        className={`w-10 h-5 rounded-full transition-colors ${checked ? 'bg-cyan-600' : 'bg-gray-700'}`}
      >
        <div className={`w-4 h-4 bg-white rounded-full transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`} />
      </button>
    </div>
  )
}
