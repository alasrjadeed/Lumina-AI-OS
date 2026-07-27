import { useState, useEffect } from 'react';
import { UserPlus, Globe, Search, Plus, Trash2, Download, Upload, RefreshCw, Target, Activity, ChevronDown, Filter, AlertCircle, ExternalLink } from 'lucide-react';
import Card from '../components/ui/Card';
import { useApi, useApiMutation } from '../hooks/useApi';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function post<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function SkeletonLine({ className = '' }: { className?: string }) {
  return <div className={`bg-white/5 rounded animate-pulse ${className}`} />;
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    new: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    contacted: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    qualified: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
    proposal: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
    negotiation: 'bg-pink-500/20 text-pink-300 border-pink-500/30',
    won: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    lost: 'bg-red-500/20 text-red-300 border-red-500/30',
    healthy: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
    failing: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    disabled: 'bg-red-500/20 text-red-300 border-red-500/30',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${colors[status] || 'bg-slate-500/20 text-slate-300 border-slate-500/30'}`}>
      {status}
    </span>
  );
}

export default function LeadGen() {
  const [tab, setTab] = useState<'generate' | 'leads' | 'categories' | 'health'>('generate');
  const [keyword, setKeyword] = useState('');
  const [location, setLocation] = useState('Bahrain');
  const [limit, setLimit] = useState(10);
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [leadsTotal, setLeadsTotal] = useState(0);
  const [leadsLoading, setLeadsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [categories, setCategories] = useState<any[]>([]);
  const [catLoading, setCatLoading] = useState(true);
  const [health, setHealth] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [selectedLeads, setSelectedLeads] = useState<Set<string>>(new Set());
  const [showGenerate, setShowGenerate] = useState(false);
  const { addToast } = useToast();

  useEffect(() => { loadLeads(); loadCategories(); loadDashboard(); }, [tab]);
  useEffect(() => { loadLeads(); }, [statusFilter]);

  async function loadDashboard() {
    try {
      const data = await get('/lead-gen/dashboard');
      setHealth(data.scraper_health);
      setAnalytics(data.analytics);
    } catch { /* silent */ }
  }

  async function loadLeads() {
    setLeadsLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (searchQuery) params.set('search', searchQuery);
      params.set('limit', '100');
      const data = await get(`/lead-gen/leads?${params}`);
      setLeads(data.leads || []);
      setLeadsTotal(data.total || 0);
    } catch { /* silent */ }
    setLeadsLoading(false);
  }

  async function loadCategories() {
    setCatLoading(true);
    try {
      const data = await get('/lead-gen/categories');
      setCategories(data.categories || []);
    } catch { /* silent */ }
    setCatLoading(false);
  }

  async function handleGenerate(bulk = false) {
    if (!keyword.trim()) { addToast('Enter a keyword', 'error'); return; }
    setGenerating(true);
    setGenResult(null);
    try {
      const endpoint = bulk ? '/lead-gen/bulk-generate' : '/lead-gen/generate';
      const result = await post(endpoint, { keyword: keyword.trim(), location: location.trim(), limit, category_name: '' });
      setGenResult(result);
      addToast(`Found ${result.raw_leads_found} leads, saved ${result.leads_saved}`, 'success');
      loadLeads();
      loadDashboard();
    } catch (e: any) {
      addToast(e.message || 'Generation failed', 'error');
    }
    setGenerating(false);
  }

  async function handleDelete(leadId: string) {
    try {
      await fetch(`${BASE}/lead-gen/leads/${leadId}`, { method: 'DELETE' });
      addToast('Lead deleted', 'success');
      loadLeads();
    } catch { addToast('Delete failed', 'error'); }
  }

  async function handleBulkDelete() {
    if (selectedLeads.size === 0) { addToast('Select leads first', 'error'); return; }
    try {
      await post('/lead-gen/bulk-delete-leads', Array.from(selectedLeads));
      addToast(`Deleted ${selectedLeads.size} leads`, 'success');
      setSelectedLeads(new Set());
      loadLeads();
    } catch { addToast('Bulk delete failed', 'error'); }
  }

  async function handleExportCSV() {
    window.open(`${BASE}/lead-gen/export-csv`, '_blank');
  }

  async function handleExportVCard() {
    window.open(`${BASE}/lead-gen/export-vcard`, '_blank');
  }

  const tabs = [
    { id: 'generate' as const, label: 'Generate', icon: Target },
    { id: 'leads' as const, label: 'Leads', icon: UserPlus },
    { id: 'categories' as const, label: 'Categories', icon: Globe },
    { id: 'health' as const, label: 'Health', icon: Activity },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-white">Lead Generation</h1>
          <p className="text-sm text-slate-400 mt-0.5">AI-powered lead discovery across 37 platforms</p>
        </div>
        <div className="flex items-center gap-2">
          <a href="/demo.html" target="_blank" className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 rounded-lg transition-colors border border-indigo-500/20">
            <ExternalLink className="w-3.5 h-3.5" /> Demo Page
          </a>
          <button onClick={handleExportCSV} className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
            <Download className="w-3.5 h-3.5" /> CSV
          </button>
          <button onClick={handleExportVCard} className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
            <Download className="w-3.5 h-3.5" /> vCard
          </button>
        </div>
      </div>

      <div className="flex items-center gap-1 px-4 py-2 border-b border-white/5 shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${
              tab === t.id ? 'bg-indigo-500/15 text-indigo-300 border border-indigo-500/20' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto">
        {tab === 'generate' && (
          <div className="p-6 space-y-6">
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-white mb-4">Generate Leads</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1.5">Keyword / Industry</label>
                    <input value={keyword} onChange={e => setKeyword(e.target.value)}
                      placeholder='e.g. "restaurants", "construction", "salons"'
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 outline-none focus:border-indigo-500/50 transition-colors" />
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 mb-1.5">Location</label>
                    <select value={location} onChange={e => setLocation(e.target.value)}
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500/50 transition-colors">
                      <option value="Bahrain">Bahrain</option>
                      <option value="Saudi Arabia">Saudi Arabia</option>
                      <option value="UAE">UAE</option>
                      <option value="Qatar">Qatar</option>
                      <option value="Kuwait">Kuwait</option>
                      <option value="Oman">Oman</option>
                      <option value="Egypt">Egypt</option>
                      <option value="Jordan">Jordan</option>
                      <option value="Lebanon">Lebanon</option>
                      <option value="Pakistan">Pakistan</option>
                      <option value="India">India</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-slate-400 mb-1.5">Limit</label>
                    <input type="number" value={limit} onChange={e => setLimit(Number(e.target.value))} min={1} max={100}
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500/50 transition-colors" />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <button onClick={() => handleGenerate(false)} disabled={generating}
                    className="flex items-center gap-2 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 disabled:opacity-50 text-white text-sm rounded-lg transition-colors">
                    {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                    Targeted Generate
                  </button>
                  <button onClick={() => handleGenerate(true)} disabled={generating}
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 disabled:opacity-50 text-slate-300 text-sm rounded-lg border border-white/10 transition-colors">
                    <Globe className="w-4 h-4" />
                    Bulk Generate (All Platforms)
                  </button>
                </div>
              </div>
            </Card>

            {genResult && (
              <Card>
                <div className="p-6">
                  <h3 className="text-sm font-semibold text-white mb-4">Generation Results</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Platforms Used</p>
                      <p className="text-lg font-semibold text-white">{genResult.platforms_used}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Raw Leads Found</p>
                      <p className="text-lg font-semibold text-emerald-400">{genResult.raw_leads_found}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Leads Saved</p>
                      <p className="text-lg font-semibold text-indigo-400">{genResult.leads_saved}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">AI Fallback</p>
                      <p className="text-lg font-semibold text-slate-300">{genResult.uses_ai_fallback ? 'Yes' : 'No'}</p>
                    </div>
                  </div>
                  {genResult.platforms_results && Object.keys(genResult.platforms_results).length > 0 && (
                    <details className="mt-2">
                      <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300">Per-platform results</summary>
                      <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2">
                        {Object.entries(genResult.platforms_results).map(([p, c]) => (
                          <div key={p} className="flex items-center justify-between bg-slate-800/30 rounded px-2 py-1">
                            <span className="text-xs text-slate-400">{p}</span>
                            <span className="text-xs text-slate-300">{c as number}</span>
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              </Card>
            )}

            {analytics && (
              <Card>
                <div className="p-6">
                  <h3 className="text-sm font-semibold text-white mb-4">Lead Analytics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Total Leads</p>
                      <p className="text-lg font-semibold text-white">{analytics.total_leads}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Avg Score</p>
                      <p className="text-lg font-semibold text-indigo-400">{Math.round(analytics.avg_score)}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Conversion</p>
                      <p className="text-lg font-semibold text-emerald-400">{Math.round(analytics.conversion_rate)}%</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Healthy Scrapers</p>
                      <p className="text-lg font-semibold text-emerald-400">{health?.healthy || 0}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-3">
                      <p className="text-[10px] text-slate-500 uppercase">Disabled Scrapers</p>
                      <p className="text-lg font-semibold text-red-400">{health?.disabled || 0}</p>
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}

        {tab === 'leads' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-white">{leadsTotal} Leads</h2>
                <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
                  className="bg-slate-800 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none">
                  <option value="">All Statuses</option>
                  <option value="new">New</option>
                  <option value="contacted">Contacted</option>
                  <option value="qualified">Qualified</option>
                  <option value="proposal">Proposal</option>
                  <option value="negotiation">Negotiation</option>
                  <option value="won">Won</option>
                  <option value="lost">Lost</option>
                </select>
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                  <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && loadLeads()}
                    placeholder="Search leads..."
                    className="w-48 bg-slate-800 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder:text-slate-600 outline-none focus:border-indigo-500/50" />
                </div>
              </div>
              <div className="flex items-center gap-2">
                {selectedLeads.size > 0 && (
                  <button onClick={handleBulkDelete} className="flex items-center gap-1 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                    <Trash2 className="w-3.5 h-3.5" /> Delete ({selectedLeads.size})
                  </button>
                )}
                <button onClick={loadLeads} className="p-1.5 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {leadsLoading ? (
              <div className="space-y-2">
                {[...Array(5)].map((_, i) => <SkeletonLine key={i} className="h-12 w-full" />)}
              </div>
            ) : leads.length === 0 ? (
              <div className="text-center py-12 text-slate-500">
                <UserPlus className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No leads yet.</p>
                <p className="text-xs text-slate-600 mt-1">Generate leads from the Generate tab</p>
              </div>
            ) : (
              <div className="space-y-1">
                {leads.map((lead: any) => (
                  <div key={lead.id} className="flex items-center gap-3 bg-slate-800/30 hover:bg-slate-800/50 rounded-lg px-4 py-3 transition-colors group">
                    <input type="checkbox"
                      checked={selectedLeads.has(lead.id)}
                      onChange={() => {
                        const next = new Set(selectedLeads);
                        next.has(lead.id) ? next.delete(lead.id) : next.add(lead.id);
                        setSelectedLeads(next);
                      }}
                      className="w-3.5 h-3.5 rounded border-slate-600 bg-transparent" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white truncate">{lead.business_name}</span>
                        <StatusBadge status={lead.status} />
                        <span className="text-[10px] text-slate-600">{lead.lead_type}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-0.5">
                        {lead.email && <span className="text-xs text-slate-400">{lead.email}</span>}
                        {lead.phone && <span className="text-xs text-slate-400">{lead.phone}</span>}
                        {lead.website && <span className="text-xs text-indigo-400 truncate">{lead.website}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-xs text-slate-600">{lead.source}</span>
                      <span className="text-xs font-medium text-indigo-400">{lead.lead_score}</span>
                      <button onClick={() => handleDelete(lead.id)} className="p-1 text-slate-500 hover:text-red-400 transition-colors">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'categories' && (
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white">Lead Categories</h2>
              <button onClick={loadCategories} className="p-1.5 text-slate-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
            {catLoading ? (
              <div className="space-y-2">
                {[...Array(4)].map((_, i) => <SkeletonLine key={i} className="h-12 w-full" />)}
              </div>
            ) : categories.length === 0 ? (
              <div className="text-center py-8 text-slate-500 text-sm">No categories defined. Default categories will be created on first use.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {categories.map((cat: any) => (
                  <div key={cat.id} className="bg-slate-800/30 rounded-lg p-4 border border-white/5 hover:border-indigo-500/20 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-white">{cat.name}</span>
                      <span className="text-[10px] text-slate-500">{cat.country_code}</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mb-2">
                      {cat.keywords?.slice(0, 5).map((kw: string) => (
                        <span key={kw} className="px-1.5 py-0.5 bg-indigo-500/10 text-indigo-300 text-[10px] rounded">{kw}</span>
                      ))}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] text-slate-500">
                      <span>{cat.platforms?.length || 0} platforms</span>
                      <span>P{cat.priority}</span>
                      <span>{cat.active ? 'Active' : 'Inactive'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'health' && (
          <div className="p-6">
            <h2 className="text-lg font-semibold text-white mb-4">Scraper Health</h2>
            {health ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <Card>
                  <div className="p-4">
                    <h3 className="text-sm font-semibold text-white mb-3">Summary</h3>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                        <p className="text-2xl font-bold text-emerald-400">{health.healthy}</p>
                        <p className="text-[10px] text-slate-500 mt-1">Healthy</p>
                      </div>
                      <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                        <p className="text-2xl font-bold text-yellow-400">{health.failing}</p>
                        <p className="text-[10px] text-slate-500 mt-1">Failing</p>
                      </div>
                      <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                        <p className="text-2xl font-bold text-red-400">{health.disabled}</p>
                        <p className="text-[10px] text-slate-500 mt-1">Disabled</p>
                      </div>
                    </div>
                  </div>
                </Card>
                <Card>
                  <div className="p-4 max-h-64 overflow-y-auto">
                    <h3 className="text-sm font-semibold text-white mb-3">Per-Platform Status</h3>
                    <div className="space-y-1">
                      {health.details && Object.entries(health.details).map(([platform, info]: [string, any]) => (
                        <div key={platform} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-white/5">
                          <span className="text-xs text-slate-300">{platform}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-slate-500">{info.success_rate}%</span>
                            <StatusBadge status={info.status} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </Card>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                <p className="text-sm">No health data yet.</p>
                <p className="text-xs text-slate-600 mt-1">Run a lead generation to populate scraper health data</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
