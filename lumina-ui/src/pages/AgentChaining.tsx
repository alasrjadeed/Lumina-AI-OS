import { useState, useEffect } from 'react';
import { GitBranch, Plus, Trash2, Play, ArrowRight, Bot, FileText, RefreshCw } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

export default function AgentChaining() {
  const [chains, setChains] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [agent, setAgent] = useState('');
  const [prompt, setPrompt] = useState('');
  const [depends, setDepends] = useState('');
  const { addToast } = useToast();

  useEffect(() => { loadChains(); }, []);

  async function loadChains() {
    setLoading(true);
    try {
      const r = await fetch(`${BASE}/chains`);
      const data = await r.json();
      setChains(data.chains || []);
    } catch {}
    setLoading(false);
  }

  async function loadChain(id: string) {
    try {
      const r = await fetch(`${BASE}/chains/${id}`);
      const data = await r.json();
      setSelected(data.chain);
    } catch {}
  }

  async function createChain() {
    if (!name.trim()) return;
    try {
      const params = new URLSearchParams({ name, description: desc });
      await fetch(`${BASE}/chains?${params.toString()}`, { method: 'POST' });
      setName(''); setDesc('');
      addToast('Chain created', 'success');
      await loadChains();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteChain(id: string) {
    try {
      await fetch(`${BASE}/chains/${id}`, { method: 'DELETE' });
      addToast('Deleted', 'success');
      if (selected?.id === id) setSelected(null);
      await loadChains();
    } catch {}
  }

  async function addStep() {
    if (!selected || !agent.trim() || !prompt.trim()) return;
    try {
      const params = new URLSearchParams({ agent, prompt });
      if (depends) params.set('depends_on', depends);
      await fetch(`${BASE}/chains/${selected.id}/steps?${params.toString()}`, { method: 'POST' });
      setAgent(''); setPrompt(''); setDepends('');
      addToast('Step added', 'success');
      await loadChain(selected.id);
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Agent Chaining</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Multi-step reasoning pipelines with dependent agent calls</p></div>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-56 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          <div className="space-y-3">
            <Card><div className="p-3 space-y-2">
              <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase">New</h3>
              <input className="input text-xs" value={name} onChange={e => setName(e.target.value)} placeholder="Chain name" />
              <input className="input text-xs" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description" />
              <button onClick={createChain} className="btn btn-primary text-xs w-full"><Plus className="w-3 h-3" /> Create</button>
            </div></Card>
            <div>
              <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Chains</h3>
              {chains.map(c => (
                <div key={c.id} className={`flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer ${selected?.id === c.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}
                  onClick={() => loadChain(c.id)}>
                  <GitBranch className="w-3 h-3 mr-1.5 shrink-0" />
                  <span className="flex-1 truncate">{c.name}</span>
                  <span className="text-2xs text-[var(--text-tertiary)]">{c.step_count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!selected ? (
            <div className="text-center py-16 text-[var(--text-tertiary)]">
              <GitBranch className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-sm">Select or create a chain</p>
            </div>
          ) : (
            <div className="max-w-3xl space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-lg font-semibold">{selected.name}</h2>
                  {selected.description && <p className="text-xs text-[var(--text-secondary)] mt-1">{selected.description}</p>}
                  <p className="text-2xs text-[var(--text-tertiary)] mt-1">{selected.step_count} steps</p>
                </div>
                <button onClick={() => deleteChain(selected.id)} className="btn btn-ghost text-xs text-red-400"><Trash2 className="w-3 h-3" /> Delete</button>
              </div>

              <Card><div className="p-4 space-y-3">
                <h3 className="text-xs font-semibold">Add Step</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                  <input className="input text-xs" value={agent} onChange={e => setAgent(e.target.value)} placeholder="Agent name" />
                  <input className="input text-xs" value={depends} onChange={e => setDepends(e.target.value)} placeholder="Depends on (step IDs, comma)" />
                  <button onClick={addStep} className="btn btn-primary text-xs"><Plus className="w-3 h-3" /> Add Step</button>
                </div>
                <textarea className="input text-xs w-full" rows={2} value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Prompt for this agent..." />
              </div></Card>

              <div className="space-y-3">
                {(selected.steps || []).map((step: any, i: number) => (
                  <div key={step.id} className="relative">
                    {i > 0 && <div className="absolute -top-3 left-5 w-px h-3 bg-[var(--border-brand)]" />}
                    <div className="bg-[var(--bg-tertiary)] rounded-lg p-3 border border-[var(--border-primary)] ml-5">
                      <div className="absolute -left-4 top-3 w-3 h-3 rounded-full bg-[var(--brand-500)] border-2 border-[var(--bg-primary)]" />
                      <div className="flex items-start gap-3">
                        <Bot className="w-4 h-4 text-[var(--brand-500)] mt-0.5 shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold">{step.agent}</span>
                            <span className="text-2xs text-[var(--text-tertiary)]">{step.id}</span>
                          </div>
                          <p className="text-xs text-[var(--text-secondary)] mt-1">{step.prompt}</p>
                          {step.depends_on?.length > 0 && (
                            <p className="text-2xs text-[var(--color-warning)] mt-1">Depends on: {step.depends_on.join(', ')}</p>
                          )}
                          {step.output && (
                            <div className="mt-2 bg-[var(--bg-hover)] rounded p-2">
                              <p className="text-2xs text-[var(--text-tertiary)] mb-1">Output:</p>
                              <p className="text-xs text-[var(--text-secondary)]">{step.output}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
