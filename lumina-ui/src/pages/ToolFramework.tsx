import { useState, useEffect } from 'react';
import { Wrench, Play, RefreshCw, CheckCircle, XCircle, Clock, BarChart3 } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

export default function ToolFramework() {
  const [tools, setTools] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [args, setArgs] = useState('{}');
  const [result, setResult] = useState<any>(null);
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [t, s] = await Promise.all([
        fetch(`${BASE}/tools`).then(r => r.json()),
        fetch(`${BASE}/tools/stats`).then(r => r.json()),
      ]);
      setTools(t.tools || []);
      setStats(s);
    } catch {}
    setLoading(false);
  }

  async function execute() {
    if (!selectedTool) return;
    try {
      setResult(null);
      const params = new URLSearchParams({ args });
      const r = await fetch(`${BASE}/tools/${selectedTool}/execute?${params.toString()}`, { method: 'POST' });
      const data = await r.json();
      setResult(data);
      addToast(data.success ? 'Executed' : 'Failed', data.success ? 'success' : 'error');
      await loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Tool Framework</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Calculator, web search, JSON utils, and more</p></div>
        <button onClick={loadAll} className="btn btn-ghost p-2"><RefreshCw className="w-4 h-4" /></button>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-56 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Tools ({tools.length})</h3>
          <div className="space-y-1">
            {tools.map((t: any) => (
              <button key={t.name} onClick={() => { setSelectedTool(t.name); setResult(null); }}
                className={`flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-xs transition-colors ${selectedTool === t.name ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}>
                <Wrench className="w-3 h-3 shrink-0" />
                <div className="flex-1 text-left min-w-0">
                  <span className="truncate block">{t.name}</span>
                  <span className="text-2xs text-[var(--text-tertiary)]">{t.usage_count} calls</span>
                </div>
              </button>
            ))}
          </div>
          {stats && (
            <div className="mt-4 pt-3 border-t border-[var(--border-primary)] text-2xs text-[var(--text-tertiary)] space-y-1">
              <p>{stats.total_calls} total calls</p>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!selectedTool ? (
            <div className="text-center py-16 text-[var(--text-tertiary)]">
              <Wrench className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-sm">Select a tool to execute</p>
            </div>
          ) : (
            <div className="max-w-3xl space-y-6">
              {(() => {
                const tool = tools.find(t => t.name === selectedTool);
                return tool ? (
                  <>
                    <div>
                      <h2 className="text-lg font-semibold">{tool.name}</h2>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">{tool.description}</p>
                    </div>

                    <Card><div className="p-4 space-y-3">
                      <h3 className="text-xs font-semibold">Parameters</h3>
                      {tool.parameters?.length > 0 ? (
                        <div className="space-y-2">
                          {tool.parameters.map((p: any) => (
                            <div key={p.name} className="text-xs">
                              <span className="text-[var(--text-secondary)]">{p.name}</span>
                              <span className="text-[var(--text-tertiary)] ml-1">({p.type}{p.required ? ', required' : ''})</span>
                              <p className="text-2xs text-[var(--text-tertiary)]">{p.description}</p>
                            </div>
                          ))}
                          <textarea className="input text-xs w-full font-mono" rows={4} value={args} onChange={e => setArgs(e.target.value)} placeholder='{"expression": "2 + 2"}' />
                        </div>
                      ) : (
                        <p className="text-xs text-[var(--text-tertiary)]">No parameters required</p>
                      )}
                      <button onClick={execute} className="btn btn-primary text-xs"><Play className="w-3 h-3" /> Execute</button>
                    </div></Card>

                    {result && (
                      <Card><div className="p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-semibold flex items-center gap-1.5">
                            {result.success ? <CheckCircle className="w-3.5 h-3.5 text-[var(--color-success)]" /> : <XCircle className="w-3.5 h-3.5 text-[var(--color-error)]" />}
                            {result.success ? 'Success' : 'Error'}
                          </h3>
                          <span className="text-2xs text-[var(--text-tertiary)] flex items-center gap-1"><Clock className="w-2.5 h-2.5" /> {result.elapsed_ms}ms</span>
                        </div>
                        <pre className="bg-[var(--bg-hover)] rounded-lg p-3 text-xs overflow-auto max-h-96">
                          {JSON.stringify(result.success ? result.result : result.error, null, 2)}
                        </pre>
                      </div></Card>
                    )}
                  </>
                ) : null;
              })()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
