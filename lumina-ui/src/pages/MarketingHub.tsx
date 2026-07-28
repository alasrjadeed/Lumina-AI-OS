import { useState, useEffect } from 'react';
import { TrendingUp, Calendar, Plus, Play, Pause, CheckCircle, Megaphone, Eye, MousePointer, Target, Activity, BarChart3 } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
const get = async <T,>(p: string): Promise<T> => { const r = await fetch(BASE + p); if (!r.ok) throw new Error(await r.text()); return r.json(); };
const post = async <T,>(p: string, b?: any): Promise<T> => { const r = await fetch(BASE + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: b ? JSON.stringify(b) : undefined }); if (!r.ok) throw new Error(await r.text()); return r.json(); };

type Tab = 'campaigns' | 'content' | 'summary';

export default function MarketingHub() {
  const [tab, setTab] = useState<Tab>('campaigns');
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [content, setContent] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [cForm, setCForm] = useState({ name: '', channel: 'email', budget: 0 });
  const [ctForm, setCtForm] = useState({ title: '', content: '', channel: 'web', tags: '' });
  const toast = useToast();

  const load = async () => {
    setLoading(true);
    try {
      if (tab === 'campaigns') { const r = await get('/marketing/campaigns'); setCampaigns((r as any).campaigns || []); }
      if (tab === 'content') { const r = await get('/marketing/content'); setContent((r as any).items || []); }
      if (tab === 'summary') setSummary(await get('/marketing/summary'));
    } catch (_) {}
    setLoading(false);
  };
  useEffect(() => { load(); }, [tab]);

  const channels = ['email', 'social', 'search', 'display', 'content'];
  const tabs: Array<{ id: Tab; label: string; Icon: any }> = [
    { id: 'campaigns', label: 'Campaigns', Icon: Megaphone },
    { id: 'content', label: 'Content Calendar', Icon: Calendar },
    { id: 'summary', label: 'Summary', Icon: TrendingUp },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Marketing Hub</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Multi-channel campaigns, content calendar, and analytics</p></div>
      </div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}
          ><t.Icon className="w-3.5 h-3.5" /> {t.label}</button>
        ))}
      </div>
      <ContentArea tab={tab} loading={loading} campaigns={campaigns} content={content} summary={summary}
        cForm={cForm} setCForm={setCForm} ctForm={ctForm} setCtForm={setCtForm}
        channels={channels} toast={toast} reload={load} />
    </div>
  );
}

function ContentArea(props: any) {
  const { tab, loading, campaigns, content, summary, cForm, setCForm, ctForm, setCtForm, channels, toast, reload } = props;
  if (tab === 'campaigns') return <CampaignsTab loading={loading} campaigns={campaigns} cForm={cForm} setCForm={setCForm} channels={channels} toast={toast} reload={reload} />;
  if (tab === 'content') return <ContentTab loading={loading} content={content} ctForm={ctForm} setCtForm={setCtForm} channels={channels} toast={toast} reload={reload} />;
  return <SummaryTab loading={loading} summary={summary} />;
}

function CampaignsTab({ loading, campaigns, cForm, setCForm, channels, toast, reload }: any) {
  const cc = async () => { try { await post('/marketing/campaigns', cForm); setCForm({ name: '', channel: 'email', budget: 0 }); toast.addToast('Campaign created', 'success'); reload(); } catch (e: any) { toast.addToast(e.message, 'error'); } };
  const launch = async (n: string) => { try { await post(`/marketing/campaigns/${encodeURIComponent(n)}/launch`); toast.addToast('Launched', 'success'); reload(); } catch {} };
  const pause = async (n: string) => { try { await post(`/marketing/campaigns/${encodeURIComponent(n)}/pause`); toast.addToast('Paused', 'success'); reload(); } catch {} };
  const complete = async (n: string) => { try { await post(`/marketing/campaigns/${encodeURIComponent(n)}/complete`); toast.addToast('Completed', 'success'); reload(); } catch {} };

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      <Card><div className="space-y-4">
        <h2 className="text-lg font-semibold">New Campaign</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div className="input-group"><label className="input-label">Name</label><input className="input" value={cForm.name} onChange={e => setCForm((p: any) => ({ ...p, name: e.target.value }))} placeholder="Q3 Product Launch" /></div>
          <div className="input-group"><label className="input-label">Channel</label><select className="select" value={cForm.channel} onChange={e => setCForm((p: any) => ({ ...p, channel: e.target.value }))}>{channels.map((c: string) => <option key={c} value={c}>{c}</option>)}</select></div>
          <button onClick={cc} className="btn btn-primary"><Plus className="w-4 h-4" /> Create</button>
        </div>
      </div></Card>
      {loading ? <Skel n={3} h="h-20" /> : campaigns.length === 0 ? <Empty Icon={Megaphone} text="No campaigns yet" /> : campaigns.map((c: any) => (
        <div key={c.name} className="bg-[var(--bg-tertiary)] rounded-xl p-4 hover:bg-[var(--bg-hover)] transition-colors">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="font-medium">{c.name}</span>
              <span className={`badge ${c.status === 'active' ? 'badge-success' : c.status === 'paused' ? 'badge-warning' : c.status === 'completed' ? 'badge-info' : 'badge-error'}`}>{c.status}</span>
            </div>
            <div className="flex items-center gap-1">
              {c.status !== 'active' && <button onClick={() => launch(c.name)} className="btn btn-primary btn-sm"><Play className="w-3 h-3" /> Launch</button>}
              {c.status === 'active' && <button onClick={() => pause(c.name)} className="btn btn-secondary btn-sm"><Pause className="w-3 h-3" /> Pause</button>}
              {c.status === 'active' && <button onClick={() => complete(c.name)} className="btn btn-secondary btn-sm"><CheckCircle className="w-3 h-3" /> Complete</button>}
              <button onClick={async () => { try { await post(`/marketing/campaigns/${encodeURIComponent(c.name)}/impressions`, { name: c.name, count: 1 }); } catch {} }} className="btn btn-ghost btn-sm" title="Track Impression"><Eye className="w-3.5 h-3.5" /></button>
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Stat label="Channel" value={c.channel} color="brand" />
            <Stat label="Budget" value={`$${c.budget}`} color="blue" />
            <Stat label="Impressions" value={c.impressions || 0} Icon={Eye} />
            <Stat label="Clicks" value={c.clicks || 0} Icon={MousePointer} />
            <Stat label="Conversions" value={c.conversions || 0} Icon={Target} />
          </div>
        </div>
      ))}
    </div>
  );
}

function ContentTab({ loading, content, ctForm, setCtForm, channels, toast, reload }: any) {
  const create = async () => {
    try { await post('/marketing/content', { ...ctForm, tags: ctForm.tags.split(',').map((t: string) => t.trim()).filter(Boolean) }); setCtForm({ title: '', content: '', channel: 'web', tags: '' }); toast.addToast('Content scheduled', 'success'); reload(); } catch (e: any) { toast.addToast(e.message, 'error'); } };
  };
  const publish = async (title: string) => { try { await post(`/marketing/content/${encodeURIComponent(title)}/publish`); toast.addToast('Published', 'success'); reload(); } catch {} };

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      <Card><div className="space-y-4">
        <h2 className="text-lg font-semibold">Schedule Content</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="input-group"><label className="input-label">Title</label><input className="input" value={ctForm.title} onChange={e => setCtForm((p: any) => ({ ...p, title: e.target.value }))} placeholder="How AI Transforms Marketing" /></div>
          <div className="input-group"><label className="input-label">Channel</label><select className="select" value={ctForm.channel} onChange={e => setCtForm((p: any) => ({ ...p, channel: e.target.value }))}>{channels.map((c: string) => <option key={c} value={c}>{c}</option>)}</select></div>
        </div>
        <div className="input-group"><label className="input-label">Content</label><textarea className="input h-24" value={ctForm.content} onChange={e => setCtForm((p: any) => ({ ...p, content: e.target.value }))} placeholder="Write your content..." /></div>
        <div className="input-group"><label className="input-label">Tags</label><input className="input" value={ctForm.tags} onChange={e => setCtForm((p: any) => ({ ...p, tags: e.target.value }))} placeholder="ai,marketing,automation" /></div>
        <button onClick={create} className="btn btn-primary"><Calendar className="w-4 h-4" /> Schedule</button>
      </div></Card>
      {loading ? <Skel n={3} h="h-16" /> : content.length === 0 ? <Empty Icon={Calendar} text="No scheduled content" /> : content.map((item: any) => (
        <div key={item.title} className="bg-[var(--bg-tertiary)] rounded-xl p-4 flex items-center justify-between hover:bg-[var(--bg-hover)] transition-colors">
          <div><div className="flex items-center gap-2"><span className="font-medium">{item.title}</span><span className={`badge ${item.status === 'published' ? 'badge-success' : 'badge-info'}`}>{item.status}</span></div><div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-secondary)]"><span>{item.channel}</span>{item.tags?.length > 0 && <span>{item.tags.join(', ')}</span>}</div></div>
          {item.status !== 'published' && <button onClick={() => publish(item.title)} className="btn btn-primary btn-sm"><Play className="w-3 h-3" /> Publish</button>}
        </div>
      ))}
    </div>
  );
}

function SummaryTab({ loading, summary }: any) {
  if (loading) return <div className="flex-1 overflow-auto p-6"><Skel n={4} h="h-24" /></div>;
  if (!summary) return <Empty Icon={TrendingUp} text="No data available yet" />;
  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Active Campaigns" value={summary.active_campaigns ?? summary.campaigns ?? 0} color="green" Icon={Activity} />
        <Stat label="Total Impressions" value={summary.total_impressions ?? summary.impressions ?? 0} color="brand" Icon={Eye} />
        <Stat label="Total Clicks" value={summary.total_clicks ?? summary.clicks ?? 0} color="blue" Icon={MousePointer} />
        <Stat label="Conversion Rate" value={`${summary.conversion_rate ?? summary.conversions ?? 0}%`} color="amber" Icon={Target} />
      </div>
      <Card><div className="text-center py-8 text-[var(--text-secondary)]"><BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" /><p className="text-sm">Marketing metrics are tracked as campaigns run</p><p className="text-xs text-[var(--text-tertiary)] mt-1">Launch campaigns and track impressions, clicks, and conversions</p></div></Card>
    </div>
  );
}

function Stat({ label, value, Icon, color = 'brand' }: any) {
  const colors: any = { brand: 'var(--brand-500)', green: 'var(--color-success)', amber: 'var(--color-warning)', red: 'var(--color-error)', blue: 'var(--color-info)' };
  return <div className="bg-[var(--bg-tertiary)] rounded-xl p-4"><div className="flex items-center justify-between"><p className="text-2xs text-[var(--text-tertiary)] uppercase tracking-wider">{label}</p>{Icon && <Icon className="w-4 h-4" style={{ color: colors[color] }} />}</div><p className="text-2xl font-bold mt-1" style={{ color: colors[color] }}>{value}</p></div>;
}
function Empty({ Icon, text }: any) { return <div className="text-center py-12 text-[var(--text-tertiary)]"><Icon className="w-12 h-12 mx-auto mb-3 opacity-30" /><p className="text-sm">{text}</p></div>; }
function Skel({ n, h }: any) { return <div className="space-y-2">{Array(n).fill(0).map((_, i) => <div key={i} className={`skeleton ${h} w-full`} />)}</div>; }
