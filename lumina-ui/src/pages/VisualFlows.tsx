import { useState, useEffect, useCallback, useRef } from 'react';
import {
  GitBranch, Plus, Play, Save, Trash2, RefreshCw, X,
  ArrowRight, Move, Zap, Settings, Download, Upload,
  ChevronRight, Activity, Clock,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/visual-flows';

interface FlowNode {
  id: string; type: string; label: string; x: number; y: number;
  config: Record<string, string>;
}

interface FlowEdge {
  id: string; source: string; target: string; label: string; condition: string;
}

interface VisualFlow {
  id: string; name: string; description: string;
  nodes: FlowNode[]; edges: FlowEdge[];
  created_at: number; updated_at: number; run_count: number;
}

interface PaletteItem {
  type: string; label: string; color: string; description: string;
}

const NODE_COLORS: Record<string, string> = {
  input: '#6366f1', ceo: '#f59e0b', planner: '#8b5cf6', programmer: '#22c55e',
  tester: '#ef4444', debugger: '#f97316', designer: '#ec4899',
  database_engineer: '#06b6d4', devops_engineer: '#14b8a6',
  security_auditor: '#dc2626', marketing_agent: '#a855f7',
  documentation_writer: '#64748b', output: '#3b82f6',
};

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function del(path: string): Promise<void> {
  await fetch(`${BASE}${path}`, { method: 'DELETE' });
}

export default function VisualFlows() {
  const { addToast } = useToast();
  const canvasRef = useRef<HTMLDivElement>(null);

  const [palette, setPalette] = useState<PaletteItem[]>([]);
  const [flows, setFlows] = useState<VisualFlow[]>([]);
  const [activeFlow, setActiveFlow] = useState<VisualFlow | null>(null);
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<FlowEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<FlowNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<FlowEdge | null>(null);
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);
  const [dragging, setDragging] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [executing, setExecuting] = useState(false);
  const [execResult, setExecResult] = useState<any>(null);
  const [showSave, setShowSave] = useState(false);
  const [flowName, setFlowName] = useState('');
  const [flowDesc, setFlowDesc] = useState('');
  const [nodeTask, setNodeTask] = useState('');

  const loadPalette = useCallback(async () => {
    try {
      const d = await get<{ palette: PaletteItem[] }>('/palette');
      setPalette(d.palette);
    } catch {}
  }, []);

  const loadFlows = useCallback(async () => {
    try {
      const d = await get<{ flows: VisualFlow[] }>('');
      setFlows(d.flows);
    } catch {}
  }, []);

  useEffect(() => { loadPalette(); loadFlows(); }, [loadPalette, loadFlows]);

  const addNode = (type: PaletteItem, x: number, y: number) => {
    const id = `node_${Date.now()}_${Math.random().toString(36).slice(2,6)}`;
    const node: FlowNode = { id, type: type.type, label: type.label, x, y, config: {} };
    setNodes(prev => [...prev, node]);
    setActiveFlow(null);
  };

  const removeNode = (id: string) => {
    setNodes(prev => prev.filter(n => n.id !== id));
    setEdges(prev => prev.filter(e => e.source !== id && e.target !== id));
    if (selectedNode?.id === id) setSelectedNode(null);
  };

  const startEdge = (nodeId: string) => {
    setConnectingFrom(nodeId);
  };

  const finishEdge = (targetId: string) => {
    if (connectingFrom && connectingFrom !== targetId) {
      const exists = edges.some(e => e.source === connectingFrom && e.target === targetId);
      if (!exists) {
        const edge: FlowEdge = {
          id: `edge_${Date.now()}`,
          source: connectingFrom,
          target: targetId,
          label: '', condition: '',
        };
        setEdges(prev => [...prev, edge]);
      }
    }
    setConnectingFrom(null);
  };

  const removeEdge = (id: string) => {
    setEdges(prev => prev.filter(e => e.id !== id));
    setSelectedEdge(null);
  };

  const handleCanvasClick = (e: React.MouseEvent) => {
    if (e.target === canvasRef.current) {
      setSelectedNode(null);
      setSelectedEdge(null);
      setConnectingFrom(null);
    }
  };

  const handleMouseDown = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation();
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    setDragging(nodeId);
    setDragOffset({ x: e.clientX - node.x, y: e.clientY - node.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!dragging || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - dragOffset.x;
    const y = e.clientY - rect.top - dragOffset.y;
    setNodes(prev => prev.map(n => n.id === dragging ? { ...n, x, y } : n));
  };

  const handleMouseUp = () => {
    setDragging(null);
  };

  const saveFlow = async () => {
    if (!flowName.trim()) return;
    const payload = {
      name: flowName.trim(),
      description: flowDesc.trim(),
      nodes: nodes.map(n => ({ id: n.id, type: n.type, label: n.label, x: n.x, y: n.y, config: n.config })),
      edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target, label: e.label, condition: e.condition })),
    };

    try {
      let saved: VisualFlow;
      if (activeFlow) {
        const r = await put<{ flow: VisualFlow }>('/update', { flow_id: activeFlow.id, ...payload });
        saved = r.flow;
      } else {
        const r = await post<{ flow: VisualFlow }>('/create', payload);
        saved = r.flow;
      }
      setActiveFlow(saved);
      addToast('Flow saved', 'success');
      setShowSave(false);
      loadFlows();
    } catch { addToast('Save failed', 'error'); }
  };

  const loadFlow = (flow: VisualFlow) => {
    setActiveFlow(flow);
    setNodes(flow.nodes.map(n => ({ ...n })));
    setEdges(flow.edges.map(e => ({ ...e })));
    setSelectedNode(null);
    setConnectingFrom(null);
  };

  const deleteFlow = async (flowId: string) => {
    await del(`/${flowId}`);
    if (activeFlow?.id === flowId) {
      setActiveFlow(null);
      setNodes([]);
      setEdges([]);
    }
    loadFlows();
    addToast('Flow deleted', 'info');
  };

  const newFlow = () => {
    setActiveFlow(null);
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setExecResult(null);
  };

  const executeFlow = async () => {
    if (nodes.length === 0) { addToast('Add at least one node', 'info'); return; }
    setExecuting(true);
    setExecResult(null);
    try {
      const payload = { flow_id: activeFlow?.id || '', nodes, edges };
      const r = await post<any>('/execute', { flow_id: activeFlow?.id || '', input_text: '' });
      setExecResult(r);
      addToast('Flow executed', 'success');
      loadFlows();
    } catch { addToast('Execution failed', 'error'); }
    setExecuting(false);
  };

  const openSaveDialog = () => {
    setFlowName(activeFlow?.name || '');
    setFlowDesc(activeFlow?.description || '');
    setShowSave(true);
  };

  const updateNodeConfig = () => {
    if (!selectedNode) return;
    setNodes(prev => prev.map(n => n.id === selectedNode.id ? { ...n, config: { ...n.config, task: nodeTask } } : n));
    setSelectedNode(prev => prev ? { ...prev, config: { ...prev.config, task: nodeTask } } : null);
  };

  useEffect(() => {
    if (selectedNode) setNodeTask(selectedNode.config?.task || '');
  }, [selectedNode]);

  const renderEdge = (edge: FlowEdge) => {
    const src = nodes.find(n => n.id === edge.source);
    const tgt = nodes.find(n => n.id === edge.target);
    if (!src || !tgt) return null;

    const sx = src.x + 90;
    const sy = src.y + 30;
    const tx = tgt.x + 90;
    const ty = tgt.y + 30;

    const midX = (sx + tx) / 2;
    const midY = (sy + ty) / 2;

    return (
      <g key={edge.id}>
        <line x1={sx} y1={sy} x2={tx} y2={ty}
          stroke={selectedEdge?.id === edge.id ? '#f59e0b' : '#475569'}
          strokeWidth={2} strokeDasharray={connectingFrom === edge.source ? '6,3' : '0'}
          onClick={(e) => { e.stopPropagation(); setSelectedEdge(edge); }}
          style={{ cursor: 'pointer' }} />
        <circle cx={midX} cy={midY} r={4} fill="#475569"
          onClick={() => removeEdge(edge.id)}
          style={{ cursor: 'pointer' }} />
      </g>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 shrink-0 bg-slate-950/30">
        <div className="flex items-center gap-3">
          <GitBranch className="w-4 h-4 text-amber-400" />
          <h1 className="text-xs font-semibold text-slate-200">Visual Agents</h1>
          {activeFlow && <span className="text-[10px] text-slate-500">{activeFlow.name}</span>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={newFlow} className="text-[10px] bg-white/5 hover:bg-white/10 text-slate-400 px-2.5 py-1 rounded transition-colors">New</button>
          <button onClick={openSaveDialog} className="text-[10px] bg-white/5 hover:bg-white/10 text-slate-400 px-2.5 py-1 rounded transition-colors flex items-center gap-1">
            <Save className="w-3 h-3" /> Save
          </button>
          <button onClick={executeFlow} disabled={executing || nodes.length === 0}
            className="text-[10px] bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white px-3 py-1 rounded transition-colors flex items-center gap-1">
            <Play className="w-3 h-3" /> {executing ? 'Running...' : 'Execute'}
          </button>
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* Palette */}
        <div className="w-48 border-r border-white/5 bg-slate-950/20 shrink-0 overflow-y-auto p-2 space-y-1">
          <p className="text-[9px] text-slate-600 font-medium uppercase tracking-wider px-2 mb-2">Agent Palette</p>
          {palette.map(p => (
            <div key={p.type}
              draggable
              onDragStart={e => { e.dataTransfer.setData('type', p.type); e.dataTransfer.setData('label', p.label); }}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-white/5 cursor-grab active:cursor-grabbing transition-colors border border-transparent hover:border-white/5">
              <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: p.color }} />
              <span className="text-[10px] text-slate-400 truncate">{p.label}</span>
            </div>
          ))}
        </div>

        {/* Canvas */}
        <div ref={canvasRef}
          className="flex-1 relative bg-[#0a0a0f] overflow-hidden"
          onClick={handleCanvasClick}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onDragOver={e => e.preventDefault()}
          onDrop={e => {
            e.preventDefault();
            const type = e.dataTransfer.getData('type');
            const label = e.dataTransfer.getData('label');
            if (type && canvasRef.current) {
              const rect = canvasRef.current.getBoundingClientRect();
              const p = palette.find(p => p.type === type);
              if (p) addNode(p, e.clientX - rect.left - 60, e.clientY - rect.top - 20);
            }
          }}>
          {/* Grid */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-10" style={{ backgroundImage: 'radial-gradient(circle, #475569 1px, transparent 1px)', backgroundSize: '20px 20px' }} />

          {/* SVG Edges */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
            {edges.map(renderEdge)}
            {connectingFrom && nodes.find(n => n.id === connectingFrom) && (
              <line x1={(nodes.find(n => n.id === connectingFrom)?.x || 0) + 90}
                y1={(nodes.find(n => n.id === connectingFrom)?.y || 0) + 30}
                x2={(nodes.find(n => n.id === connectingFrom)?.x || 0) + 90}
                y2={(nodes.find(n => n.id === connectingFrom)?.y || 0) + 30}
                stroke="#f59e0b" strokeWidth={2} strokeDasharray="6,3" opacity={0.5} />
            )}
          </svg>

          {/* Nodes */}
          {nodes.map(node => (
            <div key={node.id}
              className={`absolute rounded-xl border-2 bg-slate-900/95 backdrop-blur-sm shadow-lg cursor-pointer transition-shadow hover:shadow-xl ${selectedNode?.id === node.id ? 'border-amber-400 shadow-amber-500/20' : 'border-white/10'}`}
              style={{ left: node.x, top: node.y, width: 180, zIndex: 10 }}
              onClick={e => { e.stopPropagation(); setSelectedNode(node); setSelectedEdge(null); }}>
              <div className="flex items-center gap-2 px-3 py-2 border-b border-white/5 rounded-t-xl"
                style={{ background: (NODE_COLORS[node.type] || '#475569') + '20' }}>
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: NODE_COLORS[node.type] || '#475569' }} />
                <span className="text-[10px] font-medium text-slate-300 flex-1 truncate"
                  onMouseDown={e => handleMouseDown(e, node.id)}>{node.label}</span>
                <div className="flex items-center gap-0.5">
                  <button onClick={e => { e.stopPropagation(); startEdge(node.id); }}
                    className={`p-1 rounded transition-colors ${connectingFrom === node.id ? 'text-amber-400 bg-amber-500/10' : 'text-slate-600 hover:text-slate-400'}`}
                    title="Connect">
                    <ArrowRight className="w-3 h-3" />
                  </button>
                  <button onClick={e => { e.stopPropagation(); removeNode(node.id); }}
                    className="p-1 rounded text-slate-600 hover:text-red-400 transition-colors">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </div>
              {connectingFrom && connectingFrom !== node.id && (
                <button onClick={e => { e.stopPropagation(); finishEdge(node.id); }}
                  className="w-full text-[9px] text-amber-400 hover:bg-amber-500/10 px-3 py-1 transition-colors text-center">
                  Connect to this agent
                </button>
              )}
              <div className="px-3 py-1.5 text-[9px] text-slate-600 truncate">
                {node.config?.task || 'No task set'}
              </div>
            </div>
          ))}

          {nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <GitBranch className="w-12 h-12 text-slate-800 mx-auto mb-3" />
                <p className="text-xs text-slate-600">Drag agents from the palette to build a workflow</p>
                <p className="text-[10px] text-slate-700 mt-1">Click ➔ on a node to connect to another agent</p>
              </div>
            </div>
          )}
        </div>

        {/* Properties Panel */}
        <div className="w-56 border-l border-white/5 bg-slate-950/20 shrink-0 overflow-y-auto p-3 space-y-3">
          {selectedNode ? (
            <>
              <div>
                <p className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">Node Properties</p>
                <div className="flex items-center gap-2 mt-2">
                  <div className="w-3 h-3 rounded-full" style={{ background: NODE_COLORS[selectedNode.type] || '#475569' }} />
                  <p className="text-[11px] text-slate-300 font-medium">{selectedNode.label}</p>
                </div>
              </div>
              <div>
                <p className="text-[9px] text-slate-500 uppercase tracking-wider">Type</p>
                <p className="text-[11px] text-slate-400">{selectedNode.type}</p>
              </div>
              <div>
                <p className="text-[9px] text-slate-500 uppercase tracking-wider mb-1">Task / Prompt</p>
                <textarea value={nodeTask} onChange={e => setNodeTask(e.target.value)}
                  onBlur={updateNodeConfig}
                  rows={4}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-[10px] text-white placeholder-slate-600 outline-none focus:border-amber-500/50 resize-none"
                  placeholder="What should this agent do?" />
              </div>
              <button onClick={() => removeNode(selectedNode.id)}
                className="w-full text-[10px] text-red-400/70 hover:text-red-400 transition-colors text-left border-t border-white/5 pt-2">
                Remove Node
              </button>
            </>
          ) : selectedEdge ? (
            <>
              <div>
                <p className="text-[9px] text-slate-500 font-medium uppercase tracking-wider">Connection</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  {nodes.find(n => n.id === selectedEdge.source)?.label} → {nodes.find(n => n.id === selectedEdge.target)?.label}
                </p>
              </div>
              <button onClick={() => removeEdge(selectedEdge.id)}
                className="w-full text-[10px] text-red-400/70 hover:text-red-400 transition-colors text-left border-t border-white/5 pt-2">
                Remove Connection
              </button>
            </>
          ) : (
            <>
              {/* Flows List */}
              <div>
                <p className="text-[9px] text-slate-500 font-medium uppercase tracking-wider mb-2">Saved Flows</p>
                {flows.length === 0 ? (
                  <p className="text-[10px] text-slate-600">No flows yet</p>
                ) : (
                  <div className="space-y-1">
                    {flows.map(f => (
                      <div key={f.id} className="group flex items-center gap-1.5 px-2 py-1.5 rounded-lg hover:bg-white/5 transition-colors">
                        <button onClick={() => loadFlow(f)}
                          className="flex-1 text-left text-[10px] text-slate-400 hover:text-slate-200 truncate">
                          {f.name}
                        </button>
                        <button onClick={() => deleteFlow(f.id)}
                          className="opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition-all p-0.5">
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Execution Results */}
              {execResult && (
                <div className="border-t border-white/5 pt-3">
                  <p className="text-[9px] text-slate-500 font-medium uppercase tracking-wider mb-2">Last Result</p>
                  <div className="bg-emerald-500/5 border border-emerald-800/20 rounded-lg p-2">
                    <p className="text-[9px] text-emerald-400">Executed {execResult.nodes_executed} nodes</p>
                  </div>
                  {execResult.node_results && Object.entries(execResult.node_results).map(([id, r]: [string, any]) => {
                    const node = nodes.find(n => n.id === id);
                    return (
                      <div key={id} className={`mt-1 rounded-lg border px-2 py-1 text-[9px] ${r.status === 'success' ? 'bg-emerald-500/5 border-emerald-800/20 text-emerald-400' : 'bg-red-500/5 border-red-800/20 text-red-400'}`}>
                        <p className="font-medium">{node?.label || id}</p>
                        <p className="text-slate-500">{r.status}</p>
                      </div>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Save Dialog */}
      {showSave && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowSave(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 w-full max-w-sm shadow-2xl" onClick={e => e.stopPropagation()}>
            <h2 className="text-sm font-semibold text-slate-200 mb-3">Save Flow</h2>
            <input value={flowName} onChange={e => setFlowName(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-amber-500/50 mb-2"
              placeholder="Flow name" autoFocus />
            <input value={flowDesc} onChange={e => setFlowDesc(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-amber-500/50"
              placeholder="Description (optional)" />
            <div className="flex items-center gap-2 mt-3">
              <button onClick={() => setShowSave(false)}
                className="flex-1 text-xs text-slate-400 hover:text-slate-200 py-2 rounded-lg transition-colors">Cancel</button>
              <button onClick={saveFlow} disabled={!flowName.trim()}
                className="flex-1 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg py-2 text-xs font-medium transition-all">
                Save Flow
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
