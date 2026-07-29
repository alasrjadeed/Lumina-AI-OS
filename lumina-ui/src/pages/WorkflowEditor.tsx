import { useState, useEffect, useCallback, useRef } from 'react';
import { GitBranch, Plus, Trash2, ArrowRight, Square, Terminal, Globe, MessageSquare, Clock, Database, Zap, X, FileDown, FileUp, LayoutList, Download, Play, Search, Bookmark, Tag, Filter, Save, Settings, Key, ChevronDown, ChevronRight, Braces, Image, Loader, Workflow, type LucideIcon } from 'lucide-react';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

interface Position { x: number; y: number; }
interface NodeData { id: string; type: string; label: string; position: Position; config: Record<string, any>; credentials: string | null; notes: string; }
interface EdgeData { id: string; source: string; target: string; label: string; sourceHandle: string; targetHandle: string; }
interface WorkflowData { id: string; name: string; description: string; category: string; nodes: NodeData[]; edges: EdgeData[]; tags?: string[]; settings?: Record<string, any>; createdAt?: string; updatedAt?: string; }
interface NodeTypeInfo { type: string; label: string; category: string; color: string; icon: string; description: string; trigger: boolean; defaults: Record<string, any>; configSchema: ConfigField[]; }
interface ConfigField { key: string; label: string; type: 'string' | 'number' | 'boolean' | 'select' | 'json' | 'code'; default?: any; options?: { label: string; value: any }[]; placeholder?: string; required?: boolean; }
interface CredentialInfo { id: string; name: string; type: string; data?: Record<string, any>; createdAt?: string; }

const CATEGORIES = ['automation', 'data', 'communication', 'development', 'infrastructure', 'sales', 'productivity', 'ecommerce', 'social', 'http', 'ai', 'utilities', 'experimental', 'custom'];

const CATEGORY_LABELS: Record<string, string> = {
  triggers: 'Triggers', ai: 'AI / LLM', 'flow-control': 'Flow Control',
  'data-transform': 'Data Transform', 'file-media': 'File & Media',
  communication: 'Communication', 'crm-sales': 'CRM & Sales',
  'project-management': 'Project Mgmt', ecommerce: 'E-Commerce',
  'cloud-infra': 'Cloud & Infra', database: 'Database',
  social: 'Social Media', 'developer-tools': 'Developer Tools',
  'http-rest': 'HTTP / REST', utilities: 'Utilities',
  experimental: 'Experimental', automation: 'Automation',
  data: 'Data', development: 'Development',
  infrastructure: 'Infrastructure', sales: 'Sales',
  productivity: 'Productivity',
};

const CATEGORY_COLORS: Record<string, string> = {
  triggers: '#f59e0b', ai: '#8b5cf6', 'flow-control': '#06b6d4',
  'data-transform': '#10b981', 'file-media': '#f97316',
  communication: '#3b82f6', 'crm-sales': '#14b8a6',
  'project-management': '#6366f1', ecommerce: '#ec4899',
  'cloud-infra': '#0ea5e9', database: '#84cc16',
  social: '#e11d48', 'developer-tools': '#64748b',
  'http-rest': '#22c55e', utilities: '#a855f7',
  experimental: '#f43f5e', automation: '#f59e0b',
  data: '#10b981', development: '#64748b',
  infrastructure: '#0ea5e9', sales: '#14b8a6',
  productivity: '#6366f1',
};

const ICON_MAP: Record<string, LucideIcon> = {
  webhook: Zap, cron: Clock, 'form-trigger': FileUp,
  'telegram-trigger': MessageSquare, 'slack-send': MessageSquare,
  'send-email': MessageSquare, 'read-email': MessageSquare,
  'console-log': Terminal, 'github-trigger': GitBranch,
  'notion-create': Bookmark, 'jira-create': LayoutList,
  'http-request': Globe, 'llm-chat': Braces,
  'image-gen': Image, 'embedding': Braces,
  'vector-store': Database, 'ai-agent': Workflow,
  'mcp-tool': Terminal, 'if': GitBranch,
  'code': Braces, 'set': Save,
  'wait': Clock, 'loop': Loader,
  'noop': Square, 'respond-to-webhook': Globe,
  'read-binary': FileUp, 'write-binary': FileDown,
  'csv-parse': Database, 'html-to-pdf': FileDown,
  'image-resize': Image, 'watch-folder': Search,
  'postgres-query': Database, 's3-trigger': Database,
  's3-get': Database, 'docker-ps': Terminal,
  'google-sheets-append': Database,
  'shopify-trigger': Zap, 'stripe-trigger': Zap,
  'hubspot-trigger': Globe, 'salesforce-trigger': Globe,
  'asana-trigger': LayoutList, 'linear-trigger': LayoutList,
  'twitter-trigger': MessageSquare, 'discord-send': MessageSquare,
  'trello-trigger': LayoutList, 'form-trigger': FileUp,
  'ai-agent': Workflow,
};

function getIcon(name: string): LucideIcon {
  return ICON_MAP[name] || Terminal;
}

export default function WorkflowEditor() {
  const [tab, setTab] = useState<'builder' | 'n8n' | 'credentials'>('builder');
  const [workflows, setWorkflows] = useState<WorkflowData[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [wf, setWf] = useState<WorkflowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [category, setCategory] = useState('custom');
  const [connecting, setConnecting] = useState<string | null>(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const canvasRef = useRef<HTMLDivElement>(null);
  const [executing, setExecuting] = useState(false);
  const [execResult, setExecResult] = useState<any>(null);
  const [execPayload, setExecPayload] = useState('{}');
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [dragNodeType, setDragNodeType] = useState<string | null>(null);
  const [nodeTypes, setNodeTypes] = useState<NodeTypeInfo[]>([]);
  const [nodeCategories, setNodeCategories] = useState<string[]>([]);
  const [paletteSearch, setPaletteSearch] = useState('');
  const [paletteCategory, setPaletteCategory] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<CredentialInfo[]>([]);
  const [credForm, setCredForm] = useState({ name: '', type: '', data: '{}' });
  const [n8nTemplates, setN8nTemplates] = useState<any[]>([]);
  const [n8nJsonInput, setN8nJsonInput] = useState('');
  const [templateSearch, setTemplateSearch] = useState('');
  const [templateCategory, setTemplateCategory] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['triggers', 'ai']));
  const [draggingOver, setDraggingOver] = useState(false);
  const { addToast } = useToast();

  useEffect(() => { loadWorkflows(); loadNodeTypes(); }, []);

  useEffect(() => {
    if (tab === 'n8n') loadN8nTemplates();
    if (tab === 'credentials') loadCredentials();
  }, [tab]);

  async function loadNodeTypes() {
    try {
      const r = await fetch(`${BASE}/workflows/node-types`);
      const data = await r.json();
      setNodeTypes(data.nodeTypes || []);
      setNodeCategories(data.categories || []);
    } catch {}
  }

  async function loadWorkflows() {
    setLoading(true);
    try {
      const r = await fetch(`${BASE}/workflows`);
      const data = await r.json();
      setWorkflows(data.workflows || []);
    } catch {}
    setLoading(false);
  }

  async function loadWorkflow(id: string) {
    try {
      const r = await fetch(`${BASE}/workflows/${id}`);
      const data = await r.json();
      setWf(data.workflow);
      setSelectedId(id);
      setName(data.workflow.name);
      setDesc(data.workflow.description);
      setCategory(data.workflow.category);
      setSelectedNode(null);
    } catch {}
  }

  async function createWorkflow() {
    if (!name.trim()) return;
    try {
      const params = new URLSearchParams({ name, description: desc, category });
      await fetch(`${BASE}/workflows?${params.toString()}`, { method: 'POST' });
      addToast('Workflow created', 'success');
      setName(''); setDesc('');
      await loadWorkflows();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteWorkflow(id: string) {
    try {
      await fetch(`${BASE}/workflows/${id}`, { method: 'DELETE' });
      addToast('Deleted', 'success');
      if (selectedId === id) { setWf(null); setSelectedId(null); }
      await loadWorkflows();
    } catch { addToast('Delete failed', 'error'); }
  }

  async function addNode(type: string, label: string, config: Record<string, any> = {}) {
    if (!wf) return;
    try {
      const params = new URLSearchParams({
        node_type: type, label,
        config: JSON.stringify(config),
        x: String(Math.random() * 400 + 50),
        y: String(Object.keys(wf.nodes || {}).length * 100 + 40),
      });
      await fetch(`${BASE}/workflows/${wf.id}/nodes?${params.toString()}`, { method: 'POST' });
      await loadWorkflow(wf.id);
      addToast(`Added ${label}`, 'success');
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteNode(nodeId: string) {
    if (!wf) return;
    try {
      await fetch(`${BASE}/workflows/${wf.id}/nodes/${nodeId}`, { method: 'DELETE' });
      if (selectedNode?.id === nodeId) setSelectedNode(null);
      await loadWorkflow(wf.id);
    } catch { addToast('Delete failed', 'error'); }
  }

  async function updateNode(nodeId: string, updates: Record<string, any>) {
    if (!wf) return;
    try {
      const params = new URLSearchParams();
      if (updates.label !== undefined) params.set('label', updates.label);
      if (updates.config !== undefined) params.set('config', JSON.stringify(updates.config));
      if (updates.x !== undefined || updates.y !== undefined) {
        params.set('x', String(updates.x ?? (selectedNode?.position.x ?? 0)));
        params.set('y', String(updates.y ?? (selectedNode?.position.y ?? 0)));
      }
      if (updates.credentials !== undefined) params.set('credentials', updates.credentials);
      if (updates.notes !== undefined) params.set('notes', updates.notes);
      await fetch(`${BASE}/workflows/${wf.id}/nodes/${nodeId}?${params.toString()}`, { method: 'PATCH' });
      await loadWorkflow(wf.id);
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function addEdge(source: string, target: string) {
    if (!wf) return;
    try {
      const params = new URLSearchParams({ source, target });
      await fetch(`${BASE}/workflows/${wf.id}/edges?${params.toString()}`, { method: 'POST' });
      await loadWorkflow(wf.id);
    } catch (e: any) { addToast(e.message, 'error'); }
    setConnecting(null);
  }

  async function deleteEdge(edgeId: string) {
    if (!wf) return;
    try {
      await fetch(`${BASE}/workflows/${wf.id}/edges/${edgeId}`, { method: 'DELETE' });
      await loadWorkflow(wf.id);
    } catch {}
  }

  async function exportN8n() {
    if (!wf) return;
    try {
      const r = await fetch(`${BASE}/workflows/${wf.id}/export/n8n`);
      const data = await r.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${wf.name.replace(/\s+/g, '_')}.n8n.json`;
      a.click();
      URL.revokeObjectURL(url);
      addToast('Exported as n8n JSON', 'success');
    } catch { addToast('Export failed', 'error'); }
  }

  async function saveAsTemplate() {
    if (!wf) return;
    try {
      const r = await fetch(`${BASE}/workflows/${wf.id}/save-template?tags=${encodeURIComponent(wf.category)}`, { method: 'POST' });
      if (r.ok) addToast('Saved as reusable template', 'success');
      else addToast('Failed to save template', 'error');
    } catch { addToast('Failed to save template', 'error'); }
  }

  async function executeWorkflow() {
    if (!wf) return;
    setExecuting(true);
    setExecResult(null);
    try {
      let payload = {};
      try { payload = JSON.parse(execPayload); } catch {}
      const r = await fetch(`${BASE}/workflows/${wf.id}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await r.json();
      setExecResult(result);
      if (result.success) addToast(`Workflow ran: ${result.node_count} nodes executed`, 'success');
      else addToast(`Workflow completed with ${result.errors?.length || 0} errors`, 'warning');
    } catch (e: any) { addToast(e.message, 'error'); }
    setExecuting(false);
  }

  async function loadN8nTemplates() {
    try {
      const params = new URLSearchParams();
      if (templateSearch) params.set('query', templateSearch);
      if (templateCategory) params.set('category', templateCategory);
      const r = await fetch(`${BASE}/workflows/n8n/templates?${params.toString()}`);
      const data = await r.json();
      setN8nTemplates(data.templates || []);
    } catch {}
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
        addToast('n8n workflow imported', 'success');
        setN8nJsonInput('');
        await loadWorkflows();
      } else {
        const res = await r.json();
        addToast(res.detail || 'Import failed', 'error');
      }
    } catch { addToast('Invalid JSON', 'error'); }
  }

  async function importTemplate(templateId: string) {
    try {
      const r = await fetch(`${BASE}/workflows/n8n/templates/${templateId}/import`, { method: 'POST' });
      if (r.ok) {
        addToast('Template imported', 'success');
        await loadWorkflows();
      } else addToast('Template import failed', 'error');
    } catch { addToast('Template import failed', 'error'); }
  }

  async function loadCredentials() {
    try {
      const r = await fetch(`${BASE}/workflows/credentials`);
      const data = await r.json();
      setCredentials(data.credentials || []);
    } catch {}
  }

  async function createCredential() {
    if (!credForm.name.trim() || !credForm.type.trim()) return;
    try {
      const params = new URLSearchParams({ name: credForm.name, cred_type: credForm.type, data: credForm.data });
      await fetch(`${BASE}/workflows/credentials?${params.toString()}`, { method: 'POST' });
      addToast('Credential created', 'success');
      setCredForm({ name: '', type: '', data: '{}' });
      await loadCredentials();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteCredential(id: string) {
    try {
      await fetch(`${BASE}/workflows/credentials/${id}`, { method: 'DELETE' });
      addToast('Credential deleted', 'success');
      await loadCredentials();
    } catch {}
  }

  function getNodeTypeInfo(type: string): NodeTypeInfo | undefined {
    return nodeTypes.find(nt => nt.type === type);
  }

  function toggleCategory(cat: string) {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return next;
    });
  }

  const filteredPalette = nodeTypes.filter(nt => {
    if (paletteCategory && nt.category !== paletteCategory) return false;
    if (paletteSearch) {
      const q = paletteSearch.toLowerCase();
      return nt.label.toLowerCase().includes(q) || nt.type.toLowerCase().includes(q) || nt.description?.toLowerCase().includes(q);
    }
    return true;
  });

  const groupedPalette = filteredPalette.reduce((acc, nt) => {
    if (!acc[nt.category]) acc[nt.category] = [];
    acc[nt.category].push(nt);
    return acc;
  }, {} as Record<string, NodeTypeInfo[]>);

  const handleCanvasDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDraggingOver(false);
    const type = e.dataTransfer.getData('nodeType');
    if (!type || !wf) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const nt = getNodeTypeInfo(type);
    addNode(type, nt?.label || type, nt?.defaults || {});
  }, [wf, nodeTypes, addNode]);

  const handleNodeDragStart = (type: string) => {
    setDragNodeType(type);
  };

  const getNodeColor = (type: string): string => {
    const nt = getNodeTypeInfo(type);
    return nt?.color || CATEGORY_COLORS[nt?.category || ''] || '#64748b';
  };

  const paletteCats = Object.keys(groupedPalette);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-3 border-b border-[var(--border-primary)] shrink-0">
        <div className="flex items-center gap-4">
          <div><h1 className="text-xl font-semibold">Workflow Editor</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Visual automation builder — 81 node types, 52 templates</p></div>
        </div>
        <div className="flex items-center gap-2">
          {[['builder', GitBranch, 'Builder'], ['n8n', LayoutList, 'Templates'], ['credentials', Key, 'Credentials']].map(([t, Icon, label]) => (
            <button key={t} onClick={() => setTab(t as any)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${tab === t ? 'bg-[var(--brand-500)] text-white shadow-lg' : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'}`}>
              <Icon className="w-3.5 h-3.5" />{label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'builder' && (
        <div className="flex-1 flex min-h-0">
          <div className="w-60 border-r border-[var(--border-primary)] overflow-y-auto shrink-0 bg-[var(--bg-tertiary)]/30">
            <div className="p-3 space-y-3">
              <div>
                <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Workflows</h3>
                {loading ? <div className="skeleton h-20 w-full" /> : (
                  <div className="space-y-0.5 max-h-40 overflow-y-auto">
                    {workflows.map((w: any) => (
                      <div key={w.id} className={`flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${selectedId === w.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}
                        onClick={() => loadWorkflow(w.id)}>
                        <GitBranch className="w-3 h-3 mr-1.5 shrink-0" />
                        <span className="flex-1 truncate">{w.name}</span>
                        <button onClick={e => { e.stopPropagation(); deleteWorkflow(w.id); }} className="text-red-400 hover:text-red-300 p-0.5"><X className="w-2.5 h-2.5" /></button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="pt-2 border-t border-[var(--border-primary)]">
                <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">New Workflow</h3>
                <div className="space-y-2">
                  <input className="input text-xs" value={name} onChange={e => setName(e.target.value)} placeholder="Workflow name" />
                  <input className="input text-xs" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description" />
                  <select className="input text-xs" value={category} onChange={e => setCategory(e.target.value)}>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                  </select>
                  <button onClick={createWorkflow} className="btn btn-primary text-xs w-full"><Plus className="w-3 h-3" /> Create</button>
                </div>
              </div>

              <div className="pt-2 border-t border-[var(--border-primary)]">
                <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Node Palette</h3>
                <div className="relative mb-2">
                  <Search className="w-3 h-3 absolute left-2 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
                  <input className="input text-xs pl-7 w-full" value={paletteSearch} onChange={e => setPaletteSearch(e.target.value)} placeholder="Search nodes..." />
                </div>
                <div className="flex flex-wrap gap-1 mb-2">
                  <button onClick={() => setPaletteCategory(null)}
                    className={`text-2xs px-1.5 py-0.5 rounded ${!paletteCategory ? 'bg-[var(--brand-500)] text-white' : 'bg-[var(--bg-hover)] text-[var(--text-tertiary)]'}`}>All</button>
                  {nodeCategories.slice(0, 6).map(c => (
                    <button key={c} onClick={() => setPaletteCategory(paletteCategory === c ? null : c)}
                      className={`text-2xs px-1.5 py-0.5 rounded ${paletteCategory === c ? 'bg-[var(--brand-500)] text-white' : 'bg-[var(--bg-hover)] text-[var(--text-tertiary)]'}`}>
                      {CATEGORY_LABELS[c] || c}
                    </button>
                  ))}
                </div>
                <div className="space-y-1 max-h-[calc(100vh-520px)] overflow-y-auto">
                  {paletteCats.length === 0 && (
                    <div className="text-2xs text-[var(--text-tertiary)] text-center py-4">No matching nodes</div>
                  )}
                  {paletteCats.map(cat => (
                    <div key={cat}>
                      <button onClick={() => toggleCategory(cat)}
                        className="flex items-center gap-1 w-full text-2xs text-[var(--text-tertiary)] font-medium py-1 hover:text-[var(--text-primary)]">
                        {expandedCategories.has(cat) ? <ChevronDown className="w-2.5 h-2.5" /> : <ChevronRight className="w-2.5 h-2.5" />}
                        {CATEGORY_LABELS[cat] || cat}
                        <span className="ml-auto text-[var(--text-tertiary)]">{groupedPalette[cat].length}</span>
                      </button>
                      {expandedCategories.has(cat) && groupedPalette[cat].map(nt => {
                        const Icon = getIcon(nt.type);
                        return (
                          <div key={nt.type}
                            draggable onDragStart={() => handleNodeDragStart(nt.type)}
                            onClick={() => wf && addNode(nt.type, nt.label, nt.defaults || {})}
                            className="flex items-center gap-2 px-2 py-1.5 rounded-lg text-xs cursor-grab hover:bg-[var(--bg-hover)] transition-colors group"
                            title={nt.description}>
                            <Icon className="w-3.5 h-3.5 shrink-0" style={{ color: nt.color }} />
                            <span className="flex-1 truncate">{nt.label}</span>
                            {nt.trigger && <span className="text-2xs text-orange-400 font-medium">TRIGGER</span>}
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 flex flex-col min-w-0">
            {wf ? (
              <>
                <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-semibold">{wf.name}</h2>
                    <span className="badge badge-info text-2xs">{wf.category}</span>
                    <span className="text-2xs text-[var(--text-tertiary)]">{wf.nodes?.length || 0} nodes · {wf.edges?.length || 0} edges</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button onClick={saveAsTemplate} className="flex items-center gap-1 px-2 py-1 rounded-lg text-2xs hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]"><Bookmark className="w-3 h-3" /> Save</button>
                    <button onClick={exportN8n} className="flex items-center gap-1 px-2 py-1 rounded-lg text-2xs hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]"><FileDown className="w-3 h-3" /> Export</button>
                    <button onClick={() => { setExecPayload('{}'); setExecResult(null); executeWorkflow(); }} disabled={executing}
                      className="flex items-center gap-1 px-2 py-1 rounded-lg text-2xs bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30">
                      <Play className="w-3 h-3" /> {executing ? 'Running...' : 'Run'}
                    </button>
                  </div>
                </div>

                <div className="flex-1 flex min-h-0">
                  <div ref={canvasRef} className="flex-1 relative overflow-auto p-4"
                    onDragOver={e => { e.preventDefault(); setDraggingOver(true); }}
                    onDragLeave={() => setDraggingOver(false)}
                    onDrop={handleCanvasDrop}
                    onMouseMove={e => {
                      const r = canvasRef.current?.getBoundingClientRect();
                      setMousePos({ x: e.clientX - (r?.left || 0), y: e.clientY - (r?.top || 0) });
                    }}>
                    <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
                      {(wf.edges || []).map((e: EdgeData) => {
                        const src = (wf.nodes || []).find((n: NodeData) => n.id === e.source);
                        const tgt = (wf.nodes || []).find((n: NodeData) => n.id === e.target);
                        if (!src || !tgt) return null;
                        const x1 = (src.position?.x || 0) + 96;
                        const y1 = (src.position?.y || 0) + 16;
                        const x2 = (tgt.position?.x || 0) + 96;
                        const y2 = (tgt.position?.y || 0);
                        return (
                          <g key={e.id}>
                            <line x1={x1} y1={y1} x2={x2} y2={y2}
                              stroke="var(--border-brand)" strokeWidth={2} strokeDasharray="5,3" opacity={0.5} />
                            <circle cx={x2} cy={y2} r={3} fill="var(--border-brand)" opacity={0.6} />
                          </g>
                        );
                      })}
                      {connecting && (() => {
                        const srcNode = (wf.nodes || []).find((n: NodeData) => n.id === connecting);
                        if (!srcNode) return null;
                        const sx = (srcNode.position?.x || 0) + 96;
                        const sy = (srcNode.position?.y || 0) + 16;
                        return (
                          <g>
                            <line x1={sx} y1={sy} x2={mousePos.x} y2={mousePos.y}
                              stroke="var(--brand-500)" strokeWidth={2.5} strokeDasharray="6,4" opacity={0.8} />
                            <circle cx={mousePos.x} cy={mousePos.y} r={4} fill="var(--brand-500)" opacity={0.9} />
                          </g>
                        );
                      })()}
                    </svg>
                    <div className="relative" style={{ minHeight: 500, zIndex: 1 }}>
                      {(wf.nodes || []).map((node: NodeData) => {
                        const nt = getNodeTypeInfo(node.type);
                        const color = nt?.color || '#64748b';
                        const Icon = getIcon(node.type);
                        const isSelected = selectedNode?.id === node.id;
                        return (
                          <div key={node.id}
                            onClick={() => setSelectedNode(node)}
                            className={`absolute bg-[var(--bg-elevated)] rounded-xl border-2 transition-all cursor-pointer group hover:shadow-lg hover:border-[var(--border-brand)] ${isSelected ? 'border-[var(--brand-500)] shadow-lg ring-1 ring-[var(--brand-500)]/30' : 'border-[var(--border-primary)]'}`}
                            style={{ left: node.position?.x || 0, top: node.position?.y || 0, width: 192 }}>
                            <div className="relative flex items-center gap-2 px-3 py-2" style={{ borderBottom: `2px solid ${color}20` }}>
                              <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}20` }}>
                                <Icon className="w-3.5 h-3.5" style={{ color }} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="text-xs font-medium truncate">{node.label}</div>
                                <div className="text-2xs text-[var(--text-tertiary)] truncate">{node.type}</div>
                              </div>
                              {nt?.trigger && <div className="w-1.5 h-1.5 rounded-full bg-orange-400 shrink-0" title="Trigger" />}
                              <div className="absolute -right-1.5 top-1/2 -translate-y-1/2">
                                <div className={`w-3 h-3 rounded-full border-2 transition-all cursor-crosshair ${connecting === node.id ? 'bg-[var(--brand-500)] border-[var(--brand-500)] scale-125 shadow-lg shadow-[var(--brand-500)]/40 animate-pulse' : 'bg-[var(--bg-elevated)] border-[var(--border-primary)] group-hover:border-[var(--brand-500)] group-hover:scale-110'}`}
                                  title={connecting === node.id ? 'Connecting...' : 'Connect output'}
                                  onClick={e => { e.stopPropagation(); connecting ? (connecting !== node.id && addEdge(connecting, node.id)) : setConnecting(node.id); }} />
                              </div>
                            </div>
                            <div className="px-3 py-1.5 flex items-center justify-between">
                              <div className="flex items-center gap-1.5">
                                {connecting && connecting !== node.id ? (
                                  <button onClick={e => { e.stopPropagation(); addEdge(connecting, node.id); }}
                                    className="p-0.5 rounded bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"><ArrowRight className="w-3 h-3" /></button>
                                ) : (
                                  <button onClick={e => { e.stopPropagation(); setConnecting(connecting === node.id ? null : node.id); }}
                                    className={`p-0.5 rounded transition-colors ${connecting === node.id ? 'bg-[var(--brand-500)] text-white' : 'text-[var(--text-tertiary)] hover:text-[var(--text-primary)]'}`}>
                                    <ArrowRight className="w-3 h-3" />
                                  </button>
                                )}
                                <span className="text-2xs text-[var(--text-tertiary)]">
                                  {connecting === node.id ? 'Connecting...' : connecting ? 'Connect' : ''}
                                </span>
                              </div>
                              <button onClick={e => { e.stopPropagation(); deleteNode(node.id); }}
                                className="p-0.5 rounded text-red-400 hover:bg-red-500/20 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Trash2 className="w-3 h-3" />
                              </button>
                            </div>
                          </div>
                        );
                      })}
                      {(wf.nodes || []).length === 0 && (
                        <div className="absolute inset-0 flex items-center justify-center text-xs text-[var(--text-tertiary)]">
                          <div className={`text-center p-8 rounded-xl border-2 border-dashed transition-colors ${draggingOver ? 'border-[var(--brand-500)] bg-[var(--brand-500)]/5' : 'border-[var(--border-primary)]'}`}>
                            <GitBranch className="w-10 h-10 mx-auto mb-3 opacity-30" />
                            <p className="font-medium">Drag nodes from the palette</p>
                            <p className="text-2xs mt-1">or click a node type to add it</p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {selectedNode && (
                    <div className="w-72 border-l border-[var(--border-primary)] bg-[var(--bg-tertiary)]/30 overflow-y-auto shrink-0">
                      <div className="p-3 space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-semibold">Node Config</h3>
                          <button onClick={() => setSelectedNode(null)} className="text-[var(--text-tertiary)] hover:text-[var(--text-primary)]">
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                        {(() => {
                          const nt = getNodeTypeInfo(selectedNode.type);
                          return (
                            <div className="space-y-3">
                              <div>
                                <label className="text-2xs text-[var(--text-tertiary)] block mb-1">Label</label>
                                <input className="input text-xs w-full" value={selectedNode.label}
                                  onChange={e => {
                                    const updated = { ...selectedNode, label: e.target.value };
                                    setSelectedNode(updated);
                                  }}
                                  onBlur={() => updateNode(selectedNode.id, { label: selectedNode.label })}
                                />
                              </div>
                              {nt && nt.description && (
                                <p className="text-2xs text-[var(--text-tertiary)] leading-relaxed">{nt.description}</p>
                              )}
                              <div>
                                <label className="text-2xs text-[var(--text-tertiary)] block mb-1">Type</label>
                                <div className="text-xs text-[var(--text-primary)] font-mono bg-[var(--bg-hover)] px-2 py-1 rounded">{selectedNode.type}</div>
                              </div>
                              {nt && nt.configSchema && nt.configSchema.map((field: ConfigField) => (
                                <div key={field.key}>
                                  <label className="text-2xs text-[var(--text-tertiary)] block mb-1">
                                    {field.label}
                                    {field.required && <span className="text-red-400 ml-0.5">*</span>}
                                  </label>
                                  {field.type === 'select' ? (
                                    <select className="input text-xs w-full"
                                      value={selectedNode.config?.[field.key] ?? field.default ?? ''}
                                      onChange={e => {
                                        const cfg = { ...selectedNode.config, [field.key]: e.target.value };
                                        const updated = { ...selectedNode, config: cfg };
                                        setSelectedNode(updated);
                                        updateNode(selectedNode.id, { config: cfg });
                                      }}>
                                      {(field.options || []).map(o => (
                                        <option key={o.value} value={o.value}>{o.label}</option>
                                      ))}
                                    </select>
                                  ) : field.type === 'boolean' ? (
                                    <label className="flex items-center gap-2 cursor-pointer">
                                      <input type="checkbox"
                                        checked={!!(selectedNode.config?.[field.key] ?? field.default)}
                                        onChange={e => {
                                          const cfg = { ...selectedNode.config, [field.key]: e.target.checked };
                                          const updated = { ...selectedNode, config: cfg };
                                          setSelectedNode(updated);
                                          updateNode(selectedNode.id, { config: cfg });
                                        }}
                                        className="rounded border-[var(--border-primary)]" />
                                      <span className="text-xs">{field.label}</span>
                                    </label>
                                  ) : field.type === 'code' ? (
                                    <textarea className="input text-xs font-mono w-full h-20"
                                      placeholder={field.placeholder}
                                      value={selectedNode.config?.[field.key] ?? field.default ?? ''}
                                      onChange={e => {
                                        const cfg = { ...selectedNode.config, [field.key]: e.target.value };
                                        setSelectedNode({ ...selectedNode, config: cfg });
                                      }}
                                      onBlur={() => updateNode(selectedNode.id, { config: selectedNode.config })}
                                    />
                                  ) : (
                                    <input className="input text-xs w-full" type={field.type === 'number' ? 'number' : 'text'}
                                      placeholder={field.placeholder}
                                      value={selectedNode.config?.[field.key] ?? field.default ?? ''}
                                      onChange={e => {
                                        const val = field.type === 'number' ? Number(e.target.value) : e.target.value;
                                        const cfg = { ...selectedNode.config, [field.key]: val };
                                        setSelectedNode({ ...selectedNode, config: cfg });
                                      }}
                                      onBlur={() => updateNode(selectedNode.id, { config: selectedNode.config })}
                                    />
                                  )}
                                </div>
                              ))}
                              <div>
                                <label className="text-2xs text-[var(--text-tertiary)] block mb-1">Notes</label>
                                <textarea className="input text-xs w-full h-14"
                                  value={selectedNode.notes || ''}
                                  onChange={e => setSelectedNode({ ...selectedNode, notes: e.target.value })}
                                  onBlur={() => updateNode(selectedNode.id, { notes: selectedNode.notes })}
                                  placeholder="Optional notes about this node" />
                              </div>
                              <div>
                                <label className="text-2xs text-[var(--text-tertiary)] block mb-1">Position</label>
                                <div className="flex items-center gap-2 text-2xs text-[var(--text-tertiary)] font-mono">
                                  <span>x: {Math.round(selectedNode.position.x)}</span>
                                  <span>y: {Math.round(selectedNode.position.y)}</span>
                                </div>
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                </div>

                {execResult && (
                  <div className="border-t border-[var(--border-primary)] p-3 max-h-48 overflow-y-auto">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-xs font-semibold flex items-center gap-2">
                        <Play className="w-3 h-3" /> Execution Result
                        <span className={`badge text-2xs ${execResult.success ? 'badge-success' : 'badge-warning'}`}>
                          {execResult.success ? 'OK' : `${execResult.errors?.length || 0} errors`}
                        </span>
                      </h3>
                    </div>
                    <div className="space-y-1 text-2xs font-mono">
                      {Object.entries(execResult.outputs || {}).map(([nid, out]: any) => (
                        <div key={nid} className={`p-1.5 rounded ${out.status === 'ok' ? 'bg-emerald-500/5' : 'bg-red-500/5'}`}>
                          <div className="flex items-center gap-2">
                            <span className={`w-1.5 h-1.5 rounded-full ${out.status === 'ok' ? 'bg-emerald-400' : 'bg-red-400'}`} />
                            <span className="font-medium">{out.label}</span>
                            <span className="text-[var(--text-tertiary)]">{out.type}</span>
                            <span className="ml-auto">{out.status}</span>
                          </div>
                          {out.output && (
                            <pre className="mt-1 text-[var(--text-tertiary)] overflow-x-auto">{JSON.stringify(out.output, null, 1).slice(0, 300)}</pre>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-[var(--text-tertiary)]">
                <div className="text-center">
                  <GitBranch className="w-16 h-16 mx-auto mb-4 opacity-20" />
                  <p className="text-sm">Select or create a workflow</p>
                  <p className="text-xs mt-1">Use the sidebar to get started</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'n8n' && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-[var(--bg-elevated)] to-[var(--bg-tertiary)] border border-[var(--border-brand)]/20">
              <LayoutList className="w-5 h-5 text-[var(--text-brand)]" />
              <div>
                <p className="text-sm font-semibold">n8n Template Gallery</p>
                <p className="text-2xs text-[var(--text-tertiary)]">52 built-in templates + custom saved templates. Import, export, and run workflows.</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)]" />
                <input className="input text-xs pl-8 w-full" value={templateSearch} onChange={e => setTemplateSearch(e.target.value)} placeholder="Search templates..." />
              </div>
              <select className="input text-xs w-36" value={templateCategory} onChange={e => setTemplateCategory(e.target.value)}>
                <option value="">All Categories</option>
                {CATEGORIES.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
              </select>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <LayoutList className="w-4 h-4" /> Templates
                <span className="text-2xs text-[var(--text-tertiary)] font-normal">({n8nTemplates.length})</span>
              </h3>
              {n8nTemplates.length === 0 ? (
                <div className="text-center py-8 text-2xs text-[var(--text-tertiary)]">No templates match your search</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {n8nTemplates.map((tmpl: any) => (
                    <div key={tmpl.id} className="bento-card p-4 space-y-2 flex flex-col">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-[var(--text-primary)]">{tmpl.name}</h4>
                        <span className="badge badge-info text-2xs">{tmpl.category}</span>
                      </div>
                      <p className="text-2xs text-[var(--text-tertiary)] flex-1">{tmpl.description}</p>
                      <div className="flex items-center gap-2 text-2xs text-[var(--text-tertiary)]">
                        <span>{tmpl.workflow?.nodes?.length || 0} nodes</span>
                        <span>·</span>
                        <span>{tmpl.workflow?.edges?.length || 0} connections</span>
                        {tmpl.tags?.length > 0 && (
                          <><span>·</span>
                            <span className="flex items-center gap-1 truncate"><Tag className="w-2.5 h-2.5 shrink-0" />{tmpl.tags.slice(0, 2).join(', ')}</span>
                          </>
                        )}
                      </div>
                      <button onClick={() => importTemplate(tmpl.id)} className="btn btn-primary text-xs w-full mt-auto">
                        <Plus className="w-3 h-3" /> Import
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bento-card p-4 space-y-3">
                <h3 className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-2"><FileUp className="w-3.5 h-3.5" /> Import n8n JSON</h3>
                <p className="text-2xs text-[var(--text-tertiary)]">Paste any n8n workflow JSON to convert it into a Lumina workflow.</p>
                <textarea className="input text-xs font-mono h-24" value={n8nJsonInput} onChange={e => setN8nJsonInput(e.target.value)} placeholder='{"name":"My Workflow","nodes":[...],"connections":{...}}' />
                <button onClick={importN8nJson} className="btn btn-primary text-xs"><FileUp className="w-3 h-3" /> Import</button>
              </div>
              <div className="bento-card p-4 space-y-3">
                <h3 className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-2"><Download className="w-3.5 h-3.5" /> Export as n8n</h3>
                <p className="text-2xs text-[var(--text-tertiary)]">Build a workflow in the Builder tab, then export as n8n-compatible JSON.</p>
                <div className="flex items-center gap-2 text-2xs text-[var(--text-secondary)]">
                  <span>Switch to</span>
                  <button onClick={() => setTab('builder')} className="px-2 py-1 rounded bg-[var(--brand-500)] text-white font-medium">Builder</button>
                  <span>tab, select workflow, click Export</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === 'credentials' && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-3xl mx-auto space-y-6">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-[var(--bg-elevated)] to-[var(--bg-tertiary)] border border-[var(--border-brand)]/20">
              <Key className="w-5 h-5 text-[var(--text-brand)]" />
              <div>
                <p className="text-sm font-semibold">Credentials Manager</p>
                <p className="text-2xs text-[var(--text-tertiary)]">Manage API keys, tokens, and authentication for your workflow nodes.</p>
              </div>
            </div>

            <div className="bento-card p-4 space-y-3">
              <h3 className="text-xs font-semibold text-[var(--text-primary)]">New Credential</h3>
              <div className="flex items-end gap-2">
                <div className="flex-1 space-y-1">
                  <label className="text-2xs text-[var(--text-tertiary)]">Name</label>
                  <input className="input text-xs w-full" value={credForm.name} onChange={e => setCredForm({ ...credForm, name: e.target.value })} placeholder="My API Key" />
                </div>
                <div className="flex-1 space-y-1">
                  <label className="text-2xs text-[var(--text-tertiary)]">Type</label>
                  <select className="input text-xs w-full" value={credForm.type} onChange={e => setCredForm({ ...credForm, type: e.target.value })}>
                    <option value="">Select type</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="slack">Slack</option>
                    <option value="github">GitHub</option>
                    <option value="telegram">Telegram</option>
                    <option value="smtp">SMTP</option>
                    <option value="postgres">PostgreSQL</option>
                    <option value="aws">AWS</option>
                    <option value="http">HTTP Header</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
                <button onClick={createCredential} className="btn btn-primary text-xs"><Plus className="w-3 h-3" /> Add</button>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Saved Credentials ({credentials.length})</h3>
              {credentials.length === 0 ? (
                <div className="text-center py-8 text-2xs text-[var(--text-tertiary)]">No credentials saved yet</div>
              ) : (
                <div className="space-y-2">
                  {credentials.map((cred: CredentialInfo) => (
                    <div key={cred.id} className="bento-card p-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Key className="w-4 h-4 text-[var(--text-tertiary)]" />
                        <div>
                          <span className="text-xs font-medium">{cred.name}</span>
                          <span className="text-2xs text-[var(--text-tertiary)] ml-2">({cred.type})</span>
                        </div>
                      </div>
                      <button onClick={() => deleteCredential(cred.id)} className="text-red-400 hover:text-red-300 p-1 rounded">
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
