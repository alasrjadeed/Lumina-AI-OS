import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Activity, Clock, Download, Target, Eye, Zap, RefreshCw, Plus } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
async function get<T>(path: string): Promise<T> { const r = await fetch(`${BASE}${path}`); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function post<T>(path: string, body?: any): Promise<T> { const r = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); if (!r.ok) throw new Error(await r.text()); return r.json(); }

function StatCard({ label, value, icon: Icon, color = 'brand' }: { label: string; value: string | number; icon?: any; color?: string }) {
  const colors: Record<string, string> = { brand: 'var(--brand-500)', green: 'var(--color-success)', amber: 'var(--color-warning)', red: 'var(--color-error)', blue: 'var(--color-info)' };
  return <div className="bg-[var(--bg-tertiary)] rounded-xl p-4"><div className="flex items-center justify-between"><p className="text-2xs text-[var(--text-tertiary)] uppercase tracking-wider">{label}</p>{Icon && <Icon className="w-4 h-4" style={{ color: colors[color] }} />}</div><p className="text-2xl font-bold mt-1" style={{ color: colors[color] }}>{value}</p></div>;
}

function Skeleton({ h = 'h-8' }: { h?: string }) { return <div className={`skeleton ${h} w-full`} />; }

export default function AnalyticsDashboard() {
  const [tab, setTab] = useState<'dashboard' | 'metrics' | 'trends' | 'report'>('dashboard');
  const [dashboard, setDashboard] = useState<any>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [trackForm, setTrackForm] = useState({ name: '', value: 0, unit: '', category: 'general', tags: '' });
  const [metricFilters, setMetricFilters] = useState({ name: '', category: '', limit: 50 });
  const [trendName, setTrendName] = useState('');
  const [trendData, setTrendData] = useState<any>(null);
  const [reportData, setReportData] = useState<any>(null);
  const { addToast } = useToast();

  useEffect(() => { loadTab(); }, [tab]);

  async function loadTab() {
    setLoading(true);
    try {
      if (tab === 'dashboard') setDashboard(await get('/analytics/dashboard'));
      if (tab === 'metrics') loadMetrics();
      if (tab === 'report') { const r: any = await get('/analytics/report'); setReportData(r); }
    } catch (e: any) { /* silent */ }
    setLoading(false);
  }

  async function loadMetrics() {
    const params = new URLSearchParams();
    if (metricFilters.name) params.set('name', metricFilters.name);
    if (metricFilters.category) params.set('category', metricFilters.category);
    params.set('limit', String(metricFilters.limit));
    try { const r: any = await get(`/analytics/metrics?${params}`); setMetrics(r.metrics || []); } catch (e: any) { /* silent */ }
  }

  async function handleTrack() {
    const tags: Record<string, string> = {};
    trackForm.tags.split(',').forEach(t => { const [k, v] = t.split('=').map(x => x.trim()); if (k && v) tags[k] = v; });
    try { await post('/analytics/track', { ...trackForm, tags: Object.keys(tags).length ? tags : null }); addToast('Metric tracked', 'success'); loadMetrics(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function loadTrends() {
    if (!trendName) return;
    try { setTrendData(await get(`/analytics/trends/${encodeURIComponent(trendName)}`)); } catch (e: any) { addToast(e.message, 'error'); }
  }

  const tabs = [
    { id: 'dashboard' as const, label: 'Dashboard', icon: BarChart3 },
    { id: 'metrics' as const, label: 'Metrics', icon: Activity },
    { id: 'trends' as const, label: 'Trends', icon: TrendingUp },
    { id: 'report' as const, label: 'Report', icon: Download },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Analytics Dashboard</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Cross-module metrics, trends, and forecasting</p></div>
      </div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {/* DASHBOARD TAB */}
        {tab === 'dashboard' && (
          <div className="space-y-6">
            {loading ? <div className="space-y-4"><Skeleton h="h-24" /><Skeleton h="h-48" /></div> : dashboard ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard label="Total Metrics" value={dashboard.total_metrics ?? dashboard.metrics ?? 0} icon={Activity} color="brand" />
                  <StatCard label="Categories" value={dashboard.categories ?? 0} icon={Target} color="blue" />
                  <StatCard label="Data Points" value={dashboard.data_points ?? 0} icon={Zap} color="green" />
                  <StatCard label="Active Tracking" value={dashboard.active ?? 'On'} icon={Eye} color="amber" />
                </div>
                <Card><div className="text-center py-8">
                  <p className="text-sm text-[var(--text-secondary)]">Dashboard data</p>
                  <pre className="text-xs text-[var(--text-tertiary)] mt-2 overflow-auto max-h-96 text-left">{JSON.stringify(dashboard, null, 2)}</pre>
                </div></Card>
              </>
            ) : <div className="text-center py-12 text-[var(--text-tertiary)]"><BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No dashboard data yet</p></div>}
          </div>
        )}

        {/* METRICS TAB */}
        {tab === 'metrics' && (
          <div className="space-y-6">
            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">Track Metric</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="input-group"><label className="input-label">Name</label><input className="input" value={trackForm.name} onChange={e => setTrackForm(p => ({ ...p, name: e.target.value }))} placeholder="api_calls" /></div>
                <div className="input-group"><label className="input-label">Value</label><input className="input" type="number" value={trackForm.value} onChange={e => setTrackForm(p => ({ ...p, value: +e.target.value }))} /></div>
                <div className="input-group"><label className="input-label">Unit</label><input className="input" value={trackForm.unit} onChange={e => setTrackForm(p => ({ ...p, unit: e.target.value }))} placeholder="requests" /></div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="input-group"><label className="input-label">Category</label><input className="input" value={trackForm.category} onChange={e => setTrackForm(p => ({ ...p, category: e.target.value }))} /></div>
                <div className="input-group"><label className="input-label">Tags (key=value, comma)</label><input className="input" value={trackForm.tags} onChange={e => setTrackForm(p => ({ ...p, tags: e.target.value }))} placeholder="env=prod,module=api" /></div>
              </div>
              <button onClick={handleTrack} className="btn btn-primary"><Plus className="w-4 h-4" /> Track Metric</button>
            </div></Card>

            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">Query Metrics</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div className="input-group"><label className="input-label">Name</label><input className="input" value={metricFilters.name} onChange={e => setMetricFilters(p => ({ ...p, name: e.target.value }))} placeholder="Filter by name" /></div>
                <div className="input-group"><label className="input-label">Category</label><input className="input" value={metricFilters.category} onChange={e => setMetricFilters(p => ({ ...p, category: e.target.value }))} placeholder="Filter by category" /></div>
                <div className="input-group"><label className="input-label">Limit</label><input className="input" type="number" value={metricFilters.limit} onChange={e => setMetricFilters(p => ({ ...p, limit: +e.target.value }))} /></div>
                <button onClick={loadMetrics} className="btn btn-secondary"><RefreshCw className="w-4 h-4" /> Query</button>
              </div>
            </div></Card>

            {metrics.length > 0 ? (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Name</th><th>Value</th><th>Unit</th><th>Category</th><th>Tags</th><th>Time</th></tr></thead>
                  <tbody>{metrics.slice(0, 50).map((m: any, i: number) => (
                    <tr key={i}><td className="font-medium">{m.name}</td><td>{m.value}</td><td className="text-[var(--text-tertiary)]">{m.unit}</td><td><span className="badge badge-info">{m.category}</span></td><td className="text-xs text-[var(--text-tertiary)]">{m.tags ? Object.entries(m.tags).map(([k,v]) => `${k}=${v}`).join(', ') : '-'}</td><td className="text-xs text-[var(--text-tertiary)]">{m.timestamp ? new Date(m.timestamp * 1000).toLocaleString() : '-'}</td></tr>
                  ))}</tbody>
                </table>
              </div>
            ) : <div className="text-center py-8 text-[var(--text-tertiary)] text-sm">No metrics match the filters</div>}
          </div>
        )}

        {/* TRENDS TAB */}
        {tab === 'trends' && (
          <div className="space-y-6">
            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">View Trends</h2>
              <div className="flex items-end gap-4">
                <div className="input-group flex-1"><label className="input-label">Metric Name</label><input className="input" value={trendName} onChange={e => setTrendName(e.target.value)} placeholder="api_calls" /></div>
                <button onClick={loadTrends} className="btn btn-primary"><TrendingUp className="w-4 h-4" /> Load Trends</button>
              </div>
            </div></Card>
            {trendData && (
              <Card><div className="space-y-2">
                <h3 className="text-sm font-semibold">Trends for {trendName}</h3>
                <pre className="text-xs text-[var(--text-secondary)] overflow-auto max-h-80">{JSON.stringify(trendData, null, 2)}</pre>
              </div></Card>
            )}
          </div>
        )}

        {/* REPORT TAB */}
        {tab === 'report' && (
          <div className="space-y-6">
            {reportData ? (
              <Card><div className="space-y-2">
                <h3 className="text-sm font-semibold">Analytics Report</h3>
                <pre className="text-xs text-[var(--text-secondary)] overflow-auto max-h-96">{JSON.stringify(reportData, null, 2)}</pre>
              </div></Card>
            ) : (
              <div className="text-center py-12 text-[var(--text-tertiary)]">
                <Download className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p>Loading report data...</p>
                <button onClick={loadTab} className="btn btn-secondary mt-4"><RefreshCw className="w-4 h-4" /> Refresh</button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
