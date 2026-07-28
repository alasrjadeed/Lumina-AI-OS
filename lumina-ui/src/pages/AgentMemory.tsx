import { useState, useEffect } from 'react';
import { Brain, Plus, Trash2, RefreshCw, Database, Clock } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

export default function AgentMemory() {
  const [agents, setAgents] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [entries, setEntries] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [key, setKey] = useState('');
  const [value, setValue] = useState('');
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [a, s] = await Promise.all([
        fetch(`${BASE}/agent-memory`).then(r => r.json()),
        fetch(`${BASE}/agent-memory/stats/all`).then(r => r.json()),
      ]);
      setAgents(a.agents || []);
      setStats(s);
    } catch {}
    setLoading(false);
  }

  async function loadAgent(id: string) {
    try {
      const r = await fetch(`${BASE}/agent-memory/${id}`);
      const data = await r.json();
      setEntries(data.entries || []);
      setSelected(id);
    } catch {}
  }

  async function addMemory() {
    if (!selected || !key.trim()) return;
    try {
      const params = new URLSearchParams({ key, value });
      await fetch(`${BASE}/agent-memory/${selected}?${params.toString()}`, { method: 'POST' });
      setKey(''); setValue('');
      addToast('Memory stored', 'success');
      await loadAgent(selected);
      await loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteEntry(entryId: string) {
    if (!selected) return;
    try {
      await fetch(`${BASE}/agent-memory/${selected}/${entryId}`, { method: 'DELETE' });
      await loadAgent(selected);
    } catch {}
  }

  async function clearAgent(id: string) {
    try {
      await fetch(`${BASE}/agent-memory/${id}/clear`, { method: 'POST' });
      addToast('Cleared', 'success');
      await loadAgent(id);
      await loadAll();
    } catch {}
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Agent Memory</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Persistent memory store for AI agents</p></div>
        <button onClick={loadAll} className="btn btn-ghost p-2"><RefreshCw className="w-4 h-4" /></button>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-56 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Agents</h3>
          <div className="space-y-1">
            {agents.map(id => (
              <div key={id} className={`flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer ${selected === id ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}
                onClick={() => loadAgent(id)}>
                <Brain className="w-3 h-3 mr-1.5 shrink-0" />
                <span className="flex-1 truncate">{id}</span>
                <button onClick={e => { e.stopPropagation(); clearAgent(id); }} className="text-red-400 hover:text-red-300 p-0.5"><Trash2 className="w-2.5 h-2.5" /></button>
              </div>
            ))}
          </div>
          {stats && (
            <div className="mt-4 pt-3 border-t border-[var(--border-primary)] text-2xs text-[var(--text-tertiary)] space-y-1">
              <p>{stats.total_agents} agents</p>
              <p>{stats.total_entries} entries</p>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!selected ? (
            <div className="text-center py-16 text-[var(--text-tertiary)]">
              <Database className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-sm">Select an agent to view memory</p>
            </div>
          ) : (
            <div className="max-w-3xl space-y-4">
              <Card><div className="p-4 space-y-3">
                <h2 className="text-sm font-semibold">Store Memory</h2>
                <div className="flex gap-2">
                  <input className="input text-xs flex-1 max-w-[200px]" value={key} onChange={e => setKey(e.target.value)} placeholder="Key" />
                  <input className="input text-xs flex-1" value={value} onChange={e => setValue(e.target.value)} onKeyDown={e => e.key === 'Enter' && addMemory()} placeholder="Value" />
                  <button onClick={addMemory} className="btn btn-primary text-xs"><Plus className="w-3 h-3" /> Store</button>
                </div>
              </div></Card>

              <div className="space-y-2">
                <h3 className="text-xs font-semibold text-[var(--text-secondary)]">{entries.length} entries for {selected}</h3>
                {entries.map((e: any) => (
                  <div key={e.id} className="bg-[var(--bg-tertiary)] rounded-lg p-3 border border-[var(--border-primary)]">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-[var(--brand-500)]">{e.key}</span>
                          <span className="text-2xs text-[var(--text-tertiary)]">{e.id}</span>
                        </div>
                        <p className="text-xs text-[var(--text-secondary)] mt-1 break-words">{String(e.value)}</p>
                        <div className="flex items-center gap-2 mt-2 text-2xs text-[var(--text-tertiary)]">
                          <Clock className="w-2.5 h-2.5" />
                          <span>{new Date(e.timestamp * 1000).toLocaleString()}</span>
                          {e.ttl && <span>TTL: {e.ttl}s</span>}
                        </div>
                      </div>
                      <button onClick={() => deleteEntry(e.id)} className="text-red-400 hover:text-red-300 p-1 shrink-0"><Trash2 className="w-3 h-3" /></button>
                    </div>
                  </div>
                ))}
                {entries.length === 0 && <p className="text-xs text-[var(--text-tertiary)] text-center py-8">No memory entries</p>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
