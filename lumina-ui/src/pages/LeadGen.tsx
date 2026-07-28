import { useState, useEffect } from 'react';
import { UserPlus, Globe, Search, Trash2, Download, Upload, RefreshCw, Target, Activity, ExternalLink, Sparkles, Send, MessageCircle, Brain, FileText, Zap } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
async function get<T>(path: string): Promise<T> { const r = await fetch(`${BASE}${path}`); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function post<T>(path: string, body?: any): Promise<T> { const r = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); if (!r.ok) throw new Error(await r.text()); return r.json(); }

function SkeletonLine({ className = '' }: { className?: string }) { return <div className={`skeleton ${className}`} />; }
function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = { new: 'bg-blue-500/20 text-blue-300 border-blue-500/30', contacted: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30', qualified: 'bg-purple-500/20 text-purple-300 border-purple-500/30', proposal: 'bg-orange-500/20 text-orange-300 border-orange-500/30', negotiation: 'bg-pink-500/20 text-pink-300 border-pink-500/30', won: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30', lost: 'bg-red-500/20 text-red-300 border-red-500/30', healthy: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30', failing: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30', disabled: 'bg-red-500/20 text-red-300 border-red-500/30', hot: 'bg-red-500/20 text-red-300 border-red-500/30', warm: 'bg-amber-500/20 text-amber-300 border-amber-500/30', cold: 'bg-slate-500/20 text-slate-400 border-slate-500/30' };
  return <span className={`px-2 py-0.5 rounded-full text-2xs font-medium border ${colors[status] || colors.cold}`}>{status}</span>;
}

export default function LeadGen() {
  const [tab, setTab] = useState<'generate' | 'leads' | 'outreach' | 'categories' | 'health'>('generate');
  const [keyword, setKeyword] = useState(''); const [location, setLocation] = useState('Bahrain'); const [limit, setLimit] = useState(10);
  const [generating, setGenerating] = useState(false); const [genResult, setGenResult] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]); const [leadsTotal, setLeadsTotal] = useState(0); const [leadsLoading, setLeadsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState(''); const [searchQuery, setSearchQuery] = useState('');
  const [categories, setCategories] = useState<any[]>([]); const [catLoading, setCatLoading] = useState(true);
  const [health, setHealth] = useState<any>(null); const [analytics, setAnalytics] = useState<any>(null);
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
  const [scoringLead, setScoringLead] = useState<string | null>(null);
  const [draftLead, setDraftLead] = useState<string | null>(null);
  const [emailDraft, setEmailDraft] = useState(''); const [waDraft, setWaDraft] = useState('');
  const [outreachLang, setOutreachLang] = useState('en');
  const { addToast } = useToast();

  useEffect(() => { loadLeads(); loadCategories(); loadDashboard(); }, [tab]);
  useEffect(() => { loadLeads(); }, [statusFilter]);

  async function loadDashboard() { try { const d = await get('/lead-gen/dashboard'); setHealth(d.scraper_health); setAnalytics(d.analytics); } catch {} }
  async function loadLeads() {
    setLeadsLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (searchQuery) params.set('search', searchQuery);
      params.set('limit', '100');
      const d = await get(`/lead-gen/leads?${params}`);
      setLeads(d.leads || []); setLeadsTotal(d.total || 0);
    } catch {} setLeadsLoading(false);
  }
  async function loadCategories() { setCatLoading(true); try { setCategories((await get('/lead-gen/categories')).categories || []); } catch {} setCatLoading(false); }

  async function handleGenerate(bulk = false) {
    if (!keyword.trim()) { addToast('Enter a keyword', 'error'); return; }
    setGenerating(true); setGenResult(null);
    try {
      const endpoint = bulk ? '/lead-gen/bulk-generate' : '/lead-gen/generate';
      const result = await post(endpoint, { keyword: keyword.trim(), location: location.trim(), limit, category_name: '' });
      setGenResult(result);
      addToast(`Found ${result.raw_leads_found} leads, saved ${result.leads_saved}`, 'success');
      loadLeads(); loadDashboard();
    } catch (e: any) { addToast(e.message || 'Generation failed', 'error'); }
    setGenerating(false);
  }

  async function handleDelete(leadId: string) { try { await fetch(`${BASE}/lead-gen/leads/${leadId}`, { method: 'DELETE' }); addToast('Deleted', 'success'); loadLeads(); } catch { addToast('Delete failed', 'error'); } }
  async function handleBulkDelete() {
    if (selectedLeads.size === 0) { addToast('Select leads first', 'error'); return; }
    try { await post('/lead-gen/bulk-delete-leads', Array.from(selectedLeads)); addToast(`Deleted ${selectedLeads.size} leads`, 'success'); setSelectedLeads(new Set()); loadLeads(); } catch { addToast('Bulk delete failed', 'error'); }
  }
  async function handleBulkStatus(status: string) {
    if (selectedLeads.size === 0) { addToast('Select leads first', 'error'); return; }
    try { await post(`/lead-gen/bulk-update-status?status=${status}`, Array.from(selectedLeads)); addToast(`Updated ${selectedLeads.size} leads to ${status}`, 'success'); setSelectedLeads(new Set()); loadLeads(); } catch { addToast('Bulk update failed', 'error'); }
  }
  async function handleAIScore(leadId: string) {
    setScoringLead(leadId);
    try { const r = await post(`/lead-gen/leads/${leadId}/ai-score`); addToast(`Scored: ${r.lead_score} (${r.tier})`, 'success'); loadLeads(); } catch { addToast('Scoring failed', 'error'); }
    setScoringLead(null);
  }
  async function handleGenerateDrafts(leadId: string) {
    setDraftLead(leadId); setEmailDraft(''); setWaDraft('');
    try {
      const emailR = await post('/lead-gen/generate-email-draft', { lead_id: leadId, language: outreachLang });
      setEmailDraft(emailR.draft);
      const waR = await post('/lead-gen/generate-whatsapp-draft', { lead_id: leadId, language: outreachLang });
      setWaDraft(waR.draft);
    } catch { addToast('Draft generation failed', 'error'); }
    setDraftLead(null);
  }
  async function handleSendOutreach(leadId: string, channel: string) {
    if (channel === 'email' && emailDraft) {
      try { await post('/lead-gen/send-outreach-email', { lead_id: leadId, subject: 'Partnership Opportunity', message: emailDraft }); addToast('Email queued', 'success'); } catch { addToast('Failed', 'error'); }
    }
    if (channel === 'whatsapp') {
      const lead = leads.find(l => l.id === leadId);
      if (lead?.phone) window.open(`https://wa.me/${lead.phone.replace(/[^0-9]/g, '')}`, '_blank');
    }
  }

  const tabs = [
    { id: 'generate' as const, label: 'Generate', icon: Target },
    { id: 'leads' as const, label: 'Leads', icon: UserPlus },
    { id: 'outreach' as const, label: 'Outreach', icon: Send },
    { id: 'categories' as const, label: 'Categories', icon: Globe },
    { id: 'health' as const, label: 'Health', icon: Activity },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Lead Generation</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">AI-powered discovery · 37 platforms · AI scoring & outreach</p></div>
        <div className="flex items-center gap-2">
          <a href="/demo.html" target="_blank" className="btn btn-ghost btn-sm"><ExternalLink className="w-3.5 h-3.5" /> Demo</a>
          <button onClick={() => window.open(`${BASE}/lead-gen/export-csv`, '_blank')} className="btn btn-ghost btn-sm"><Download className="w-3.5 h-3.5" /> CSV</button>
          <button onClick={() => window.open(`${BASE}/lead-gen/export-vcard`, '_blank')} className="btn btn-ghost btn-sm"><Download className="w-3.5 h-3.5" /> vCard</button>
        </div>
      </div>

      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto">
        {/* GENERATE TAB */}
        {tab === 'generate' && (
          <div className="p-6 space-y-6">
            <Card><div className="p-6">
              <h2 className="text-lg font-semibold mb-4">Generate Leads</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="input-group"><label className="input-label">Keyword</label><input className="input" value={keyword} onChange={e => setKeyword(e.target.value)} placeholder='e.g. "restaurants", "construction"' /></div>
                <div className="input-group"><label className="input-label">Location</label><select className="select" value={location} onChange={e => setLocation(e.target.value)}>
                  {['Bahrain','Saudi Arabia','UAE','Qatar','Kuwait','Oman','Egypt','Jordan','Lebanon','Pakistan','India'].map(c => <option key={c} value={c}>{c}</option>)}
                </select></div>
                <div className="input-group"><label className="input-label">Limit</label><input className="input" type="number" value={limit} onChange={e => setLimit(+e.target.value)} min={1} max={100} /></div>
              </div>
              <div className="flex items-center gap-3">
                <button onClick={() => handleGenerate(false)} disabled={generating} className="btn btn-primary">{generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />} Targeted Generate</button>
                <button onClick={() => handleGenerate(true)} disabled={generating} className="btn btn-secondary">{generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />} Bulk Generate</button>
              </div>
            </div></Card>
            {genResult && (
              <Card><div className="p-6">
                <h3 className="text-sm font-semibold mb-4">Results</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  {[{l:'Platforms',v:genResult.platforms_used},{l:'Found',v:genResult.raw_leads_found,c:'var(--color-success)'},{l:'Saved',v:genResult.leads_saved,c:'var(--brand-500)'},{l:'Source',v:genResult.uses_ai_fallback?'AI':'Live'}].map(s => <div key={s.l} className="bg-[var(--bg-tertiary)] rounded-xl p-3"><p className="text-2xs text-[var(--text-tertiary)]">{s.l}</p><p className="text-lg font-bold mt-0.5" style={{color:s.c||'var(--text-primary)'}}>{s.v}</p></div>)}
                </div>
                {genResult.platforms_results && <details><summary className="text-xs text-[var(--text-secondary)] cursor-pointer">Per-platform results</summary><div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2">{Object.entries(genResult.platforms_results).map(([p,c]) => <div key={p} className="flex justify-between bg-[var(--bg-tertiary)] rounded px-2 py-1 text-xs"><span className="text-[var(--text-secondary)]">{p}</span><span>{c as number}</span></div>)}</div></details>}
              </div></Card>
            )}
            {analytics && (
              <Card><div className="p-6">
                <h3 className="text-sm font-semibold mb-4">Analytics</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {[{l:'Total',v:analytics.total_leads},{l:'Avg Score',v:Math.round(analytics.avg_score),c:'var(--brand-500)'},{l:'Conversion',v:`${Math.round(analytics.conversion_rate)}%`,c:'var(--color-success)'},{l:'Healthy',v:health?.healthy||0,c:'var(--color-success)'},{l:'Disabled',v:health?.disabled||0,c:'var(--color-error)'}].map(s => <div key={s.l} className="bg-[var(--bg-tertiary)] rounded-xl p-3"><p className="text-2xs text-[var(--text-tertiary)]">{s.l}</p><p className="text-lg font-bold mt-0.5" style={{color:s.c||'var(--text-primary)'}}>{s.v}</p></div>)}
                </div>
              </div></Card>
            )}
          </div>
        )}

        {/* LEADS TAB */}
        {tab === 'leads' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold">{leadsTotal} Leads</h2>
                <select className="select w-auto" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                  <option value="">All</option><option value="new">New</option><option value="contacted">Contacted</option><option value="qualified">Qualified</option><option value="proposal">Proposal</option><option value="negotiation">Negotiation</option><option value="won">Won</option><option value="lost">Lost</option>
                </select>
                <div className="relative"><Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" /><input className="input pl-8 w-48" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && loadLeads()} placeholder="Search..." /></div>
              </div>
              <div className="flex items-center gap-2">
                {selectedLeads.size > 0 && (
                  <>
                    <button onClick={() => handleBulkStatus('contacted')} className="btn btn-ghost btn-sm">Contacted</button>
                    <button onClick={() => handleBulkStatus('qualified')} className="btn btn-ghost btn-sm">Qualify</button>
                    <button onClick={handleBulkDelete} className="btn btn-ghost btn-sm text-red-400"><Trash2 className="w-3.5 h-3.5" /> {selectedLeads.size}</button>
                  </>
                )}
                <button onClick={loadLeads} className="btn btn-ghost btn-sm"><RefreshCw className="w-3.5 h-3.5" /></button>
              </div>
            </div>
            {leadsLoading ? <div className="space-y-2">{Array(5).fill(0).map((_,i) => <SkeletonLine key={i} className="h-12 w-full" />)}</div>
            : leads.length === 0 ? <div className="text-center py-12 text-[var(--text-tertiary)]"><UserPlus className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No leads yet</p></div>
            : <div className="space-y-1">
              {leads.map((lead: any) => (
                <div key={lead.id} className="flex items-center gap-3 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] rounded-xl px-4 py-3 transition-colors group">
                  <input type="checkbox" checked={selectedLeads.has(lead.id)} onChange={() => { const n = new Set(selectedLeads); n.has(lead.id) ? n.delete(lead.id) : n.add(lead.id); setSelectedLeads(n); }} className="w-3.5 h-3.5 rounded accent-[var(--brand-500)]" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium truncate">{lead.business_name}</span>
                      <StatusBadge status={lead.status} />
                      {lead.score_tier && <StatusBadge status={lead.score_tier} />}
                      {lead.lead_type && lead.lead_type !== 'unknown' && <span className="text-2xs text-[var(--text-tertiary)]">{lead.lead_type}</span>}
                    </div>
                    <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                      {lead.email && <span className="text-xs text-[var(--text-secondary)]">📧 {lead.email}</span>}
                      {lead.phone && <span className="text-xs text-[var(--text-secondary)]">📞 {lead.phone}</span>}
                      {lead.website && <span className="text-xs text-[var(--text-brand)] truncate">🌐 {lead.website}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="text-xs text-[var(--text-tertiary)]">{lead.source}</span>
                    <span className="text-xs font-medium text-[var(--text-brand)]">⭐{lead.lead_score}</span>
                    <button onClick={() => handleAIScore(lead.id)} disabled={scoringLead === lead.id} className="btn btn-ghost btn-sm" title="AI Score">{scoringLead === lead.id ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Brain className="w-3 h-3" />}</button>
                    <button onClick={() => handleGenerateDrafts(lead.id)} className="btn btn-ghost btn-sm" title="Drafts"><FileText className="w-3 h-3" /></button>
                    {lead.phone && <a href={`https://wa.me/${(lead.phone||'').replace(/[^0-9]/g,'')}`} target="_blank" className="btn btn-ghost btn-sm text-green-400" title="WhatsApp"><MessageCircle className="w-3 h-3" /></a>}
                    <button onClick={() => handleDelete(lead.id)} className="btn btn-ghost btn-sm text-red-400"><Trash2 className="w-3 h-3" /></button>
                  </div>
                </div>
              ))}
            </div>}
          </div>
        )}

        {/* OUTREACH TAB */}
        {tab === 'outreach' && (
          <div className="p-6 space-y-6">
            <Card><div className="p-6">
              <h2 className="text-lg font-semibold mb-4">AI Outreach Generator</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="input-group"><label className="input-label">Lead</label><select className="select" value={draftLead || ''} onChange={e => { setDraftLead(e.target.value); if (e.target.value) handleGenerateDrafts(e.target.value); }}>
                  <option value="">Select lead</option>{leads.map(l => <option key={l.id} value={l.id}>{l.business_name} ({l.email || 'no email'})</option>)}
                </select></div>
                <div className="input-group"><label className="input-label">Language</label><select className="select" value={outreachLang} onChange={e => { setOutreachLang(e.target.value); if (draftLead) handleGenerateDrafts(draftLead); }}>
                  <option value="en">English</option><option value="ar">Arabic</option>
                </select></div>
              </div>

              {draftLead && (
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2"><h3 className="text-sm font-semibold">Email Draft</h3><button onClick={() => handleSendOutreach(draftLead!, 'email')} className="btn btn-primary btn-sm"><Send className="w-3 h-3" /> Send Email</button></div>
                    <textarea className="input h-32 font-mono text-xs" value={emailDraft} onChange={e => setEmailDraft(e.target.value)} />
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2"><h3 className="text-sm font-semibold">WhatsApp Draft</h3><button onClick={() => handleSendOutreach(draftLead!, 'whatsapp')} className="btn btn-secondary btn-sm"><MessageCircle className="w-3 h-3" /> Open WhatsApp</button></div>
                    <textarea className="input h-32 font-mono text-xs" value={waDraft} onChange={e => setWaDraft(e.target.value)} />
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleSendOutreach(draftLead!, 'email')} disabled={!emailDraft} className="btn btn-primary"><Send className="w-4 h-4" /> Send Email</button>
                    <button onClick={() => handleSendOutreach(draftLead!, 'whatsapp')} className="btn btn-secondary"><MessageCircle className="w-4 h-4" /> Send via WhatsApp</button>
                  </div>
                </div>
              )}
            </div></Card>
            <Card><div className="p-6">
              <h2 className="text-lg font-semibold mb-4">Import</h2>
              <div className="flex flex-wrap gap-3">
                <label className="btn btn-secondary cursor-pointer"><Upload className="w-4 h-4" /> Import CSV <input type="file" accept=".csv" className="hidden" onChange={async e => { const f = e.target.files?.[0]; if (!f) return; const fd = new FormData(); fd.append('file', f); try { const r = await fetch(`${BASE}/lead-gen/import-csv`, { method: 'POST', body: fd }); const d = await r.json(); addToast(`Imported ${d.saved} leads`, 'success'); loadLeads(); } catch { addToast('Import failed', 'error'); } }} /></label>
                <label className="btn btn-secondary cursor-pointer"><Upload className="w-4 h-4" /> Import vCard <input type="file" accept=".vcf" className="hidden" onChange={async e => { const f = e.target.files?.[0]; if (!f) return; const fd = new FormData(); fd.append('file', f); try { const r = await fetch(`${BASE}/lead-gen/import-vcard`, { method: 'POST', body: fd }); const d = await r.json(); addToast(`Imported ${d.saved} leads`, 'success'); loadLeads(); } catch { addToast('Import failed', 'error'); } }} /></label>
                <label className="btn btn-secondary cursor-pointer"><Upload className="w-4 h-4" /> Import WhatsApp Group <input type="file" accept=".csv" className="hidden" onChange={async e => { const f = e.target.files?.[0]; if (!f) return; const fd = new FormData(); fd.append('file', f); try { const r = await fetch(`${BASE}/lead-gen/import-whatsapp-group`, { method: 'POST', body: fd }); const d = await r.json(); addToast(`Imported ${d.saved} contacts`, 'success'); loadLeads(); } catch { addToast('Import failed', 'error'); } }} /></label>
              </div>
            </div></Card>
          </div>
        )}

        {/* CATEGORIES TAB */}
        {tab === 'categories' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-semibold">Categories</h2><button onClick={loadCategories} className="btn btn-ghost btn-sm"><RefreshCw className="w-3.5 h-3.5" /></button></div>
            {catLoading ? <div className="space-y-2">{Array(4).fill(0).map((_,i) => <SkeletonLine key={i} className="h-12" />)}</div>
            : categories.length === 0 ? <div className="text-center py-8 text-[var(--text-tertiary)]">No categories. Defaults will be created on first use.</div>
            : <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {categories.map((cat: any) => (
                <div key={cat.id} className="bg-[var(--bg-tertiary)] rounded-xl p-4 border border-[var(--border-primary)] hover:border-[var(--border-brand)] transition-colors">
                  <div className="flex items-center justify-between mb-2"><span className="text-sm font-medium">{cat.name}</span><span className="text-2xs text-[var(--text-tertiary)]">{cat.country_code}</span></div>
                  <div className="flex flex-wrap gap-1 mb-2">{cat.keywords?.slice(0,5).map((kw: string) => <span key={kw} className="badge badge-brand" style={{fontSize:'10px'}}>{kw}</span>)}</div>
                  <div className="flex items-center gap-3 text-2xs text-[var(--text-tertiary)]"><span>{cat.platforms?.length || 0} platforms</span><span>P{cat.priority}</span><span>{cat.active ? 'Active' : 'Inactive'}</span></div>
                </div>
              ))}
            </div>}
          </div>
        )}

        {/* HEALTH TAB */}
        {tab === 'health' && (
          <div className="p-6">
            <h2 className="text-lg font-semibold mb-4">Scraper Health</h2>
            {health ? <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card><div className="p-4">
                <h3 className="text-sm font-semibold mb-3">Summary</h3>
                <div className="grid grid-cols-3 gap-3">
                  {[['Healthy',health.healthy,'var(--color-success)'],[null,health.failing,'var(--color-warning)'],[null,health.disabled,'var(--color-error)']].map(([l,v,c]) => <div key={String(l)} className="bg-[var(--bg-tertiary)] rounded-xl p-3 text-center"><p className="text-2xl font-bold" style={{color:c as string}}>{v}</p><p className="text-2xs text-[var(--text-tertiary)]">{l}</p></div>)}
                </div>
              </div></Card>
              <Card><div className="p-4 max-h-64 overflow-y-auto">
                <h3 className="text-sm font-semibold mb-3">Per-Platform</h3>
                <div className="space-y-1">{health.details && Object.entries(health.details).map(([p,i]: [string, any]) => <div key={p} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-[var(--bg-hover)]"><span className="text-xs">{p}</span><div className="flex items-center gap-2"><span className="text-2xs text-[var(--text-tertiary)]">{i.success_rate}%</span><StatusBadge status={i.status} /></div></div>)}</div>
              </div></Card>
            </div> : <div className="text-center py-12 text-[var(--text-tertiary)]"><Activity className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No health data yet</p></div>}
          </div>
        )}
      </div>
    </div>
  );
}
