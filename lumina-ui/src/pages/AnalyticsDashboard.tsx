import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Activity, Download, Target, Eye, Zap, RefreshCw, Plus, Search } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
const get = async <T,>(p: string): Promise<T> => { const r = await fetch(BASE + p); if (!r.ok) throw Error(await r.text()); return r.json(); };
const post = async <T,>(p: string, b?: any): Promise<T> => { const r = await fetch(BASE + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: b ? JSON.stringify(b) : undefined }); if (!r.ok) throw Error(await r.text()); return r.json(); };

export default function AnalyticsDashboard() {
  const [tab, setTab] = useState<'dashboard'|'metrics'|'trends'>('dashboard');
  const [dash, setDash] = useState<any>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [value, setValue] = useState(0);
  const [unit, setUnit] = useState('');
  const [category, setCategory] = useState('general');
  const [trendName, setTrendName] = useState('');
  const [trendData, setTrendData] = useState<any>(null);
  const [reportData, setReportData] = useState<any>(null);
  const toast = useToast();

  useEffect(() => { load(); }, [tab]);
  const load = async () => {
    setLoading(true);
    try {
      if (tab === 'dashboard') setDash(await get('/analytics/dashboard'));
      if (tab === 'metrics') { const r = await get('/analytics/metrics?limit=50'); setMetrics((r as any).metrics||[]); }
      if (tab === 'report') setReportData(await get('/analytics/report'));
    } catch (_) {} finally { setLoading(false); }
  };

  const track = async () => { try { await post('/analytics/track',{name,value,unit,category}); setName('');setValue(0);setUnit(''); toast.addToast('Metric tracked','success'); load(); } catch (e:any) { toast.addToast(e.message,'error'); } };
  const loadTrends = async () => { if (!trendName) return; try { setTrendData(await get('/analytics/trends/'+encodeURIComponent(trendName))); } catch {} };

  if (loading && !dash) return <div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-3 border-[var(--border-primary)] border-t-[var(--brand-500)] rounded-full animate-spin"/></div>;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0"><div><h1 className="text-xl font-semibold">Analytics</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Cross-module metrics, trends, and reports</p></div></div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {[{id:'dashboard',l:'Dashboard',i:BarChart3},{id:'metrics',l:'Metrics',i:Activity},{id:'trends',l:'Trends',i:TrendingUp},{id:'report',l:'Report',i:Download}].map((t:any)=>(<button key={t.id} onClick={()=>setTab(t.id)} className={'flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors '+(tab===t.id?'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]':'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]')}><t.i className="w-3.5 h-3.5"/>{t.l}</button>))}
      </div>
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {tab==='dashboard'&&dash&&<>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Stat label="Metrics Today" value={dash.total_metrics_today??0} color="brand" Icon={Activity}/>
            <Stat label="Categories" value={Object.keys(dash.categories||{}).length} color="blue" Icon={Target}/>
            <Stat label="This Week" value={dash.total_metrics_week??0} color="green" Icon={Zap}/>
            <Stat label="Snapshots" value={(dash.snapshots||[]).length} color="amber" Icon={Eye}/>
          </div>
          <Card><div className="space-y-3"><h3 className="text-sm font-semibold">Latest Values</h3>
            {Object.keys(dash.latest_values||{}).length>0 ? <div className="space-y-1">{Object.entries(dash.latest_values||{}).map(([k,v]:[string,any])=>(<div key={k} className="flex items-center justify-between py-1.5 px-3 rounded bg-[var(--bg-tertiary)] text-xs"><span className="text-[var(--text-secondary)]">{k}</span><span className="font-medium">{v}</span></div>))}</div>
            : <div className="text-center py-6 text-[var(--text-tertiary)] text-sm">No metrics tracked yet. Go to the Metrics tab to start tracking.</div>}
          </div></Card>
        </>}
        {tab==='metrics'&&<>
          <Card><div className="space-y-4"><h2 className="text-lg font-semibold">Track Metric</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
              <div className="input-group"><label className="input-label">Name</label><input className="input" value={name} onChange={e=>setName(e.target.value)} placeholder="api_calls"/></div>
              <div className="input-group"><label className="input-label">Value</label><input className="input" type="number" value={value} onChange={e=>setValue(+e.target.value)}/></div>
              <div className="input-group"><label className="input-label">Unit</label><input className="input" value={unit} onChange={e=>setUnit(e.target.value)} placeholder="requests"/></div>
              <button onClick={track} className="btn btn-primary"><Plus className="w-4 h-4"/>Track</button>
            </div>
          </div></Card>
          {metrics.length>0 ? <div className="table-wrap"><table><thead><tr><th>Name</th><th>Value</th><th>Unit</th><th>Category</th><th>Time</th></tr></thead><tbody>{metrics.map((m:any,i:number)=>(<tr key={i}><td className="font-medium">{m.name}</td><td>{m.value}</td><td className="text-[var(--text-tertiary)]">{m.unit}</td><td><span className="badge badge-info">{m.category}</span></td><td className="text-xs text-[var(--text-tertiary)]">{m.timestamp?new Date(m.timestamp*1000).toLocaleString():'-'}</td></tr>))}</tbody></table></div>
          : <div className="text-center py-12 text-[var(--text-tertiary)]"><Activity className="w-12 h-12 mx-auto mb-3 opacity-30"/><p className="text-sm">No metrics yet</p></div>}
        </>}
        {tab==='trends'&&<>
          <Card><div className="space-y-4"><h2 className="text-lg font-semibold">View Trends</h2>
            <div className="flex items-end gap-4">
              <div className="input-group flex-1"><label className="input-label">Metric Name</label><input className="input" value={trendName} onChange={e=>setTrendName(e.target.value)} placeholder="api_calls" onKeyDown={e=>e.key==='Enter'&&loadTrends()}/></div>
              <button onClick={loadTrends} className="btn btn-primary"><TrendingUp className="w-4 h-4"/>Load</button>
            </div></div></Card>
          {trendData&&<Card><pre className="text-xs text-[var(--text-secondary)] overflow-auto max-h-80">{JSON.stringify(trendData,null,2)}</pre></Card>}
        </>}
        {tab==='report'&&(reportData
          ? <Card><pre className="text-xs text-[var(--text-secondary)] overflow-auto max-h-96">{JSON.stringify(reportData,null,2)}</pre></Card>
          : <div className="text-center py-12 text-[var(--text-tertiary)]"><Download className="w-12 h-12 mx-auto mb-3 opacity-30"/><p className="text-sm">No report data</p><button onClick={load} className="btn btn-secondary btn-sm mt-3"><RefreshCw className="w-3.5 h-3.5"/>Refresh</button></div>
        )}
      </div>
    </div>
  );
}

function Stat({label,value,Icon,color='brand'}:{label:string;value:string|number;Icon?:any;color?:string}) {
  const c:any={brand:'var(--brand-500)',green:'var(--color-success)',amber:'var(--color-warning)',red:'var(--color-error)',blue:'var(--color-info)'};
  return <div className="bg-[var(--bg-tertiary)] rounded-xl p-4"><div className="flex items-center justify-between"><p className="text-2xs text-[var(--text-tertiary)] uppercase tracking-wider">{label}</p>{Icon&&<Icon className="w-4 h-4" style={{color:c[color]}}/>}</div><p className="text-2xl font-bold mt-1" style={{color:c[color]}}>{value}</p></div>;
}
