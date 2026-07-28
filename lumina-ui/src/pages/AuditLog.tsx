import { useState, useEffect } from 'react';
import { Shield, Search, Filter, Clock, Activity, FileText, RefreshCw, AlertTriangle, CheckCircle } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
async function get<T>(path: string): Promise<T> { const r = await fetch(`${BASE}${path}`); if (!r.ok) throw new Error(await r.text()); return r.json(); }

function StatCard({ label, value, color = 'brand', icon: Icon }: { label: string; value: string | number; color?: string; icon?: any }) {
  const colors: Record<string, string> = { brand: 'var(--brand-500)', green: 'var(--color-success)', amber: 'var(--color-warning)', red: 'var(--color-error)' };
  return <div className="bg-[var(--bg-tertiary)] rounded-xl p-4"><div className="flex items-center justify-between"><p className="text-2xs text-[var(--text-tertiary)] uppercase tracking-wider">{label}</p>{Icon && <Icon className="w-4 h-4" style={{ color: colors[color] }} />}</div><p className="text-2xl font-bold mt-1" style={{ color: colors[color] }}>{value}</p></div>;
}

function Skeleton({ h = 'h-8' }: { h?: string }) { return <div className={`skeleton ${h} w-full`} />; }

export default function AuditLogViewer() {
  const [tab, setTab] = useState<'entries' | 'today' | 'stats'>('entries');
  const [entries, setEntries] = useState<any[]>([]);
  const [today, setToday] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [actions, setActions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ agent: '', action: '', status: '', limit: 100 });
  const [reportDate, setReportDate] = useState('');
  const [report, setReport] = useState<any>(null);
  const { addToast } = useToast();

  useEffect(() => { loadTab(); }, [tab]);

  async function loadTab() {
    setLoading(true);
    try {
      if (tab === 'entries') loadEntries();
      if (tab === 'today') setToday(await get('/audit/today'));
      if (tab === 'stats') { setStats(await get('/audit/stats')); setActions((await get('/audit/actions')).actions || []); }
    } catch (e: any) { /* silent */ }
    setLoading(false);
  }

  async function loadEntries() {
    const params = new URLSearchParams();
    if (filters.agent) params.set('agent', filters.agent);
    if (filters.action) params.set('action', filters.action);
    if (filters.status) params.set('status', filters.status);
    params.set('limit', String(filters.limit));
    try { const r: any = await get(`/audit/entries?${params}`); setEntries(r.entries || []); } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function loadReport() {
    if (!reportDate) return;
    try { setReport(await get(`/audit/report?date=${reportDate}`)); } catch (e: any) { addToast(e.message, 'error'); }
  }

  const tabs = [
    { id: 'entries' as const, label: 'Entries', icon: FileText },
    { id: 'today' as const, label: 'Today', icon: Clock },
    { id: 'stats' as const, label: 'Stats', icon: Activity },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Audit Log</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Agent action audit trail with tamper-evident chain</p></div>
      </div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {/* ENTRIES TAB */}
        {tab === 'entries' && (
          <div className="space-y-6">
            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">Filter Entries</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div className="input-group"><label className="input-label">Agent</label><input className="input" value={filters.agent} onChange={e => setFilters(p => ({ ...p, agent: e.target.value }))} placeholder="LeadGen AI" /></div>
                <div className="input-group"><label className="input-label">Action</label><input className="input" value={filters.action} onChange={e => setFilters(p => ({ ...p, action: e.target.value }))} placeholder="generate" /></div>
                <div className="input-group"><label className="input-label">Status</label><select className="select" value={filters.status} onChange={e => setFilters(p => ({ ...p, status: e.target.value }))}><option value="">All</option><option value="success">Success</option><option value="failure">Failure</option></select></div>
                <button onClick={loadEntries} className="btn btn-primary"><Search className="w-4 h-4" /> Search</button>
              </div>
            </div></Card>

            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">Report by Date</h2>
              <div className="flex items-end gap-4">
                <div className="input-group flex-1"><label className="input-label">Date (YYYY-MM-DD)</label><input className="input" value={reportDate} onChange={e => setReportDate(e.target.value)} placeholder="2026-07-28" /></div>
                <button onClick={loadReport} className="btn btn-secondary"><FileText className="w-4 h-4" /> Load Report</button>
              </div>
              {report && <pre className="text-xs text-[var(--text-secondary)] mt-4 overflow-auto max-h-40 bg-[var(--bg-primary)] rounded-lg p-3">{JSON.stringify(report, null, 2)}</pre>}
            </div></Card>

            {loading ? <div className="space-y-2">{Array(5).fill(0).map((_,i) => <Skeleton key={i} h="h-12" />)}</div> : entries.length === 0 ? <div className="text-center py-12 text-[var(--text-tertiary)]"><Shield className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No audit entries match the filters</p></div>
            : <div className="table-wrap">
              <table>
                <thead><tr><th>Agent</th><th>Action</th><th>Status</th><th>Details</th><th>Time</th></tr></thead>
                <tbody>{entries.map((e: any, i: number) => (
                  <tr key={i}>
                    <td className="font-medium">{e.agent || e.actor || '-'}</td>
                    <td>{e.action}</td>
                    <td>{e.status === 'success' ? <span className="badge badge-success flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Success</span> : <span className="badge badge-error flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Failed</span>}</td>
                    <td className="text-xs text-[var(--text-secondary)] max-w-xs truncate">{e.details ? JSON.stringify(e.details) : e.resource || '-'}</td>
                    <td className="text-xs text-[var(--text-tertiary)] whitespace-nowrap">{e.timestamp ? new Date(e.timestamp * (e.timestamp > 1e12 ? 1 : 1000)).toLocaleString() : '-'}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>}
          </div>
        )}

        {/* TODAY TAB */}
        {tab === 'today' && (
          <div className="space-y-6">
            {today ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard label="Total Today" value={today.total ?? today.count ?? 0} color="brand" icon={Activity} />
                  <StatCard label="Success" value={today.success ?? 0} color="green" icon={CheckCircle} />
                  <StatCard label="Failures" value={today.failures ?? today.failed ?? 0} color="red" icon={AlertTriangle} />
                  <StatCard label="Unique Agents" value={today.agents ?? today.unique_agents ?? 0} color="blue" icon={Shield} />
                </div>
                <Card><pre className="text-xs text-[var(--text-secondary)] overflow-auto max-h-96">{JSON.stringify(today, null, 2)}</pre></Card>
              </>
            ) : <div className="text-center py-12 text-[var(--text-tertiary)]"><Clock className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No data for today yet</p></div>}
          </div>
        )}

        {/* STATS TAB */}
        {tab === 'stats' && (
          <div className="space-y-6">
            {stats ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard label="Total Events" value={stats.total ?? stats.events ?? 0} color="brand" icon={Activity} />
                  <StatCard label="Success Rate" value={`${stats.success_rate ?? 100}%`} color="green" icon={CheckCircle} />
                  <StatCard label="Top Action" value={stats.top_action ?? '-'} color="blue" icon={FileText} />
                  <StatCard label="Top Agent" value={stats.top_agent ?? '-'} color="amber" icon={Shield} />
                </div>
                {actions.length > 0 && (
                  <Card><div className="space-y-2">
                    <h3 className="text-sm font-semibold">Available Actions ({actions.length})</h3>
                    <div className="flex flex-wrap gap-1">
                      {actions.map((a: string) => <span key={a} className="badge badge-info">{a}</span>)}
                    </div>
                  </div></Card>
                )}
                <Card><pre className="text-xs text-[var(--text-secondary)] overflow-auto max-h-96">{JSON.stringify(stats, null, 2)}</pre></Card>
              </>
            ) : <div className="text-center py-12 text-[var(--text-tertiary)]"><Activity className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No statistics available</p></div>}
          </div>
        )}
      </div>
    </div>
  );
}
