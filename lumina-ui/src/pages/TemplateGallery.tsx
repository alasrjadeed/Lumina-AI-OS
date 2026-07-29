import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutList, Search, Tag, Plus, FileUp, Download, Grid3X3, List, ArrowLeft, Filter, ChevronDown, Zap, Clock, MessageSquare, Globe, Database, Terminal, GitBranch, Bot, Workflow, Package, Check, type LucideIcon } from 'lucide-react';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

const CATEGORIES = ['automation','data','communication','development','infrastructure','sales','productivity','ecommerce','social','http','ai','utilities','experimental','custom'];

const CATEGORY_COLORS: Record<string, string> = {
  automation: '#f59e0b', data: '#10b981', communication: '#3b82f6',
  development: '#64748b', infrastructure: '#0ea5e9', sales: '#14b8a6',
  productivity: '#6366f1', ecommerce: '#ec4899', social: '#e11d48',
  http: '#22c55e', ai: '#8b5cf6', utilities: '#a855f7',
  experimental: '#f43f5e', custom: '#94a3b8',
};

interface Template {
  id: string; name: string; description: string; category: string;
  tags: string[]; icon: string;
  workflow: { name: string; nodes: any[]; edges: any[] };
}

export default function TemplateGallery() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [importing, setImporting] = useState<string | null>(null);
  const [n8nJsonInput, setN8nJsonInput] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newTmpl, setNewTmpl] = useState({ name: '', description: '', category: 'automation' });
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<string[]>([]);
  const [nodeTypeOptions, setNodeTypeOptions] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadTemplates(); }, []);

  async function loadTemplates() {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: '100' });
      if (search) params.set('query', search);
      if (categoryFilter) params.set('category', categoryFilter);
      const r = await fetch(`${BASE}/workflows/n8n/templates?${params.toString()}`);
      const data = await r.json();
      setTemplates(data.templates || []);
    } catch { addToast('Failed to load templates', 'error'); }
    setLoading(false);
  }

  useEffect(() => { loadTemplates(); }, [search, categoryFilter]);
  useEffect(() => {
    if (showCreate && nodeTypeOptions.length === 0) {
      fetch(`${BASE}/workflows/node-types`).then(r => r.json()).then(d => setNodeTypeOptions(d.nodeTypes || [])).catch(() => {});
    }
  }, [showCreate]);

  async function importTemplate(id: string) {
    setImporting(id);
    try {
      const r = await fetch(`${BASE}/workflows/n8n/templates/${id}/import`, { method: 'POST' });
      if (r.ok) {
        addToast('Template imported!', 'success');
        navigate('/workflow-editor');
      } else {
        const res = await r.json();
        addToast(res.detail || 'Import failed', 'error');
      }
    } catch { addToast('Import failed', 'error'); }
    setImporting(null);
  }

  function toggleNodeType(nt: string) {
    setSelectedNodeTypes(prev => prev.includes(nt) ? prev.filter(n => n !== nt) : [...prev, nt]);
  }

  async function createTemplate() {
    if (!newTmpl.name.trim() || selectedNodeTypes.length === 0) return;
    setSaving(true);
    try {
      const r = await fetch(`${BASE}/workflows/n8n/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...newTmpl, node_types: selectedNodeTypes }),
      });
      if (r.ok) {
        addToast('Custom template created!', 'success');
        setShowCreate(false); setNewTmpl({ name: '', description: '', category: 'automation' }); setSelectedNodeTypes([]);
        loadTemplates();
      } else {
        const res = await r.json();
        addToast(res.detail || 'Failed to create template', 'error');
      }
    } catch { addToast('Failed to create template', 'error'); }
    setSaving(false);
  }

  async function importN8nJson() {
    if (!n8nJsonInput.trim()) return;
    try {
      const data = JSON.parse(n8nJsonInput);
      const r = await fetch(`${BASE}/workflows/n8n/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (r.ok) {
        addToast('n8n workflow imported successfully', 'success');
        setN8nJsonInput('');
        loadTemplates();
      } else {
        const res = await r.json();
        addToast(res.detail || 'Import failed', 'error');
      }
    } catch { addToast('Invalid JSON format', 'error'); }
  }

  function getCategoryColor(cat: string): string {
    return CATEGORY_COLORS[cat] || '#94a3b8';
  }

  const filtered = templates.filter(t => {
    if (categoryFilter && t.category !== categoryFilter) return false;
    if (search) {
      const q = search.toLowerCase();
      return t.name.toLowerCase().includes(q) || t.description.toLowerCase().includes(q) || t.tags?.some(tag => tag.includes(q));
    }
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/workflow-editor')} className="p-1.5 rounded-lg hover:bg-[var(--bg-hover)] text-[var(--text-secondary)] transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <LayoutList className="w-5 h-5 text-[var(--text-brand)]" /> Template Gallery
            </h1>
            <p className="text-sm text-[var(--text-secondary)] mt-0.5">{templates.length} built-in workflow templates — import and customize</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setViewMode('grid')} className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
            <Grid3X3 className="w-4 h-4" />
          </button>
          <button onClick={() => setViewMode('list')} className={`p-1.5 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
            <List className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="sticky top-0 z-10 pb-2 -mx-2 px-2 bg-[var(--bg-primary)]">
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
                <input className="input text-sm pl-10 w-full" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search templates by name, description, or tags..." />
              </div>
              <div className="flex items-center gap-1.5 flex-wrap">
                <Filter className="w-4 h-4 text-[var(--text-tertiary)]" />
                <button onClick={() => setCategoryFilter('')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${!categoryFilter ? 'bg-[var(--brand-500)] text-white shadow-sm' : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}>
                  All
                </button>
                {CATEGORIES.filter(c => templates.some(t => t.category === c)).map(cat => (
                  <button key={cat} onClick={() => setCategoryFilter(categoryFilter === cat ? '' : cat)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${categoryFilter === cat ? 'text-white shadow-sm' : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'}`}
                    style={categoryFilter === cat ? { backgroundColor: getCategoryColor(cat) } : {}}>
                    {cat}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1,2,3,4,5,6].map(i => (
                <div key={i} className="bento-card p-5 space-y-3">
                  <div className="skeleton h-4 w-3/4" />
                  <div className="skeleton h-3 w-full" />
                  <div className="skeleton h-3 w-1/2" />
                  <div className="skeleton h-9 w-full mt-3" />
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16">
              <LayoutList className="w-16 h-16 mx-auto mb-4 text-[var(--text-tertiary)] opacity-30" />
              <p className="text-base font-medium text-[var(--text-primary)]">No templates found</p>
              <p className="text-sm text-[var(--text-tertiary)] mt-1">Try adjusting your search or category filter</p>
              <button onClick={() => { setSearch(''); setCategoryFilter(''); }}
                className="btn btn-primary text-sm mt-4">Clear Filters</button>
            </div>
          ) : viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map(tmpl => (
                <div key={tmpl.id} className="bento-card p-5 flex flex-col hover:border-[var(--border-brand)]/40 transition-all duration-200 group">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg" style={{ backgroundColor: `${getCategoryColor(tmpl.category)}18` }}>
                        <LayoutList className="w-4 h-4" style={{ color: getCategoryColor(tmpl.category) }} />
                      </div>
                      <div>
                        <h3 className="text-sm font-semibold text-[var(--text-primary)] leading-tight group-hover:text-[var(--text-brand)] transition-colors">{tmpl.name}</h3>
                        <span className="text-2xs font-medium px-1.5 py-0.5 rounded" style={{ color: getCategoryColor(tmpl.category), backgroundColor: `${getCategoryColor(tmpl.category)}15` }}>
                          {tmpl.category}
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className="text-xs text-[var(--text-tertiary)] leading-relaxed flex-1 mb-3 line-clamp-2">{tmpl.description}</p>
                  <div className="flex items-center gap-3 text-2xs text-[var(--text-tertiary)] mb-3">
                    <span className="flex items-center gap-1"><Workflow className="w-3 h-3" />{tmpl.workflow?.nodes?.length || 0} nodes</span>
                    <span className="flex items-center gap-1"><GitBranch className="w-3 h-3" />{tmpl.workflow?.edges?.length || 0} edges</span>
                    {tmpl.tags?.length > 0 && (
                      <span className="flex items-center gap-1 truncate max-w-[100px]">
                        <Tag className="w-3 h-3 shrink-0" />
                        <span className="truncate">{tmpl.tags.slice(0, 2).join(', ')}</span>
                      </span>
                    )}
                  </div>
                  <button onClick={() => importTemplate(tmpl.id)} disabled={importing === tmpl.id}
                    className="btn btn-primary text-xs w-full mt-auto flex items-center justify-center gap-1.5">
                    {importing === tmpl.id ? <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      : <Plus className="w-3.5 h-3.5" />}
                    {importing === tmpl.id ? 'Importing...' : 'Import Template'}
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map(tmpl => (
                <div key={tmpl.id} className="bento-card p-4 flex items-center gap-4 hover:border-[var(--border-brand)]/40 transition-all">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${getCategoryColor(tmpl.category)}18` }}>
                    <LayoutList className="w-3.5 h-3.5" style={{ color: getCategoryColor(tmpl.category) }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold">{tmpl.name}</h3>
                      <span className="text-2xs px-1.5 py-0.5 rounded font-medium" style={{ color: getCategoryColor(tmpl.category), backgroundColor: `${getCategoryColor(tmpl.category)}15` }}>
                        {tmpl.category}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)] truncate mt-0.5">{tmpl.description}</p>
                    <div className="flex items-center gap-3 text-2xs text-[var(--text-tertiary)] mt-1">
                      <span>{tmpl.workflow?.nodes?.length || 0} nodes</span>
                      <span>·</span>
                      <span>{tmpl.workflow?.edges?.length || 0} edges</span>
                      {tmpl.tags?.length > 0 && (
                        <><span>·</span>
                          <span className="flex items-center gap-1"><Tag className="w-2.5 h-2.5" />{tmpl.tags.join(', ')}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <button onClick={() => importTemplate(tmpl.id)} disabled={importing === tmpl.id}
                    className="btn btn-primary text-xs shrink-0">
                    {importing === tmpl.id ? '...' : 'Import'}
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-[var(--border-primary)]">
            <div className="bento-card p-5 space-y-3">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2"><FileUp className="w-4 h-4 text-[var(--text-brand)]" /> Import n8n JSON</h3>
              <p className="text-xs text-[var(--text-tertiary)]">Paste any n8n workflow JSON to convert it into a Lumina workflow.</p>
              <textarea className="input text-xs font-mono h-28 w-full" value={n8nJsonInput} onChange={e => setN8nJsonInput(e.target.value)} placeholder='{"name":"My Workflow","nodes":[...],"connections":{...}}' />
              <button onClick={importN8nJson} className="btn btn-primary text-xs"><FileUp className="w-3.5 h-3.5" /> Import JSON</button>
            </div>

            <div className="bento-card p-5 space-y-3">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2"><Package className="w-4 h-4 text-[var(--text-brand)]" /> Create Custom Template</h3>
              <p className="text-xs text-[var(--text-tertiary)]">Pick node types to build a reusable template with connected features.</p>
              {!showCreate ? (
                <button onClick={() => setShowCreate(true)} className="btn btn-primary text-xs"><Plus className="w-3.5 h-3.5" /> New Template</button>
              ) : (
                <div className="space-y-2" onClick={e => e.stopPropagation()}>
                  <input className="input text-xs" value={newTmpl.name} onChange={e => setNewTmpl(p => ({ ...p, name: e.target.value }))} placeholder="Template name" />
                  <input className="input text-xs" value={newTmpl.description} onChange={e => setNewTmpl(p => ({ ...p, description: e.target.value }))} placeholder="Description" />
                  <select className="input text-xs" value={newTmpl.category} onChange={e => setNewTmpl(p => ({ ...p, category: e.target.value }))}>
                    {['automation','data','communication','ai','development','infrastructure','sales','productivity','ecommerce','social','utilities','custom'].map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <div className="max-h-32 overflow-y-auto space-y-0.5 border border-[var(--border-primary)] rounded-lg p-1.5">
                    {nodeTypeOptions.map(nt => (
                      <label key={nt.type} className="flex items-center gap-1.5 px-1.5 py-1 rounded hover:bg-[var(--bg-hover)] cursor-pointer text-2xs">
                        <input type="checkbox" checked={selectedNodeTypes.includes(nt.type)} onChange={() => toggleNodeType(nt.type)} className="w-3 h-3" />
                        <span className="flex-1 truncate">{nt.label}</span>
                        <span className="text-[var(--text-tertiary)] truncate max-w-[60px]">{nt.type}</span>
                      </label>
                    ))}
                  </div>
                  <div className="flex gap-1.5">
                    <button onClick={createTemplate} disabled={saving || !newTmpl.name.trim() || selectedNodeTypes.length === 0}
                      className="btn btn-primary text-xs flex-1">
                      {saving ? 'Saving...' : <><Check className="w-3 h-3" /> Save Template</>}
                    </button>
                    <button onClick={() => { setShowCreate(false); setSelectedNodeTypes([]); }} className="btn text-xs">Cancel</button>
                  </div>
                </div>
              )}
            </div>

            <div className="bento-card p-5 space-y-3 flex flex-col items-center justify-center text-center">
              <Download className="w-8 h-8 text-[var(--text-brand)] opacity-50" />
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Export to n8n</h3>
              <p className="text-xs text-[var(--text-tertiary)]">Build a workflow in the Workflow Editor, then export as n8n-compatible JSON.</p>
              <button onClick={() => navigate('/workflow-editor')} className="btn btn-primary text-xs">
                Open Workflow Editor
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
