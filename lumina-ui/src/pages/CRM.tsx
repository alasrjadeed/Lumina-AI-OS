import { useState, useEffect } from 'react';
import { Briefcase, UserPlus, TrendingUp, Plus, Trash2, Clock, DollarSign, BarChart3, ArrowRight, CheckCircle, XCircle, MessageSquare, Calendar, RefreshCw, GripVertical } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
async function get<T>(path: string): Promise<T> { const r = await fetch(`${BASE}${path}`); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function post<T>(path: string, body?: any): Promise<T> { const r = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); if (!r.ok) throw new Error(await r.text()); return r.json(); }

const DEAL_STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost'] as const;
const STAGE_LABELS: Record<string, string> = { lead: 'Lead', qualified: 'Qualified', proposal: 'Proposal', negotiation: 'Negotiation', closed_won: 'Won', closed_lost: 'Lost' };
const STAGE_COLORS: Record<string, string> = { lead: 'var(--color-info)', qualified: 'var(--brand-500)', proposal: 'var(--color-warning)', negotiation: 'bg-orange-500', closed_won: 'var(--color-success)', closed_lost: 'var(--color-error)' };

function Skeleton({ h = 'h-12' }: { h?: string }) { return <div className={`skeleton ${h} w-full`} />; }
function StatusBadge({ status }: { status: string }) {
  const c: Record<string, string> = { new: 'badge-info', contacted: 'badge-warning', qualified: 'badge-brand', proposal: 'badge-brand', negotiation: 'badge-warning', won: 'badge-success', lost: 'badge-error' };
  return <span className={`badge ${c[status] || 'badge-info'}`}>{status}</span>;
}

export default function CRM() {
  const [tab, setTab] = useState<'pipeline' | 'contacts' | 'deals' | 'timeline'>('pipeline');
  const [contacts, setContacts] = useState<any[]>([]);
  const [deals, setDeals] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState<string | null>(null);
  const [contactForm, setContactForm] = useState({ name: '', email: '', phone: '', company: '' });
  const [dealForm, setDealForm] = useState({ title: '', value: 0, contact_id: '', stage: 'lead' });
  const [activityLog, setActivityLog] = useState<any[]>([]);
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, [tab]);

  async function loadAll() {
    setLoading(true);
    try {
      if (summary === null || tab === 'pipeline') { const s: any = await get('/crm/summary'); setSummary(s); }
      const d: any = await get('/crm/deals'); setDeals(d.deals || d || []);
    } catch { /* silent */ }
    setLoading(false);
  }

  function addActivity(action: string, detail: string) {
    setActivityLog(a => [{ time: Date.now(), action, detail }, ...a.slice(0, 49)]);
  }

  async function handleAddContact() {
    try { await post('/crm/contacts', contactForm); setContactForm({ name: '', email: '', phone: '', company: '' }); addToast('Contact added', 'success'); addActivity('contact_added', contactForm.name); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleAddDeal() {
    try { await post('/crm/deals', dealForm); setDealForm({ title: '', value: 0, contact_id: '', stage: 'lead' }); addToast('Deal added', 'success'); addActivity('deal_created', dealForm.title); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleStageChange(dealId: string, newStage: string) {
    try { await post('/crm/deals/stage', { deal_id: dealId, stage: newStage }); addToast(`Moved to ${STAGE_LABELS[newStage]}`, 'success'); addActivity('stage_change', `${dealId} → ${STAGE_LABELS[newStage]}`); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleDeleteDeal(dealId: string) {
    try { await fetch(`${BASE}/crm/deals/${dealId}`, { method: 'DELETE' }); addToast('Deal deleted', 'success'); addActivity('deal_deleted', dealId); loadAll(); } catch { addToast('Delete failed', 'error'); }
  }

  function onDragStart(dealId: string) { setDragging(dealId); }
  function onDrop(targetStage: string) { if (dragging) handleStageChange(dragging, targetStage); setDragging(null); }

  const tabs = [
    { id: 'pipeline' as const, label: 'Pipeline', icon: TrendingUp },
    { id: 'contacts' as const, label: 'Contacts', icon: UserPlus },
    { id: 'timeline' as const, label: 'Timeline', icon: Clock },
  ];

  const stageDeals = (stage: string) => deals.filter((d: any) => d.stage === stage).length;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">CRM</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Sales pipeline, contacts, deals, and activity timeline</p></div>
      </div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {/* PIPELINE TAB — Drag & Drop Columns */}
        {tab === 'pipeline' && (
          <div className="space-y-6">
            {summary && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {[{l:'Pipeline',v:summary.total_deals||0,c:'var(--brand-500)'},{l:'Won',v:summary.won||0,c:'var(--color-success)'},{l:'Revenue',v:`$${(summary.revenue||0).toLocaleString()}`,c:'var(--color-success)'},{l:'Conversion',v:`${Math.round(summary.conversion_rate||0)}%`,c:'var(--color-warning)'},{l:'Avg Deal',v:`$${Math.round(summary.avg_deal||0).toLocaleString()}`,c:'var(--color-info)'}].map(s => <div key={s.l} className="bg-[var(--bg-tertiary)] rounded-xl p-4"><p className="text-2xs text-[var(--text-tertiary)] uppercase">{s.l}</p><p className="text-xl font-bold mt-1" style={{color:s.c}}>{s.v}</p></div>)}
              </div>
            )}

            {/* Drag & Drop Pipeline Columns */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {DEAL_STAGES.map(stage => (
                <div key={stage} className="bg-[var(--bg-tertiary)] rounded-xl p-3 min-h-[200px] border-2 border-transparent hover:border-[var(--border-brand)] transition-colors"
                  onDragOver={e => e.preventDefault()}
                  onDrop={() => onDrop(stage)}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold" style={{color: STAGE_COLORS[stage]}}>{STAGE_LABELS[stage]}</span>
                    <span className="text-2xs text-[var(--text-tertiary)]">{stageDeals(stage)}</span>
                  </div>
                  <div className="space-y-2">
                    {deals.filter((d: any) => d.stage === stage).map((d: any) => (
                      <div key={d.id || d._id} className="bg-[var(--bg-elevated)] rounded-lg p-2 border border-[var(--border-primary)] cursor-grab hover:border-[var(--border-brand)] transition-colors"
                        draggable onDragStart={() => onDragStart(d.id || d._id)}>
                        <div className="text-xs font-medium truncate">{d.title}</div>
                        <div className="flex items-center justify-between mt-1">
                          <span className="text-2xs text-[var(--color-success)] font-medium">${d.value?.toLocaleString?.() || d.value || 0}</span>
                          <button onClick={() => handleDeleteDeal(d.id || d._id)} className="text-red-400 hover:text-red-300"><XCircle className="w-3 h-3" /></button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Quick Deal Form */}
            <Card><div className="p-4 space-y-4">
              <h2 className="text-sm font-semibold">New Deal</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                <div className="input-group"><label className="input-label">Title</label><input className="input" value={dealForm.title} onChange={e => setDealForm(p => ({...p, title: e.target.value}))} placeholder="Website redesign" /></div>
                <div className="input-group"><label className="input-label">Value ($)</label><input className="input" type="number" value={dealForm.value} onChange={e => setDealForm(p => ({...p, value: +e.target.value}))} /></div>
                <button onClick={handleAddDeal} className="btn btn-primary"><Plus className="w-4 h-4" /> Add Deal</button>
              </div>
            </div></Card>
          </div>
        )}

        {/* CONTACTS TAB */}
        {tab === 'contacts' && (
          <div className="space-y-6">
            <Card><div className="p-4 space-y-4">
              <h2 className="text-sm font-semibold">Add Contact</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                <div className="input-group"><label className="input-label">Name</label><input className="input" value={contactForm.name} onChange={e => setContactForm(p => ({...p, name: e.target.value}))} placeholder="John Doe" /></div>
                <div className="input-group"><label className="input-label">Email</label><input className="input" value={contactForm.email} onChange={e => setContactForm(p => ({...p, email: e.target.value}))} placeholder="john@example.com" /></div>
                <div className="input-group"><label className="input-label">Phone</label><input className="input" value={contactForm.phone} onChange={e => setContactForm(p => ({...p, phone: e.target.value}))} /></div>
                <button onClick={handleAddContact} className="btn btn-primary"><UserPlus className="w-4 h-4" /> Add</button>
              </div>
            </div></Card>
            <div className="text-center py-12 text-[var(--text-tertiary)]"><UserPlus className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>Contacts are managed via the CRM API</p><p className="text-xs mt-1">Use the form above or POST /crm/contacts</p></div>
          </div>
        )}

        {/* TIMELINE TAB */}
        {tab === 'timeline' && (
          <div className="space-y-4">
            {activityLog.length === 0 ? (
              <div className="text-center py-12 text-[var(--text-tertiary)]"><Clock className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No activity yet</p><p className="text-xs mt-1">Activity is tracked as you add deals and change stages</p></div>
            ) : (
              <div className="relative pl-6 border-l-2 border-[var(--border-brand)] ml-3 space-y-4">
                {activityLog.map((a, i) => (
                  <div key={i} className="relative">
                    <div className="absolute -left-[25px] w-3 h-3 rounded-full bg-[var(--brand-500)] border-2 border-[var(--bg-primary)]" />
                    <div className="bg-[var(--bg-tertiary)] rounded-xl p-3">
                      <div className="flex items-center justify-between"><span className="text-xs font-medium">{a.action}</span><span className="text-2xs text-[var(--text-tertiary)]">{new Date(a.time).toLocaleTimeString()}</span></div>
                      <p className="text-xs text-[var(--text-secondary)] mt-0.5">{a.detail}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
