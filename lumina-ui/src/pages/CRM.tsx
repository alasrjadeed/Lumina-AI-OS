import { useEffect, useState } from 'react';
import { api } from '../api';
import {
  BarChart3, Plus, User, DollarSign, TrendingUp, Target,
  CheckCircle, XCircle, Search, Phone, Mail, Building2,
  Tag, Calendar, ArrowUpRight, Clock, Filter,
  Edit3, Trash2, RefreshCw, Activity, Zap, Users, ChevronDown,
} from 'lucide-react';

interface Contact { id: string; name: string; email: string; phone?: string; company?: string; }
interface Deal { id: string; title: string; value: number; stage: string; contact_id?: string; }
interface Summary { total_deals: number; total_contacts: number; total_value: number; won_value: number; pipeline_value: number; conversion_rate: string; }

const STAGES = [
  { key: 'lead', label: 'Lead', color: 'bg-slate-500' },
  { key: 'qualified', label: 'Qualified', color: 'bg-blue-500' },
  { key: 'proposal', label: 'Proposal', color: 'bg-violet-500' },
  { key: 'negotiation', label: 'Negotiation', color: 'bg-amber-500' },
  { key: 'closed_won', label: 'Won', color: 'bg-emerald-500' },
  { key: 'closed_lost', label: 'Lost', color: 'bg-red-500' },
];

export default function CRM() {
  const [tab, setTab] = useState('pipeline');
  const [summary, setSummary] = useState<Summary | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [contactSearch, setContactSearch] = useState('');
  const [showAddContact, setShowAddContact] = useState(false);
  const [showAddDeal, setShowAddDeal] = useState(false);
  const [newName, setNewName] = useState(''); const [newEmail, setNewEmail] = useState(''); const [newPhone, setNewPhone] = useState(''); const [newCompany, setNewCompany] = useState('');
  const [dealTitle, setDealTitle] = useState(''); const [dealValue, setDealValue] = useState(''); const [dealStage, setDealStage] = useState('lead');
  const [dragging, setDragging] = useState<string | null>(null);

  const fetchData = () => {
    api.crmSummary().then(setSummary).catch(() => {});
    api.listContacts().then(d => setContacts(d.contacts)).catch(() => {});
    api.listDeals().then(d => setDeals(d.deals)).catch(() => {});
  };
  useEffect(fetchData, []);

  const addContact = async () => {
    if (!newName.trim()) return;
    await api.addContact(newName, newEmail);
    setNewName(''); setNewEmail(''); setNewPhone(''); setNewCompany(''); setShowAddContact(false);
    fetchData();
  };

  const addDeal = async () => {
    if (!dealTitle.trim()) return;
    await api.addDeal(dealTitle, parseFloat(dealValue) || 0, '');
    setDealTitle(''); setDealValue(''); setShowAddDeal(false);
    fetchData();
  };

  const moveStage = async (dealId: string, newStage: string) => {
    try {
      await fetch('/api/crm/deals/stage', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ deal_id: dealId, stage: newStage }) });
      fetchData();
    } catch {}
  };

  const filteredContacts = contacts.filter(c =>
    c.name.toLowerCase().includes(contactSearch.toLowerCase()) ||
    c.email.toLowerCase().includes(contactSearch.toLowerCase())
  );

  const totalValue = deals.reduce((a, d) => a + d.value, 0);
  const wonValue = deals.filter(d => d.stage === 'closed_won').reduce((a, d) => a + d.value, 0);

  const tabs = [
    { id: 'pipeline', label: 'Pipeline', icon: Activity },
    { id: 'contacts', label: 'Contacts', icon: Users },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3"><BarChart3 className="w-6 h-6 text-lumina-400" /> CRM</h1>
          <p className="text-sm text-slate-400 mt-0.5">Sales pipeline & customer management</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-slate-400">{deals.length} deals · {contacts.length} contacts</div>
          <button onClick={fetchData} className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200 transition-all"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard icon={DollarSign} label="Total Value" value={`$${totalValue.toLocaleString()}`} color="lumina" />
        <StatCard icon={TrendingUp} label="Won" value={`$${wonValue.toLocaleString()}`} color="emerald" />
        <StatCard icon={Target} label="Conversion" value={summary?.conversion_rate || '0%'} color="violet" />
        <StatCard icon={Users} label="Contacts" value={String(contacts.length)} color="blue" />
        <StatCard icon={Activity} label="Deals" value={String(deals.length)} color="amber" />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/5 pb-1">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm rounded-t-xl transition-all capitalize ${
              tab === t.id ? 'bg-white/5 text-lumina-300 border-b-2 border-lumina-500 font-medium' : 'text-slate-500 hover:text-slate-300'
            }`}><t.icon className="w-4 h-4" />{t.label}</button>
        ))}
        <div className="ml-auto flex gap-2">
          <button onClick={() => setShowAddDeal(true)} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-4 py-2 text-xs font-medium flex items-center gap-1.5 transition-all"><Plus className="w-3.5 h-3.5" /> Deal</button>
          <button onClick={() => setShowAddContact(true)} className="bg-white/5 hover:bg-white/10 text-slate-300 rounded-xl px-4 py-2 text-xs flex items-center gap-1.5 transition-all"><Plus className="w-3.5 h-3.5" /> Contact</button>
        </div>
      </div>

      {/* Add Deal Modal */}
      {showAddDeal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setShowAddDeal(false)}>
          <div className="bg-slate-900 rounded-2xl border border-white/10 p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white">New Deal</h3>
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Deal title" value={dealTitle} onChange={e => setDealTitle(e.target.value)} />
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Value ($)" type="number" value={dealValue} onChange={e => setDealValue(e.target.value)} />
            <select className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" value={dealStage} onChange={e => setDealStage(e.target.value)}>
              {STAGES.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
            <div className="flex gap-3">
              <button onClick={addDeal} className="flex-1 bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl py-2.5 text-sm font-medium">Create Deal</button>
              <button onClick={() => setShowAddDeal(false)} className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl py-2.5 text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Add Contact Modal */}
      {showAddContact && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={() => setShowAddContact(false)}>
          <div className="bg-slate-900 rounded-2xl border border-white/10 p-6 w-full max-w-md space-y-4" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white">New Contact</h3>
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Full name *" value={newName} onChange={e => setNewName(e.target.value)} />
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Email" value={newEmail} onChange={e => setNewEmail(e.target.value)} />
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Phone" value={newPhone} onChange={e => setNewPhone(e.target.value)} />
            <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Company" value={newCompany} onChange={e => setNewCompany(e.target.value)} />
            <div className="flex gap-3">
              <button onClick={addContact} className="flex-1 bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl py-2.5 text-sm font-medium">Add Contact</button>
              <button onClick={() => setShowAddContact(false)} className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl py-2.5 text-sm">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* ─── PIPELINE KANBAN ─── */}
      {tab === 'pipeline' && (
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-3 min-h-[500px]">
          {STAGES.map(stage => {
            const stageDeals = deals.filter(d => d.stage === stage.key);
            const stageTotal = stageDeals.reduce((a, d) => a + d.value, 0);
            return (
              <div key={stage.key} className="bento-card p-3 flex flex-col min-h-[400px]">
                <div className="flex items-center justify-between mb-3 shrink-0">
                  <div className="flex items-center gap-2">
                    <div className={`w-2.5 h-2.5 rounded-full ${stage.color}`} />
                    <span className="text-xs font-semibold text-slate-300 uppercase">{stage.label}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 bg-white/5 px-2 py-0.5 rounded-full">{stageDeals.length}</span>
                </div>
                <div className="flex-1 space-y-2 overflow-y-auto min-h-[200px]"
                  onDragOver={e => e.preventDefault()}
                  onDrop={e => { const id = e.dataTransfer.getData('dealId'); if (id) moveStage(id, stage.key); }}>
                  {stageDeals.map(deal => (
                    <div key={deal.id} draggable
                      onDragStart={e => e.dataTransfer.setData('dealId', deal.id)}
                      className="bg-white/5 rounded-xl p-3 border border-white/5 hover:border-lumina-500/30 cursor-grab active:cursor-grabbing transition-all group">
                      <p className="text-sm font-medium text-slate-200 truncate">{deal.title}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs font-semibold text-lumina-400">${deal.value.toLocaleString()}</span>
                        <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-all">
                          <button onClick={() => {
                            const idx = STAGES.findIndex(s => s.key === stage.key);
                            if (idx < STAGES.length - 1) moveStage(deal.id, STAGES[idx + 1].key);
                          }} className="p-1 rounded hover:bg-white/10 text-slate-400 hover:text-slate-200"><ChevronDown className="w-3 h-3" /></button>
                        </div>
                      </div>
                    </div>
                  ))}
                  {stageDeals.length === 0 && (
                    <div className="text-center py-8 text-xs text-slate-600 border border-dashed border-white/5 rounded-xl">Drop deals here</div>
                  )}
                </div>
                {stageTotal > 0 && <div className="mt-2 pt-2 border-t border-white/5 text-[10px] text-slate-500 shrink-0">${stageTotal.toLocaleString()}</div>}
              </div>
            );
          })}
        </div>
      )}

      {/* ─── CONTACTS ─── */}
      {tab === 'contacts' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bento-card">
            <div className="flex items-center gap-3 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Search contacts..." value={contactSearch} onChange={e => setContactSearch(e.target.value)} />
              </div>
            </div>
            <div className="space-y-2">
              {filteredContacts.map(c => (
                <div key={c.id} className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-all group">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center text-white text-sm font-bold">{c.name[0]}</div>
                    <div>
                      <p className="text-sm font-medium text-slate-200">{c.name}</p>
                      <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5">
                        <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{c.email}</span>
                        {c.phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{c.phone}</span>}
                        {c.company && <span className="flex items-center gap-1"><Building2 className="w-3 h-3" />{c.company}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              {filteredContacts.length === 0 && <p className="text-sm text-slate-500 text-center py-8">No contacts found</p>}
            </div>
          </div>
          <div className="bento-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Quick Stats</h3>
            <div className="space-y-4">
              <div><p className="text-xs text-slate-400">Total Contacts</p><p className="text-2xl font-bold text-white">{contacts.length}</p></div>
              <div className="h-px bg-white/5" />
              <div><p className="text-xs text-slate-400">With Email</p><p className="text-lg font-semibold text-white">{contacts.filter(c => c.email).length}</p></div>
              <div><p className="text-xs text-slate-400">With Phone</p><p className="text-lg font-semibold text-white">{contacts.filter(c => c.phone).length}</p></div>
              <div><p className="text-xs text-slate-400">With Company</p><p className="text-lg font-semibold text-white">{contacts.filter(c => c.company).length}</p></div>
            </div>
          </div>
        </div>
      )}

      {/* ─── ANALYTICS ─── */}
      {tab === 'analytics' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bento-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Pipeline Distribution</h3>
            <div className="space-y-3">
              {STAGES.map(stage => {
                const stageDeals = deals.filter(d => d.stage === stage.key);
                const pct = totalValue > 0 ? (stageDeals.reduce((a, d) => a + d.value, 0) / totalValue * 100) : 0;
                return (
                  <div key={stage.key}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-400">{stage.label}</span>
                      <span className="text-slate-300 font-medium">${stageDeals.reduce((a, d) => a + d.value, 0).toLocaleString()} ({pct.toFixed(0)}%)</span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full transition-all duration-500 ${stage.color}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          <div className="bento-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Deal Summary</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                <div><p className="text-xs text-slate-400">Won</p><p className="text-lg font-bold text-emerald-400">{deals.filter(d => d.stage === 'closed_won').length}</p></div>
                <DollarSign className="w-8 h-8 text-emerald-400/50" />
              </div>
              <div className="flex items-center justify-between p-4 rounded-xl bg-red-500/5 border border-red-500/10">
                <div><p className="text-xs text-slate-400">Lost</p><p className="text-lg font-bold text-red-400">{deals.filter(d => d.stage === 'closed_lost').length}</p></div>
                <XCircle className="w-8 h-8 text-red-400/50" />
              </div>
              <div className="flex items-center justify-between p-4 rounded-xl bg-lumina-500/5 border border-lumina-500/10">
                <div><p className="text-xs text-slate-400">Active</p><p className="text-lg font-bold text-lumina-400">{deals.filter(d => !['closed_won','closed_lost'].includes(d.stage)).length}</p></div>
                <Activity className="w-8 h-8 text-lumina-400/50" />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: string; color: string }) {
  const colors: Record<string, string> = {
    lumina: 'from-lumina-500 to-lumina-700 shadow-lumina-500/10',
    emerald: 'from-emerald-500 to-emerald-700 shadow-emerald-500/10',
    violet: 'from-violet-500 to-violet-700 shadow-violet-500/10',
    blue: 'from-blue-500 to-blue-700 shadow-blue-500/10',
    amber: 'from-amber-500 to-amber-700 shadow-amber-500/10',
  };
  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${colors[color] || colors.lumina} p-[1px] transition-all duration-300 hover:scale-[1.02]`}>
      <div className="rounded-2xl bg-slate-950/90 backdrop-blur-sm p-4">
        <div className="flex items-start justify-between">
          <div><p className="text-[10px] font-medium text-white/60 uppercase tracking-wider">{label}</p><p className="text-sm font-bold text-white mt-1">{value}</p></div>
          <Icon className="w-6 h-6 text-white/30" />
        </div>
      </div>
    </div>
  );
}
