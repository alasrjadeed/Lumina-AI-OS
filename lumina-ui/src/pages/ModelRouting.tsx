import { useState, useEffect } from 'react';
import { Route, Cpu, BarChart3, RefreshCw, Zap, DollarSign, Clock, TrendingUp, CheckCircle, ArrowRight } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

const TASK_TYPES = ['chat', 'code', 'reasoning', 'creative', 'analysis', 'vision', 'embedding', 'fast'];

export default function ModelRouting() {
  const [models, setModels] = useState<Record<string, any>>({});
  const [routes, setRoutes] = useState<Record<string, any>>({});
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState('chat');
  const [suggestion, setSuggestion] = useState<any>(null);
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [m, r, u] = await Promise.all([
        fetch(`${BASE}/model-routing/models`).then(r => r.json()),
        fetch(`${BASE}/model-routing/routes`).then(r => r.json()),
        fetch(`${BASE}/model-routing/usage`).then(r => r.json()),
      ]);
      setModels(m.models || {});
      setRoutes(r.routes || {});
      setUsage(u);
    } catch {}
    setLoading(false);
  }

  async function suggest(task: string) {
    try {
      const r = await fetch(`${BASE}/model-routing/suggest?task_type=${task}`);
      const data = await r.json();
      setSuggestion(data.suggestion);
      setSelectedTask(task);
    } catch {}
  }

  async function updateRoute(taskType: string, strategy: string, models: string) {
    try {
      const params = new URLSearchParams({ strategy, models });
      const r = await fetch(`${BASE}/model-routing/routes/${taskType}?${params.toString()}`, { method: 'POST' });
      const data = await r.json();
      if (data.error) { addToast(data.error, 'error'); return; }
      addToast(`Route updated for ${taskType}`, 'success');
      await loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  function getStrategyColor(s: string) {
    const c: Record<string, string> = { manual: 'var(--text-tertiary)', cost_optimal: 'var(--color-success)', latency_optimal: 'var(--color-warning)', quality_optimal: 'var(--brand-500)', fallback_chain: 'var(--color-error)' };
    return c[s] || 'var(--text-secondary)';
  }

  function getQualityLabel(q: number) {
    return ['', 'Basic', 'Fair', 'Good', 'Great', 'Excellent'][q] || 'Unknown';
  }

  if (loading) {
    return <div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-3 border-[var(--border-primary)] border-t-[var(--brand-500)] rounded-full animate-spin" /></div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Model Routing</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Intelligent dispatch of AI requests to the optimal model</p></div>
        <button onClick={loadAll} className="btn btn-ghost p-2"><RefreshCw className="w-4 h-4" /></button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Route Tester */}
        <Card><div className="p-4 space-y-4">
          <h2 className="text-sm font-semibold flex items-center gap-2"><Zap className="w-4 h-4 text-[var(--color-warning)]" /> Route Tester</h2>
          <div className="flex items-center gap-2">
            <select className="input text-xs" value={selectedTask} onChange={e => setSelectedTask(e.target.value)}>
              {TASK_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <button onClick={() => suggest(selectedTask)} className="btn btn-primary text-xs"><Route className="w-3.5 h-3.5" /> Suggest Model</button>
          </div>
          {suggestion && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                { l: 'Model', v: suggestion.model, c: 'var(--brand-500)' },
                { l: 'Provider', v: suggestion.provider, c: 'var(--color-info)' },
                { l: 'Cost/1K', v: `$${suggestion.cost_per_1k}`, c: 'var(--color-success)' },
                { l: 'Latency', v: `${suggestion.estimated_latency_ms}ms`, c: 'var(--color-warning)' },
                { l: 'Quality', v: getQualityLabel(suggestion.quality), c: 'var(--brand-500)' },
              ].map(s => (
                <div key={s.l} className="bg-[var(--bg-tertiary)] rounded-lg p-3">
                  <p className="text-2xs text-[var(--text-tertiary)] uppercase">{s.l}</p>
                  <p className="text-sm font-bold mt-0.5" style={{ color: s.c }}>{s.v}</p>
                </div>
              ))}
            </div>
          )}
        </div></Card>

        {/* Routing Table */}
        <Card><div className="p-4 space-y-3">
          <h2 className="text-sm font-semibold">Routing Table</h2>
          <div className="space-y-2">
            {Object.entries(routes).map(([task, config]: [string, any]) => (
              <div key={task} className="flex items-center justify-between bg-[var(--bg-tertiary)] rounded-lg p-3">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold w-20">{task}</span>
                  <span className="text-2xs px-2 py-0.5 rounded-full" style={{ backgroundColor: getStrategyColor(config.strategy) + '20', color: getStrategyColor(config.strategy) }}>
                    {config.strategy.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1">
                    {(config.models || []).slice(0, 3).map((m: string) => (
                      <span key={m} className="text-2xs text-[var(--text-secondary)] bg-[var(--bg-hover)] px-1.5 py-0.5 rounded">{m}</span>
                    ))}
                    {(config.models || []).length > 3 && <span className="text-2xs text-[var(--text-tertiary)]">+{config.models.length - 3}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div></Card>

        {/* Available Models */}
        <Card><div className="p-4 space-y-3">
          <h2 className="text-sm font-semibold">Available Models</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(models).map(([name, profile]: [string, any]) => (
              <div key={name} className="bg-[var(--bg-tertiary)] rounded-lg p-3 border border-[var(--border-primary)]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <Cpu className="w-3.5 h-3.5 text-[var(--brand-500)] shrink-0" />
                    <span className="text-xs font-medium truncate">{name}</span>
                  </div>
                  <span className="text-2xs text-[var(--text-tertiary)]">{profile.provider}</span>
                </div>
                <div className="flex items-center gap-3 mt-2 text-2xs text-[var(--text-secondary)]">
                  <span className="flex items-center gap-0.5"><DollarSign className="w-2.5 h-2.5" /> ${profile.cost_per_1k}</span>
                  <span className="flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" /> {profile.latency_ms}ms</span>
                  <span className="flex items-center gap-0.5"><TrendingUp className="w-2.5 h-2.5" /> {getQualityLabel(profile.quality)}</span>
                </div>
                <div className="flex flex-wrap gap-1 mt-2">
                  {(profile.capabilities || []).map((cap: string) => (
                    <span key={cap} className="text-2xs px-1.5 py-0.5 rounded bg-[var(--bg-hover)] text-[var(--text-tertiary)]">{cap}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div></Card>

        {/* Usage Stats */}
        {usage && (
          <Card><div className="p-4 space-y-3">
            <h2 className="text-sm font-semibold">Usage Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-[var(--bg-tertiary)] rounded-xl p-4">
                <p className="text-2xs text-[var(--text-tertiary)] uppercase">Total Calls</p>
                <p className="text-2xl font-bold mt-1">{usage.total_calls || 0}</p>
              </div>
              <div className="bg-[var(--bg-tertiary)] rounded-xl p-4">
                <p className="text-2xs text-[var(--text-tertiary)] uppercase">Total Cost</p>
                <p className="text-2xl font-bold mt-1" style={{ color: 'var(--color-success)' }}>${(usage.total_cost || 0).toFixed(4)}</p>
              </div>
              <div className="bg-[var(--bg-tertiary)] rounded-xl p-4">
                <p className="text-2xs text-[var(--text-tertiary)] uppercase">Calls by Model</p>
                <div className="space-y-1 mt-2">
                  {Object.entries(usage.by_model || {}).map(([model, count]: [string, any]) => (
                    <div key={model} className="flex items-center justify-between text-xs">
                      <span className="text-[var(--text-secondary)] truncate">{model}</span>
                      <span className="font-medium">{String(count)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div></Card>
        )}
      </div>
    </div>
  );
}
