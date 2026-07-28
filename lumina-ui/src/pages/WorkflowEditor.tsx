import { useState, useEffect } from 'react';
import { GitBranch, Plus, Trash2, GripVertical, ArrowRight, Square, Terminal, Globe, MessageSquare, Clock, Database, Zap, X, FileDown, FileUp, LayoutList, Download, Play, Search, Bookmark, Tag, Filter } from 'lucide-react';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

const NODE_TYPES = [
  { type: 'trigger', label: 'Webhook', icon: Zap, color: 'var(--color-warning)' },
  { type: 'schedule', label: 'Schedule', icon: Clock, color: 'var(--color-warning)' },
  { type: 'manual', label: 'Manual', icon: Play, color: 'var(--color-warning)' },
  { type: 'action', label: 'Action', icon: Terminal, color: 'var(--color-info)' },
  { type: 'condition', label: 'Condition', icon: Diamond, color: 'var(--brand-500)' },
  { type: 'api_call', label: 'API Call', icon: Globe, color: 'var(--color-success)' },
  { type: 'email', label: 'Email', icon: MessageSquare, color: 'var(--color-info)' },
  { type: 'slack', label: 'Slack', icon: MessageSquare, color: 'var(--color-info)' },
  { type: 'notification', label: 'Notify', icon: MessageSquare, color: 'var(--color-info)' },
  { type: 'delay', label: 'Delay', icon: Clock, color: 'var(--text-tertiary)' },
  { type: 'data', label: 'Data', icon: Database, color: 'var(--color-warning)' },
  { type: 'transform', label: 'Transform', icon: Database, color: 'var(--color-warning)' },
];

const CATEGORIES = ['automation', 'data', 'communication', 'development', 'crm', 'ecommerce', 'custom'];

function Diamond({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return <svg className={className} style={style} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polygon points="12,2 22,12 12,22 2,12" /></svg>;
}

export default function WorkflowEditor() {
  const [tab, setTab] = useState<'builder' | 'n8n'>('builder');
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [wf, setWf] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [category, setCategory] = useState('custom');
  const [connecting, setConnecting] = useState<string | null>(null);
  const [executing, setExecuting] = useState(false);
  const [execResult, setExecResult] = useState<any>(null);
  const [execPayload, setExecPayload] = useState('{}');
  const { addToast } = useToast();

  const [n8nTemplates, setN8nTemplates] = useState<any[]>([]);
  const [n8nJsonInput, setN8nJsonInput] = useState('');
  const [templateSearch, setTemplateSearch] = useState('');
  const [templateCategory, setTemplateCategory] = useState('');

  useEffect(() => { loadWorkflows(); }, []);

  useEffect(() => {
    if (tab === 'n8n') loadN8nTemplates();
  }, [tab, templateSearch, templateCategory]);

  useEffect(() => {
    if (tab === 'n8n') loadN8nTemplates();
  }, []);

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

  async function addNode(type: string, label: string) {
    if (!wf) return;
    try {
      const params = new URLSearchParams({ node_type: type, label, config: '{}', x: String(Math.random() * 300), y: String(Object.keys(wf.nodes || {}).length * 80 + 20) });
      await fetch(`${BASE}/workflows/${wf.id}/nodes?${params.toString()}`, { method: 'POST' });
      await loadWorkflow(wf.id);
      addToast(`Added ${label}`, 'success');
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteNode(nodeId: string) {
    if (!wf) return;
    try {
      await fetch(`${BASE}/workflows/${wf.id}/nodes/${nodeId}`, { method: 'DELETE' });
      await loadWorkflow(wf.id);
    } catch { addToast('Delete failed', 'error'); }
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

  async function exportN8n() {
    if (!wf) return;
    try {
      const r = await fetch(`${BASE}/workflows/${wf.id}/export/n8n`);
      const data = await r.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${wf.name}.n8n.json`;
      a.click();
      URL.revokeObjectURL(url);
      addToast('Exported as n8n JSON', 'success');
    } catch { addToast('Export failed', 'error'); }
  }

  async function saveAsTemplate() {
    if (!wf) return;
    try {
      const r = await fetch(`${BASE}/workflows/${wf.id}/save-template?tags=${encodeURIComponent(wf.name)}`, { method: 'POST' });
      if (r.ok) {
        addToast('Saved as reusable template', 'success');
      } else {
        addToast('Failed to save template', 'error');
      }
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
      if (result.success) {
        addToast(`Workflow ran: ${result.node_count} nodes executed`, 'success');
      } else {
        addToast(`Workflow completed with ${result.errors?.length || 0} errors`, 'warning');
      }
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
      } else {
        addToast('Template import failed', 'error');
      }
    } catch { addToast('Template import failed', 'error'); }
  }

  function getNodeIcon(type: string) {
    const nt = NODE_TYPES.find(n => n.type === type);
    return nt ? nt.icon : Square;
  }

  function getNodeColor(type: string) {
    const nt = NODE_TYPES.find(n => n.type === type);
    return nt ? nt.color : 'var(--text-secondary)';
  }

  const renderCanvas = () => {
    if (!wf) return null;
    const nodes = wf.nodes || [];
    const edges = wf.edges || [];
    return (
      <div className="relative flex-1 min-h-[400px] bg-[var(--bg-tertiary)] rounded-xl border border-[var(--border-primary)] overflow-auto">
        <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
          {edges.map((e: any) => {
            const src = nodes.find((n: any) => n.id === e.source);
            const tgt = nodes.find((n: any) => n.id === e.target);
            if (!src || !tgt) return null;
            return (
              <line key={e.id} x1={(src.position?.x || 0) + 75} y1={(src.position?.y || 0) + 20} x2={(tgt.position?.x || 0) + 75} y2={(tgt.position?.y || 0) + 20}
                stroke="var(--border-brand)" strokeWidth={2} strokeDasharray="5,3" opacity={0.6} />
            );
          })}
        </svg>
        <div className="relative" style={{ minHeight: 400, zIndex: 1 }}>
          {nodes.map((node: any) => {
            const Icon = getNodeIcon(node.type);
            const color = getNodeColor(node.type);
            return (
              <div key={node.id} className="absolute flex items-start gap-2 bg-[var(--bg-elevated)] rounded-lg p-2.5 border border-[var(--border-primary)] shadow-sm hover:border-[var(--border-brand)] transition-colors cursor-pointer group"
                style={{ left: node.position?.x || 0, top: node.position?.y || 0, width: 180 }}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <Icon className="w-3.5 h-3.5 shrink-0" style={{ color }} />
                    <span className="text-xs font-medium truncate">{node.label}</span>
                  </div>
                  <span className="text-2xs text-[var(--text-tertiary)]">{node.type}</span>
                </div>
                <div className="hidden group-hover:flex items-center gap-1 shrink-0">
                  {connecting && connecting !== node.id && (
                    <button onClick={() => addEdge(connecting, node.id)} className="p-0.5 text-green-400 hover:text-green-300"><ArrowRight className="w-3 h-3" /></button>
                  )}
                  {!connecting && (
                    <button onClick={() => setConnecting(node.id)} className="p-0.5 text-[var(--text-tertiary)] hover:text-[var(--text-primary)]"><ArrowRight className="w-3 h-3" /></button>
                  )}
                  <button onClick={() => deleteNode(node.id)} className="p-0.5 text-red-400 hover:text-red-300"><Trash2 className="w-3 h-3" /></button>
                </div>
              </div>
            );
          })}
          {nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center text-xs text-[var(--text-tertiary)]">
              <div className="text-center"><GitBranch className="w-8 h-8 mx-auto mb-2 opacity-30" /><p>Drop nodes from the palette</p></div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div className="flex items-center gap-4">
          <div><h1 className="text-xl font-semibold">Workflow Editor</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Drag-and-drop visual automation builder</p></div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setTab('builder')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${tab === 'builder' ? 'bg-[var(--brand-500)] text-white shadow-lg' : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'}`}>
            <GitBranch className="w-3.5 h-3.5" />Builder
          </button>
          <button onClick={() => setTab('n8n')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${tab === 'n8n' ? 'bg-[var(--brand-500)] text-white shadow-lg' : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)]'}`}>
            <LayoutList className="w-3.5 h-3.5" />n8n
          </button>
        </div>
      </div>

      {tab === 'builder' && (
        <div className="flex-1 flex min-h-0">
          <div className="w-56 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
            <div className="space-y-3">
              <div>
                <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Workflows</h3>
                {loading ? <div className="skeleton h-20 w-full" /> : (
                  <div className="space-y-1">
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
                <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">New</h3>
                <div className="space-y-2">
                  <input className="input text-xs" value={name} onChange={e => setName(e.target.value)} placeholder="Workflow name" />
                  <input className="input text-xs" value={desc} onChange={e => setDesc(e.target.value)} placeholder="Description" />
                  <select className="input text-xs" value={category} onChange={e => setCategory(e.target.value)}>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                  </select>
                  <button onClick={createWorkflow} className="btn btn-primary text-xs w-full"><Plus className="w-3 h-3" /> Create</button>
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

                <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border-primary)] shrink-0 overflow-x-auto">
                  <span className="text-2xs text-[var(--text-tertiary)] uppercase font-semibold mr-2">Nodes:</span>
                  {NODE_TYPES.map(nt => {
                    const Icon = nt.icon;
                    return (
                      <button key={nt.type} onClick={() => addNode(nt.type, nt.label)} className="flex items-center gap-1 px-2 py-1 rounded-lg text-2xs hover:bg-[var(--bg-hover)] border border-transparent hover:border-[var(--border-brand)] transition-colors">
                        <Icon className="w-3 h-3" style={{ color: nt.color }} /> {nt.label}
                      </button>
                    );
                  })}
                </div>

                <div className="flex-1 overflow-auto p-4">
                  {renderCanvas()}
                  {execResult && (
                    <div className="mt-4 bento-card p-3 border-emerald-500/20">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-xs font-semibold">Execution Result</h3>
                        <span className={`badge text-2xs ${execResult.success ? 'badge-success' : 'badge-warning'}`}>
                          {execResult.success ? 'OK' : `${execResult.errors?.length || 0} errors`}
                        </span>
                      </div>
                      <div className="space-y-1.5 text-2xs font-mono">
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
                </div>
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
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="bento-card p-4 bg-gradient-to-r from-[var(--bg-elevated)] to-[var(--bg-tertiary)] border-[var(--border-brand)]/20">
              <div className="flex items-center gap-3">
                <LayoutList className="w-5 h-5 text-[var(--text-brand)]" />
                <div>
                  <p className="text-sm font-semibold">n8n Template Gallery</p>
                  <p className="text-2xs text-[var(--text-tertiary)]">15 built-in templates + custom saved templates. Import, export, and run workflows.</p>
                </div>
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
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {n8nTemplates.map(tmpl => (
                    <div key={tmpl.id} className="bento-card p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-xs font-semibold text-[var(--text-primary)]">{tmpl.name}</h4>
                        <span className="badge badge-info text-2xs">{tmpl.category}</span>
                      </div>
                      <p className="text-2xs text-[var(--text-tertiary)]">{tmpl.description}</p>
                      <div className="flex items-center gap-2 text-2xs text-[var(--text-tertiary)]">
                        <span>{tmpl.nodes.length} nodes</span>
                        <span>·</span>
                        <span>{tmpl.edges.length} connections</span>
                        {tmpl.tags && tmpl.tags.length > 0 && (
                          <><span>·</span>
                            <span className="flex items-center gap-1"><Tag className="w-2.5 h-2.5" />{tmpl.tags.slice(0, 3).join(', ')}</span>
                          </>
                        )}
                      </div>
                      <button onClick={() => importTemplate(tmpl.id)} className="btn btn-primary text-xs w-full">
                        <Plus className="w-3 h-3" /> Import Template
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
                <h3 className="text-xs font-semibold text-[var(--text-primary)] flex items-center gap-2"><Download className="w-3.5 h-3.5" /> Export to n8n</h3>
                <p className="text-2xs text-[var(--text-tertiary)]">Build a workflow in the Builder tab, then export as n8n-compatible JSON to import into n8n.</p>
                <div className="flex items-center gap-2 text-2xs text-[var(--text-secondary)]">
                  <span>Switch to</span>
                  <button onClick={() => setTab('builder')} className="px-2 py-1 rounded bg-[var(--brand-500)] text-white font-medium">Builder</button>
                  <span>tab, select a workflow, click Export</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
