import { useState, useEffect } from 'react';
import { UserPlus, Plus, Trash2, Copy, Save, Bot, Settings, Cpu, Thermometer } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

export default function AgentBuilder() {
  const [blueprints, setBlueprints] = useState<any[]>([]);
  const [tools, setTools] = useState<string[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', description: '', system_prompt: '', tools: [] as string[], model: 'gpt-4o-mini', temperature: 0.7, max_tokens: 2048 });
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [b, t] = await Promise.all([
        fetch(`${BASE}/agent-blueprints`).then(r => r.json()),
        fetch(`${BASE}/agent-blueprints/tools`).then(r => r.json()),
      ]);
      setBlueprints(b.blueprints || []);
      setTools(t.tools || []);
    } catch {}
    setLoading(false);
  }

  async function createBP() {
    if (!form.name.trim()) return;
    try {
      const params = new URLSearchParams({
        name: form.name,
        description: form.description,
        system_prompt: form.system_prompt,
        tools: form.tools.join(','),
        model: form.model,
        temperature: String(form.temperature),
        max_tokens: String(form.max_tokens),
      });
      await fetch(`${BASE}/agent-blueprints?${params.toString()}`, { method: 'POST' });
      setForm({ name: '', description: '', system_prompt: '', tools: [], model: 'gpt-4o-mini', temperature: 0.7, max_tokens: 2048 });
      addToast('Blueprint created', 'success');
      await loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteBP(id: string) {
    try {
      await fetch(`${BASE}/agent-blueprints/${id}`, { method: 'DELETE' });
      addToast('Deleted', 'success');
      if (selected?.id === id) setSelected(null);
      await loadAll();
    } catch {}
  }

  async function duplicateBP(id: string) {
    try {
      await fetch(`${BASE}/agent-blueprints/${id}/duplicate`, { method: 'POST' });
      addToast('Duplicated', 'success');
      await loadAll();
    } catch {}
  }

  async function updateBP(id: string) {
    try {
      const params = new URLSearchParams({
        name: form.name,
        description: form.description,
        system_prompt: form.system_prompt,
        tools: form.tools.join(','),
        model: form.model,
        temperature: String(form.temperature),
        max_tokens: String(form.max_tokens),
      });
      await fetch(`${BASE}/agent-blueprints/${id}?${params.toString()}`, { method: 'PATCH' });
      addToast('Updated', 'success');
      setSelected(null);
      await loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  function editBP(bp: any) {
    setSelected(bp);
    setForm({
      name: bp.name,
      description: bp.description || '',
      system_prompt: bp.system_prompt || '',
      tools: bp.tools || [],
      model: bp.model || 'gpt-4o-mini',
      temperature: bp.temperature ?? 0.7,
      max_tokens: bp.max_tokens ?? 2048,
    });
  }

  function toggleTool(t: string) {
    setForm(p => ({
      ...p,
      tools: p.tools.includes(t) ? p.tools.filter(x => x !== t) : [...p.tools, t],
    }));
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Agent Builder</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Create and configure custom AI agents</p></div>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-56 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Blueprints</h3>
          <div className="space-y-1">
            {blueprints.map((bp: any) => (
              <div key={bp.id} className={`flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer ${selected?.id === bp.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}
                onClick={() => editBP(bp)}>
                <Bot className="w-3 h-3 mr-1.5 shrink-0" />
                <span className="flex-1 truncate">{bp.name}</span>
                <button onClick={e => { e.stopPropagation(); duplicateBP(bp.id); }} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)] p-0.5"><Copy className="w-2.5 h-2.5" /></button>
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl space-y-6">
            <Card><div className="p-4 space-y-4">
              <h2 className="text-sm font-semibold">{selected ? 'Edit Agent' : 'New Agent'}</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="input-group md:col-span-2"><label className="input-label">Name</label><input className="input text-xs" value={form.name} onChange={e => setForm(p => ({...p, name: e.target.value}))} placeholder="My Custom Agent" /></div>
                <div className="input-group md:col-span-2"><label className="input-label">Description</label><input className="input text-xs" value={form.description} onChange={e => setForm(p => ({...p, description: e.target.value}))} placeholder="What this agent does" /></div>
              </div>
              <div className="input-group"><label className="input-label">System Prompt</label><textarea className="input text-xs" rows={6} value={form.system_prompt} onChange={e => setForm(p => ({...p, system_prompt: e.target.value}))} placeholder="You are a helpful assistant that..." /></div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="input-group"><label className="input-label">Model</label>
                  <select className="input text-xs" value={form.model} onChange={e => setForm(p => ({...p, model: e.target.value}))}>
                    <option value="gpt-4o">GPT-4o</option>
                    <option value="gpt-4o-mini">GPT-4o Mini</option>
                    <option value="claude-3-opus">Claude 3 Opus</option>
                    <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                    <option value="llama-3-70b">Llama 3 70B</option>
                    <option value="llama-3-8b">Llama 3 8B</option>
                    <option value="gemini-pro">Gemini Pro</option>
                    <option value="deepseek-coder">DeepSeek Coder</option>
                  </select>
                </div>
                <div className="input-group"><label className="input-label">Temperature</label><input className="input text-xs" type="number" step={0.1} min={0} max={2} value={form.temperature} onChange={e => setForm(p => ({...p, temperature: +e.target.value}))} /></div>
                <div className="input-group"><label className="input-label">Max Tokens</label><input className="input text-xs" type="number" min={1} max={32000} value={form.max_tokens} onChange={e => setForm(p => ({...p, max_tokens: +e.target.value}))} /></div>
              </div>
              <div>
                <label className="input-label">Tools</label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {tools.map(t => (
                    <button key={t} onClick={() => toggleTool(t)} className={`text-2xs px-2 py-1 rounded-lg border transition-colors ${form.tools.includes(t) ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border-[var(--border-brand)]' : 'border-[var(--border-primary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'}`}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                {selected ? (
                  <>
                    <button onClick={() => updateBP(selected.id)} className="btn btn-primary text-xs"><Save className="w-3 h-3" /> Update</button>
                    <button onClick={() => { setSelected(null); setForm({ name: '', description: '', system_prompt: '', tools: [], model: 'gpt-4o-mini', temperature: 0.7, max_tokens: 2048 }); }} className="btn btn-ghost text-xs">Cancel</button>
                  </>
                ) : (
                  <button onClick={createBP} className="btn btn-primary text-xs"><Plus className="w-3 h-3" /> Create Blueprint</button>
                )}
              </div>
            </div></Card>

            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-[var(--text-secondary)]">Saved Blueprints ({blueprints.length})</h3>
              {blueprints.map((bp: any) => (
                <div key={bp.id} className="bg-[var(--bg-tertiary)] rounded-lg p-3 border border-[var(--border-primary)] hover:border-[var(--border-brand)] cursor-pointer transition-colors" onClick={() => editBP(bp)}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Bot className="w-4 h-4 text-[var(--brand-500)]" />
                        <span className="text-sm font-semibold">{bp.name}</span>
                      </div>
                      {bp.description && <p className="text-xs text-[var(--text-secondary)] mt-1">{bp.description}</p>}
                      <div className="flex items-center gap-3 mt-2 text-2xs text-[var(--text-tertiary)]">
                        <span className="flex items-center gap-1"><Cpu className="w-2.5 h-2.5" /> {bp.model}</span>
                        <span className="flex items-center gap-1"><Thermometer className="w-2.5 h-2.5" /> {bp.temperature}</span>
                        <span>{bp.tools?.length || 0} tools</span>
                      </div>
                    </div>
                    <button onClick={e => { e.stopPropagation(); deleteBP(bp.id); }} className="text-red-400 hover:text-red-300 p-1 shrink-0"><Trash2 className="w-3 h-3" /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
