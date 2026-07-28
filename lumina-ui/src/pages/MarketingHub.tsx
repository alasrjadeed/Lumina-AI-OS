import { useState, useEffect } from 'react';
import { TrendingUp, Calendar, Plus, Play, Pause, CheckCircle, BarChart3, Megaphone, Eye, MousePointer, Target, Activity, RefreshCw } from 'lucide-react';
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

export default function MarketingHub() {
  const [tab, setTab] = useState<'campaigns' | 'content' | 'summary'>('campaigns');
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [content, setContent] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [cForm, setCForm] = useState({ name: '', channel: 'email', budget: 0 });
  const [ctForm, setCtForm] = useState({ title: '', content: '', channel: 'web', tags: '' });
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, [tab]);

  async function loadAll() {
    setLoading(true);
    try {
      if (tab === 'campaigns') setCampaigns((await get('/marketing/campaigns')).campaigns || []);
      if (tab === 'content') setContent((await get('/marketing/content')).items || []);
      if (tab === 'summary') setSummary(await get('/marketing/summary'));
    } catch (e: any) { /* silent */ }
    setLoading(false);
  }

  async function createCampaign() {
    try { await post('/marketing/campaigns', cForm); setCForm({ name: '', channel: 'email', budget: 0 }); addToast('Campaign created', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function launchCampaign(name: string) { try { await post(`/marketing/campaigns/${encodeURIComponent(name)}/launch`); addToast('Launched', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); } }
  async function pauseCampaign(name: string) { try { await post(`/marketing/campaigns/${encodeURIComponent(name)}/pause`); addToast('Paused', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); } }
  async function completeCampaign(name: string) { try { await post(`/marketing/campaigns/${encodeURIComponent(name)}/complete`); addToast('Completed', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); } }
  async function trackImpression(name: string) { try { await post(`/marketing/campaigns/${encodeURIComponent(name)}/impressions`, { name, count: 1 }); loadAll(); } catch (e: any) { addToast(e.message, 'error'); } }
  async function createContent() {
    const tags = ctForm.tags.split(',').map(t => t.trim()).filter(Boolean);
    try { await post('/marketing/content', { ...ctForm, tags }); setCtForm({ title: '', content: '', channel: 'web', tags: '' }); addToast('Content scheduled', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); } }
  }
  async function publishContent(title: string) { try { await post(`/marketing/content/${encodeURIComponent(title)}/publish`); addToast('Published', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); } }

  const tabs = [
    { id: 'campaigns' as const, label: 'Campaigns', icon: Megaphone },
    { id: 'content' as const, label: 'Content Calendar', icon: Calendar },
    { id: 'summary' as const, label: 'Summary', icon: TrendingUp },
  ];

  const channels = ['email', 'social', 'search', 'display', 'content'];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Marketing Hub</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Multi-channel campaigns, content calendar, and analytics</p></div>
      </div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {/* CAMPAIGNS TAB */}
        {tab === 'campaigns' && (
          <div className="space-y-6">
            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">New Campaign</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div className="input-group"><label className="input-label">Name</label><input className="input" value={cForm.name} onChange={e => setCForm(p => ({ ...p, name: e.target.value }))} placeholder="Q3 Product Launch" /></div>
                <div className="input-group"><label className="input-label">Channel</label><select className="select" value={cForm.channel} onChange={e => setCForm(p => ({ ...p, channel: e.target.value }))}>{channels.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
                <button onClick={createCampaign} className="btn btn-primary"><Plus className="w-4 h-4" /> Create</button>
              </div>
            </div></Card>

            {loading ? (
              <div className="space-y-2">{Array(3).fill(0).map((_,i) => <Skeleton key={i} h="h-20" />)}</div>
            ) : campaigns.length === 0 ? (
              <div className="text-center py-12 text-[var(--text-tertiary)]"><Megaphone className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No campaigns yet</p></div>
            ) : (
              <div className="space-y-2">
                {campaigns.map((c: any) => (
                  <div key={c.name} className="bg-[var(--bg-tertiary)] rounded-xl p-4 hover:bg-[var(--bg-hover)] transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{c.name}</span>
                      <span className={`badge ${c.status === 'active' ? 'badge-success' : c.status === 'paused' ? 'badge-warning' : c.status === 'completed' ? 'badge-info' : 'badge-error'}`}>{c.status}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      {c.status !== 'active' && <button onClick={() => launchCampaign(c.name)} className="btn btn-primary btn-sm"><Play className="w-3 h-3" /> Launch</button>}
                      {c.status === 'active' && <button onClick={() => pauseCampaign(c.name)} className="btn btn-secondary btn-sm"><Pause className="w-3 h-3" /> Pause</button>}
                      {c.status === 'active' && <button onClick={() => completeCampaign(c.name)} className="btn btn-secondary btn-sm"><CheckCircle className="w-3 h-3" /> Complete</button>}
                      <button onClick={() => trackImpression(c.name)} className="btn btn-ghost btn-sm" title="Track Impression"><Eye className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    <StatCard label="Channel" value={c.channel} color="brand" />
                    <StatCard label="Budget" value={`$${c.budget}`} color="blue" />
                    <StatCard label="Impressions" value={c.impressions || 0} icon={Eye} />
                    <StatCard label="Clicks" value={c.clicks || 0} icon={MousePointer} />
                    <StatCard label="Conversions" value={c.conversions || 0} icon={Target} />
                  </div>
                </div>
              ))}
            </div>}
          </div>
        )}

        {/* CONTENT CALENDAR TAB */}
        {tab === 'content' && (
          <div className="space-y-6">
            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">Schedule Content</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="input-group"><label className="input-label">Title</label><input className="input" value={ctForm.title} onChange={e => setCtForm(p => ({ ...p, title: e.target.value }))} placeholder="How AI Transforms Marketing" /></div>
                <div className="input-group"><label className="input-label">Channel</label><select className="select" value={ctForm.channel} onChange={e => setCtForm(p => ({ ...p, channel: e.target.value }))}>{channels.map(c => <option key={c} value={c}>{c}</option>)}</select></div>
              </div>
              <div className="input-group"><label className="input-label">Content</label><textarea className="input h-24" value={ctForm.content} onChange={e => setCtForm(p => ({ ...p, content: e.target.value }))} placeholder="Write your content..." /></div>
              <div className="input-group"><label className="input-label">Tags (comma-separated)</label><input className="input" value={ctForm.tags} onChange={e => setCtForm(p => ({ ...p, tags: e.target.value }))} placeholder="ai,marketing,automation" /></div>
              <button onClick={createContent} className="btn btn-primary"><Calendar className="w-4 h-4" /> Schedule</button>
            </div></Card>

            {loading ? <div className="space-y-2">{Array(3).fill(0).map((_,i) => <Skeleton key={i} h="h-16" />)}</div> : content.length === 0 ? <div className="text-center py-12 text-[var(--text-tertiary)]"><Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No scheduled content</p></div>
            : <div className="space-y-2">
              {content.map((item: any) => (
                <div key={item.title} className="bg-[var(--bg-tertiary)] rounded-xl p-4 flex items-center justify-between hover:bg-[var(--bg-hover)] transition-colors">
                  <div>
                    <div className="flex items-center gap-2"><span className="font-medium">{item.title}</span><span className={`badge ${item.status === 'published' ? 'badge-success' : 'badge-info'}`}>{item.status}</span></div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-secondary)]">
                      <span>Channel: {item.channel}</span>
                      {item.tags?.length > 0 && <span>Tags: {item.tags.join(', ')}</span>}
                    </div>
                  </div>
                  {item.status !== 'published' && <button onClick={() => publishContent(item.title)} className="btn btn-primary btn-sm"><Play className="w-3 h-3" /> Publish</button>}
                </div>
              ))}
            </div>}
          </div>
        )}

        {/* SUMMARY TAB */}
        {tab === 'summary' && (
          <div className="space-y-6">
            {loading ? <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{Array(4).fill(0).map((_,i) => <Skeleton key={i} h="h-24" />)}</div>
            : summary ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StatCard label="Active Campaigns" value={summary.active_campaigns ?? summary.campaigns ?? 0} icon={Activity} color="green" />
                  <StatCard label="Total Impressions" value={summary.total_impressions ?? summary.impressions ?? 0} icon={Eye} color="brand" />
                  <StatCard label="Total Clicks" value={summary.total_clicks ?? summary.clicks ?? 0} icon={MousePointer} color="blue" />
                  <StatCard label="Conversion Rate" value={`${summary.conversion_rate ?? summary.conversions ?? 0}%`} icon={Target} color="amber" />
                </div>
                <Card><div className="text-center py-8 text-[var(--text-secondary)]">
                  <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Marketing metrics are tracked as campaigns run</p>
                  <p className="text-xs text-[var(--text-tertiary)] mt-1">Launch campaigns and track impressions, clicks, and conversions</p>
                </div></Card>
              </div>
            ) : <div className="text-center py-12 text-[var(--text-tertiary)]"><TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No data available yet</p></div>}
          </div>
        )}
                    </div>
                  </div>
                ))}
              </div>
            )}
