import { useState, useEffect } from 'react';
import { TrendingUp, Calendar, Plus, Play, Pause, CheckCircle, Megaphone, Eye, MousePointer, Target, Activity, BarChart3 } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
const api = {
  get: async <T,>(p: string): Promise<T> => { const r = await fetch(BASE + p); if (!r.ok) throw Error(await r.text()); return r.json(); },
  post: async <T,>(p: string, b?: any): Promise<T> => { const r = await fetch(BASE + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: b ? JSON.stringify(b) : undefined }); if (!r.ok) throw Error(await r.text()); return r.json(); },
};

export default function MarketingHub() {
  const [tab, setTab] = useState<'campaigns'|'content'|'summary'>('campaigns');
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [content, setContent] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [channel, setChannel] = useState('email');
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [ch, setCh] = useState('web');
  const [tags, setTags] = useState('');
  const toast = useToast();
  const channels = ['email','social','search','display','content'];

  const load = async () => {
    setLoading(true);
    try {
      if (tab === 'campaigns') { const r = await api.get('/marketing/campaigns'); setCampaigns((r as any).campaigns||[]); }
      if (tab === 'content') { const r = await api.get('/marketing/content'); setContent((r as any).items||[]); }
      if (tab === 'summary') setSummary(await api.get('/marketing/summary'));
    } catch (_) {}
    setLoading(false);
  };
  useEffect(() => { load(); }, [tab]);

  const createCampaign = async () => { try { await api.post('/marketing/campaigns',{name,channel,budget:0}); setName(''); toast.addToast('Created','success'); load(); } catch(e:any) { toast.addToast(e.message,'error'); } };
  const launch = async (n:string) => { try { await api.post('/marketing/campaigns/'+encodeURIComponent(n)+'/launch'); load(); } catch {} };
  const pause = async (n:string) => { try { await api.post('/marketing/campaigns/'+encodeURIComponent(n)+'/pause'); load(); } catch {} };
  const complete = async (n:string) => { try { await api.post('/marketing/campaigns/'+encodeURIComponent(n)+'/complete'); load(); } catch {} };
  const createContent = async () => { try { await api.post('/marketing/content',{title,content:body,channel:ch,tags:tags.split(',').map((t:string)=>t.trim()).filter(Boolean)}); setTitle('');setBody('');setTags(''); toast.addToast('Scheduled','success'); load(); } catch(e:any) { toast.addToast(e.message,'error'); } };
  const publish = async (t:string) => { try { await api.post('/marketing/content/'+encodeURIComponent(t)+'/publish'); load(); } catch {} };

  function renderCampaigns() {
    if (loading) return <div className="space-y-2">{[1,2,3].map(i=><div key={i} className="skeleton h-20 w-full"/>)}</div>;
    if (campaigns.length===0) return <div className="text-center py-12 text-[var(--text-tertiary)]"><Megaphone className="w-12 h-12 mx-auto mb-3 opacity-30"/><p className="text-sm">No campaigns yet</p></div>;
    return campaigns.map((c:any)=>(
      <div key={c.name} className="bg-[var(--bg-tertiary)] rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2"><span className="font-medium">{c.name}</span><span className={'badge '+(c.status==='active'?'badge-success':c.status==='paused'?'badge-warning':c.status==='completed'?'badge-info':'badge-error')}>{c.status}</span></div>
          <div className="flex items-center gap-1">
            {c.status!=='active'&&<button onClick={()=>launch(c.name)} className="btn btn-primary btn-sm"><Play className="w-3 h-3"/>Launch</button>}
            {c.status==='active'&&<button onClick={()=>pause(c.name)} className="btn btn-secondary btn-sm"><Pause className="w-3 h-3"/>Pause</button>}
            {c.status==='active'&&<button onClick={()=>complete(c.name)} className="btn btn-secondary btn-sm"><CheckCircle className="w-3 h-3"/>Complete</button>}
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Stat label="Channel" value={c.channel}/>
          <Stat label="Budget" value={'$'+c.budget} color="blue"/>
          <Stat label="Impressions" value={c.impressions||0}/>
          <Stat label="Clicks" value={c.clicks||0}/>
          <Stat label="Conversions" value={c.conversions||0}/>
        </div>
      </div>
    ));
  }

  function renderContent() {
    if (loading) return <div className="space-y-2">{[1,2,3].map(i=><div key={i} className="skeleton h-16 w-full"/>)}</div>;
    if (content.length===0) return <div className="text-center py-12 text-[var(--text-tertiary)]"><Calendar className="w-12 h-12 mx-auto mb-3 opacity-30"/><p className="text-sm">No scheduled content</p></div>;
    return content.map((item:any)=>(
      <div key={item.title} className="bg-[var(--bg-tertiary)] rounded-xl p-4 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2"><span className="font-medium">{item.title}</span><span className={'badge '+(item.status==='published'?'badge-success':'badge-info')}>{item.status}</span></div>
          <div className="flex items-center gap-3 mt-1 text-xs text-[var(--text-secondary)]"><span>{item.channel}</span>{item.tags?.length>0&&<span>{item.tags.join(', ')}</span>}</div>
        </div>
        {item.status!=='published'&&<button onClick={()=>publish(item.title)} className="btn btn-primary btn-sm"><Play className="w-3 h-3"/>Publish</button>}
      </div>
    ));
  }

  function renderSummary() {
    if (loading) return <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[1,2,3,4].map(i=><div key={i} className="skeleton h-24 w-full"/>)}</div>;
    if (!summary) return <div className="text-center py-12 text-[var(--text-tertiary)]"><TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-30"/><p className="text-sm">No data yet</p></div>;
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Active" value={summary.active_campaigns??summary.campaigns??0} color="green"/>
          <Stat label="Impressions" value={summary.total_impressions??summary.impressions??0} color="brand"/>
          <Stat label="Clicks" value={summary.total_clicks??summary.clicks??0} color="blue"/>
          <Stat label="Rate" value={(summary.conversion_rate??summary.conversions??0)+'%'} color="amber"/>
        </div>
        <Card><div className="text-center py-8 text-[var(--text-secondary)]"><BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30"/><p className="text-sm">Launch campaigns to track metrics</p></div></Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0"><div><h1 className="text-xl font-semibold">Marketing Hub</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Campaigns, content calendar, analytics</p></div></div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {[{id:'campaigns',l:'Campaigns',i:Megaphone},{id:'content',l:'Calendar',i:Calendar},{id:'summary',l:'Summary',i:TrendingUp}].map((t:any)=>(<button key={t.id} onClick={()=>setTab(t.id)} className={'flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors '+(tab===t.id?'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]':'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]')}><t.i className="w-3.5 h-3.5"/>{t.l}</button>))}
      </div>
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {tab==='campaigns'&&<>
          <Card><div className="space-y-4"><h2 className="text-lg font-semibold">New Campaign</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div className="input-group"><label className="input-label">Name</label><input className="input" value={name} onChange={e=>setName(e.target.value)} placeholder="Q3 Launch"/></div>
              <div className="input-group"><label className="input-label">Channel</label><select className="select" value={channel} onChange={e=>setChannel(e.target.value)}>{channels.map((c:string)=><option key={c} value={c}>{c}</option>)}</select></div>
              <button onClick={createCampaign} className="btn btn-primary"><Plus className="w-4 h-4"/>Create</button>
            </div></div></Card>
          {renderCampaigns()}
        </>}
        {tab==='content'&&<>
          <Card><div className="space-y-4"><h2 className="text-lg font-semibold">Schedule Content</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="input-group"><label className="input-label">Title</label><input className="input" value={title} onChange={e=>setTitle(e.target.value)} placeholder="Post title"/></div>
              <div className="input-group"><label className="input-label">Channel</label><select className="select" value={ch} onChange={e=>setCh(e.target.value)}>{channels.map((c:string)=><option key={c} value={c}>{c}</option>)}</select></div>
            </div>
            <div className="input-group"><label className="input-label">Content</label><textarea className="input h-24" value={body} onChange={e=>setBody(e.target.value)} placeholder="Write your content..."/></div>
            <div className="input-group"><label className="input-label">Tags</label><input className="input" value={tags} onChange={e=>setTags(e.target.value)} placeholder="ai,marketing"/></div>
            <button onClick={createContent} className="btn btn-primary"><Calendar className="w-4 h-4"/>Schedule</button>
          </div></Card>
          {renderContent()}
        </>}
        {tab==='summary'&&renderSummary()}
      </div>
    </div>
  );
}

function Stat({label,value,color='brand'}:{label:string;value:string|number;color?:string}) {
  const c:any={brand:'var(--brand-500)',green:'var(--color-success)',amber:'var(--color-warning)',red:'var(--color-error)',blue:'var(--color-info)'};
  return <div className="bg-[var(--bg-tertiary)] rounded-xl p-4"><p className="text-2xs text-[var(--text-tertiary)] uppercase">{label}</p><p className="text-2xl font-bold mt-1" style={{color:c[color]}}>{value}</p></div>;
}
