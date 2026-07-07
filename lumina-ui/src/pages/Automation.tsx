import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity, Play, Loader2, CheckCircle, XCircle, Plus, Trash2,
  Power, PowerOff, Clock, Globe, FileText, Bell, Terminal,
  Code2, Mail, User, LogIn, Eye, EyeOff, Copy, RefreshCw,
  Settings2, ListOrdered, Workflow, History, Zap, Webhook,
  ToggleLeft, ToggleRight, ChevronRight, ChevronDown, Brain, GitBranch,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/automation';

interface TriggerType { id: string; label: string; description: string; config?: Record<string, any>; }
interface ActionType { id: string; label: string; description: string; config?: Record<string, any>; }
interface Workflow { id: string; name: string; description: string; trigger: { type: string; config: Record<string, any> }; steps: Step[]; enabled: boolean; created_at: string; updated_at: string; tags: string[]; }
interface Step { id: string; action: string; name: string; config: Record<string, any>; depends_on?: string[]; }
interface Run { run_id: string; workflow_id: string; started_at: string; completed_at: string; status: string; steps: StepResult[]; error: string; trigger_info: string; }
interface StepResult { step_id: string; step_name: string; action: string; status: string; started_at: string; completed_at: string; output: string; error: string; }

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
async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function triggerIcon(type: string) {
  switch (type) {
    case 'manual': return Play;
    case 'schedule': return Clock;
    case 'webhook': return Globe;
    case 'file_change': return FileText;
    case 'time': return Clock;
    case 'interval': return RefreshCw;
    default: return Zap;
  }
}

function actionIcon(id: string) {
  switch (id) {
    case 'shell': return Terminal;
    case 'http_request': return Globe;
    case 'ai_task': return Brain;
    case 'file_operation': return FileText;
    case 'notification': return Bell;
    case 'employee_task': return User;
    case 'wait': return Clock;
    case 'condition': return GitBranch;
    case 'log': return FileText;
    case 'script': return Code2;
    case 'send_email': return Mail;
    default: return Zap;
  }
}

export default function Automation() {
  const [tab, setTab] = useState('dashboard');
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [triggers, setTriggers] = useState<TriggerType[]>([]);
  const [actions, setActions] = useState<ActionType[]>([]);
  const [history, setHistory] = useState<Run[]>([]);
  const [selectedRun, setSelectedRun] = useState<Run | null>(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const { addToast } = useToast();

  // Editor state
  const [editing, setEditing] = useState<Workflow | null>(null);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editTrigger, setEditTrigger] = useState('manual');
  const [editTriggerConfig, setEditTriggerConfig] = useState<Record<string, any>>({});
  const [editSteps, setEditSteps] = useState<Step[]>([]);
  const [showNewStepMenu, setShowNewStepMenu] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      const [wf, tr, ac, hist] = await Promise.all([
        get<{ workflows: Workflow[] }>('/workflows'),
        get<{ triggers: TriggerType[] }>('/triggers'),
        get<{ actions: ActionType[] }>('/actions'),
        get<{ history: Run[] }>('/history?limit=30'),
      ]);
      setWorkflows(wf.workflows);
      setTriggers(tr.triggers);
      setActions(ac.actions);
      setHistory(hist.history);
    } catch (e: any) {
      addToast('Failed to load automation data', 'error');
    }
  }, [addToast]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const runWorkflow = async (id: string) => {
    try {
      const res = await post<{ run_id: string }>(`/workflows/${id}/run`);
      addToast(`Workflow started: ${res.run_id}`, 'success');
      loadAll();
    } catch { addToast('Failed to run workflow', 'error'); }
  };

  const toggleWorkflow = async (id: string) => {
    try {
      await post(`/workflows/${id}/toggle`);
      loadAll();
    } catch { addToast('Failed to toggle workflow', 'error'); }
  };

  const deleteWorkflow = async (id: string) => {
    try {
      await del(`/workflows/${id}`);
      addToast('Workflow deleted', 'info');
      loadAll();
    } catch { addToast('Failed to delete workflow', 'error'); }
  };

  const startNewWorkflow = () => {
    setEditing(null);
    setEditName('');
    setEditDesc('');
    setEditTrigger('manual');
    setEditTriggerConfig({});
    setEditSteps([]);
    setTab('editor');
  };

  const editWorkflow = (wf: Workflow) => {
    setEditing(wf);
    setEditName(wf.name);
    setEditDesc(wf.description);
    setEditTrigger(wf.trigger.type);
    setEditTriggerConfig(wf.trigger.config);
    setEditSteps(wf.steps);
    setTab('editor');
  };

  const addStep = (action: string) => {
    const actionDef = actions.find(a => a.id === action);
    setEditSteps(prev => [...prev, {
      id: Math.random().toString(36).slice(2, 8),
      action,
      name: actionDef?.label || action,
      config: { ...(actionDef?.config || {}) },
    }]);
    setShowNewStepMenu(false);
  };

  const updateStep = (idx: number, data: Partial<Step>) => {
    setEditSteps(prev => prev.map((s, i) => i === idx ? { ...s, ...data } : s));
  };

  const removeStep = (idx: number) => {
    setEditSteps(prev => prev.filter((_, i) => i !== idx));
  };

  const saveWorkflow = async () => {
    if (!editName.trim()) { addToast('Workflow name is required', 'error'); return; }
    setLoading(true);
    try {
      const body = {
        name: editName,
        description: editDesc,
        trigger: { type: editTrigger, config: editTriggerConfig },
        steps: editSteps,
      };
      if (editing) {
        await put(`/workflows/${editing.id}`, body);
        addToast('Workflow updated', 'success');
      } else {
        await post('/workflows', body);
        addToast('Workflow created', 'success');
      }
      setTab('workflows');
      loadAll();
    } catch { addToast('Failed to save workflow', 'error'); }
    setLoading(false);
  };

  const filteredWorkflows = workflows.filter(w =>
    w.name.toLowerCase().includes(search.toLowerCase()) ||
    w.description.toLowerCase().includes(search.toLowerCase())
  );

  const renderTriggerConfig = () => {
    const t = triggers.find(t => t.id === editTrigger);
    if (!t?.config) return null;
    return (
      <div className="space-y-3 mt-3 p-4 bg-white/[0.02] rounded-xl border border-white/5">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Trigger Config</p>
        {Object.entries(t.config).map(([key, val]) => (
          <div key={key}>
            <label className="text-xs text-slate-500 block mb-1">{key.replace(/_/g, ' ')}</label>
            {typeof val === 'number' ? (
              <input type="number" value={editTriggerConfig[key] ?? val} onChange={e => setEditTriggerConfig(p => ({ ...p, [key]: +e.target.value }))}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-lumina-500/50" />
            ) : (
              <input value={editTriggerConfig[key] ?? val} onChange={e => setEditTriggerConfig(p => ({ ...p, [key]: e.target.value }))}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-lumina-500/50"
                placeholder={key} />
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderStepConfig = (step: Step, idx: number) => {
    const a = actions.find(ac => ac.id === step.action);
    if (!a?.config) return null;
    return (
      <div className="space-y-2 mt-2">
        {Object.entries(a.config).map(([key, val]) => (
          <div key={key}>
            <label className="text-[10px] text-slate-500 block mb-0.5">{key.replace(/_/g, ' ')}</label>
            {key === 'code' || key === 'prompt' || key === 'command' || key === 'body' ? (
              <textarea rows={2} value={step.config[key] ?? val} onChange={e => updateStep(idx, { config: { ...step.config, [key]: e.target.value } })}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white font-mono outline-none focus:border-lumina-500/50 resize-none" />
            ) : key === 'timeout' || key === 'seconds' || key === 'delay_seconds' || key === 'interval_seconds' ? (
              <input type="number" value={step.config[key] ?? val} onChange={e => updateStep(idx, { config: { ...step.config, [key]: +e.target.value } })}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:border-lumina-500/50" />
            ) : key === 'method' ? (
              <select value={step.config.method ?? 'GET'} onChange={e => updateStep(idx, { config: { ...step.config, method: e.target.value } })}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:border-lumina-500/50">
                {['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            ) : key === 'level' ? (
              <select value={step.config.level ?? 'info'} onChange={e => updateStep(idx, { config: { ...step.config, level: e.target.value } })}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:border-lumina-500/50">
                {['info', 'warn', 'error', 'debug'].map(l => <option key={l} value={l}>{l}</option>)}
              </select>
            ) : key === 'headers' ? (
              <input value={JSON.stringify(step.config.headers ?? {})} onChange={e => { try { updateStep(idx, { config: { ...step.config, headers: JSON.parse(e.target.value) } }); } catch {} }}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white font-mono outline-none focus:border-lumina-500/50" placeholder='{"Content-Type": "application/json"}' />
            ) : (
              <input value={step.config[key] ?? val} onChange={e => updateStep(idx, { config: { ...step.config, [key]: e.target.value } })}
                className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white outline-none focus:border-lumina-500/50" />
            )}
          </div>
        ))}
      </div>
    );
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'workflows', label: `Workflows (${workflows.length})`, icon: ListOrdered },
    { id: 'editor', label: editing ? 'Edit Workflow' : 'New Workflow', icon: Settings2 },
    { id: 'history', label: `History (${history.length})`, icon: History },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader icon={Workflow} title="Automation" description="Advanced workflow builder and execution engine" />
        <button onClick={startNewWorkflow} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2 transition-all shadow-lg shadow-lumina-500/20">
          <Plus className="w-4 h-4" /> New Workflow
        </button>
      </div>

      <div className="flex items-center gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/5 w-fit">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t.id ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'text-slate-400 hover:text-slate-200'
            }`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      {/* Dashboard */}
      {tab === 'dashboard' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card hover={false} className="text-center py-6">
              <Activity className="w-8 h-8 text-lumina-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">{workflows.length}</p>
              <p className="text-xs text-slate-500">Total Workflows</p>
            </Card>
            <Card hover={false} className="text-center py-6">
              <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">{workflows.filter(w => w.enabled).length}</p>
              <p className="text-xs text-slate-500">Active</p>
            </Card>
            <Card hover={false} className="text-center py-6">
              <History className="w-8 h-8 text-blue-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">{history.length}</p>
              <p className="text-xs text-slate-500">Executions</p>
            </Card>
            <Card hover={false} className="text-center py-6">
              <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-2xl font-bold text-white">{history.filter(h => h.status === 'success').length}</p>
              <p className="text-xs text-slate-500">Successful</p>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card hover={false} className="space-y-4">
              <CardSection label="Trigger Types">
                <div className="grid grid-cols-2 gap-2">
                  {triggers.map(t => (
                    <div key={t.id} className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                      {React.createElement(triggerIcon(t.id), { className: 'w-4 h-4 text-lumina-400 shrink-0 mt-0.5' })}
                      <div>
                        <p className="text-xs font-medium text-slate-200">{t.label}</p>
                        <p className="text-[10px] text-slate-500">{t.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardSection>
            </Card>
            <Card hover={false} className="space-y-4">
              <CardSection label="Action Types">
                <div className="grid grid-cols-2 gap-2 max-h-80 overflow-y-auto">
                  {actions.map(a => (
                    <div key={a.id} className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.02] border border-white/5">
                      {React.createElement(actionIcon(a.id), { className: 'w-4 h-4 text-lumina-400 shrink-0 mt-0.5' })}
                      <div>
                        <p className="text-xs font-medium text-slate-200">{a.label}</p>
                        <p className="text-[10px] text-slate-500">{a.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardSection>
            </Card>
          </div>
        </div>
      )}

      {/* Workflows List */}
      {tab === 'workflows' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <input value={search} onChange={e => setSearch(e.target.value)}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50"
              placeholder="Search workflows..." />
            <button onClick={loadAll} className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {filteredWorkflows.length === 0 ? (
            <Card hover={false} className="text-center py-12">
              <Activity className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No workflows yet</p>
              <button onClick={startNewWorkflow} className="mt-4 bg-lumina-600 hover:bg-lumina-500 text-white rounded-lg px-4 py-2 text-sm font-medium inline-flex items-center gap-2">
                <Plus className="w-4 h-4" /> Create your first workflow
              </button>
            </Card>
          ) : (
            <div className="space-y-3">
              {filteredWorkflows.map(wf => (
                <Card key={wf.id} onClick={() => editWorkflow(wf)} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 min-w-0 flex-1">
                      {React.createElement(triggerIcon(wf.trigger.type), { className: 'w-5 h-5 text-lumina-400 shrink-0 mt-0.5' })}
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-slate-200 truncate">{wf.name}</p>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${wf.enabled ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500'}`}>
                            {wf.enabled ? 'Active' : 'Disabled'}
                          </span>
                          <span className="text-[10px] text-slate-600 bg-white/5 px-1.5 py-0.5 rounded-full">{wf.trigger.type}</span>
                        </div>
                        {wf.description && <p className="text-xs text-slate-500 truncate mt-0.5">{wf.description}</p>}
                        <div className="flex items-center gap-3 mt-1.5">
                          <span className="text-[10px] text-slate-600">{wf.steps.length} step{wf.steps.length !== 1 ? 's' : ''}</span>
                          <span className="text-[10px] text-slate-600">{new Date(wf.updated_at).toLocaleString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0" onClick={e => e.stopPropagation()}>
                      <button onClick={() => runWorkflow(wf.id)} disabled={!wf.enabled}
                        className="p-2 rounded-lg hover:bg-lumina-600/15 text-slate-400 hover:text-lumina-300 disabled:opacity-30 transition-colors" title="Run now">
                        <Play className="w-4 h-4" />
                      </button>
                      <button onClick={() => toggleWorkflow(wf.id)}
                        className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-slate-200 transition-colors" title={wf.enabled ? 'Disable' : 'Enable'}>
                        {wf.enabled ? <ToggleRight className="w-4 h-4 text-emerald-400" /> : <ToggleLeft className="w-4 h-4" />}
                      </button>
                      <button onClick={() => deleteWorkflow(wf.id)}
                        className="p-2 rounded-lg hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-colors" title="Delete">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Editor */}
      {tab === 'editor' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card hover={false} className="space-y-4">
              <CardSection label="Workflow Details">
                <input value={editName} onChange={e => setEditName(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50"
                  placeholder="Workflow name" />
                <textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} rows={2}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50 resize-none"
                  placeholder="Description (optional)" />
              </CardSection>
            </Card>

            <Card hover={false} className="space-y-4">
              <CardSection label="Trigger">
                <div className="flex flex-wrap gap-2">
                  {triggers.map(t => (
                    <button key={t.id} onClick={() => { setEditTrigger(t.id); setEditTriggerConfig(t.config ? { ...t.config } : {}); }}
                      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-all ${
                        editTrigger === t.id ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'bg-white/5 text-slate-400 hover:text-slate-200 border border-transparent'
                      }`}>
                      {React.createElement(triggerIcon(t.id), { className: 'w-3.5 h-3.5' })} {t.label}
                    </button>
                  ))}
                </div>
                {renderTriggerConfig()}
              </CardSection>
            </Card>

            <Card hover={false} className="space-y-4">
              <CardSection label={`Steps (${editSteps.length})`} action={
                <div className="relative">
                  <button onClick={() => setShowNewStepMenu(!showNewStepMenu)}
                    className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-lg px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 transition-all">
                    <Plus className="w-3.5 h-3.5" /> Add Step
                  </button>
                  {showNewStepMenu && (
                    <div className="absolute right-0 top-full mt-1 w-56 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50 py-1 max-h-64 overflow-y-auto">
                      {actions.map(a => (
                        <button key={a.id} onClick={() => addStep(a.id)}
                          className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-slate-300 hover:bg-white/5 hover:text-white transition-colors text-left">
                          {React.createElement(actionIcon(a.id), { className: 'w-3.5 h-3.5 text-lumina-400 shrink-0' })}
                          <span className="truncate">{a.label}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              }>
                {editSteps.length === 0 ? (
                  <div className="text-center py-8 border-2 border-dashed border-white/10 rounded-xl">
                    <p className="text-xs text-slate-500">No steps yet. Click "Add Step" to begin.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {editSteps.map((step, idx) => {
                      const Icon = actionIcon(step.action);
                      return (
                        <div key={step.id} className="bg-white/[0.02] border border-white/10 rounded-xl p-4 space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 min-w-0">
                              <Icon className="w-4 h-4 text-lumina-400 shrink-0" />
                              <input value={step.name} onChange={e => updateStep(idx, { name: e.target.value })}
                                className="bg-transparent text-sm font-medium text-slate-200 outline-none border-b border-transparent focus:border-lumina-500/50 min-w-0"
                                placeholder="Step name" />
                              <span className="text-[10px] text-slate-600 bg-white/5 px-1.5 py-0.5 rounded-full">{step.action}</span>
                            </div>
                            <button onClick={() => removeStep(idx)}
                              className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors shrink-0">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                          {renderStepConfig(step, idx)}
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardSection>
            </Card>
          </div>

          <div className="space-y-4">
            <Card hover={false} className="space-y-4 sticky top-4">
              <CardSection label="Workflow Summary">
                <div className="space-y-2 text-xs text-slate-400">
                  <div className="flex justify-between"><span>Name</span><span className="text-slate-200 font-medium truncate ml-2">{editName || '(unnamed)'}</span></div>
                  <div className="flex justify-between"><span>Trigger</span><span className="text-slate-200">{triggers.find(t => t.id === editTrigger)?.label || editTrigger}</span></div>
                  <div className="flex justify-between"><span>Steps</span><span className="text-slate-200">{editSteps.length}</span></div>
                  <div className="flex justify-between"><span>Actions</span><span className="text-slate-200">{editSteps.map(s => s.action).join(', ') || '(none)'}</span></div>
                </div>
              </CardSection>
              <div className="flex gap-2">
                <button onClick={saveWorkflow} disabled={loading || !editName.trim()}
                  className="flex-1 bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-4 py-2.5 text-sm font-medium transition-all flex items-center justify-center gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  {editing ? 'Update Workflow' : 'Create Workflow'}
                </button>
                <button onClick={() => setTab('workflows')}
                  className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 text-sm transition-colors">
                  Cancel
                </button>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* History */}
      {tab === 'history' && (
        <div className="space-y-4">
          {selectedRun ? (
            <div className="space-y-4">
              <button onClick={() => setSelectedRun(null)} className="text-xs text-lumina-400 hover:text-lumina-300 flex items-center gap-1">
                <ChevronRight className="w-3 h-3 rotate-180" /> Back to history
              </button>
              <Card hover={false} className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-200">Run {selectedRun.run_id}</p>
                    <p className="text-xs text-slate-500">{selectedRun.trigger_info || 'Manual'} · {new Date(selectedRun.started_at).toLocaleString()}</p>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                    selectedRun.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                    selectedRun.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'
                  }`}>{selectedRun.status}</span>
                </div>
                {selectedRun.error && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-xs text-red-400 font-mono">{selectedRun.error}</div>
                )}
                <div className="space-y-2">
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Steps</p>
                  {selectedRun.steps.map((s, i) => (
                    <div key={s.step_id} className={`rounded-xl border p-4 ${
                      s.status === 'success' ? 'bg-emerald-500/5 border-emerald-800/30' :
                      s.status === 'failed' ? 'bg-red-500/5 border-red-800/30' : 'bg-slate-900/50 border-white/10'
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {React.createElement(actionIcon(s.action), { className: 'w-4 h-4 text-lumina-400' })}
                          <span className="text-sm font-medium text-slate-200">{s.step_name}</span>
                          <span className="text-[10px] text-slate-600">{s.action}</span>
                        </div>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                          s.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                          s.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'
                        }`}>{s.status}</span>
                      </div>
                      {s.output && <pre className="text-xs text-slate-400 font-mono bg-slate-950/50 rounded-lg p-2 overflow-x-auto max-h-32">{s.output}</pre>}
                      {s.error && <pre className="text-xs text-red-400 font-mono bg-red-950/30 rounded-lg p-2 mt-1">{s.error}</pre>}
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <button onClick={loadAll} className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
                  <RefreshCw className="w-4 h-4" />
                </button>
                <span className="text-xs text-slate-500">{history.length} total executions</span>
              </div>
              {history.length === 0 ? (
                <Card hover={false} className="text-center py-12">
                  <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-sm text-slate-400">No execution history</p>
                  <p className="text-xs text-slate-500 mt-1">Run a workflow to see results here</p>
                </Card>
              ) : (
                <div className="space-y-2">
                  {history.map(run => (
                    <Card key={run.run_id} onClick={() => setSelectedRun(run)} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className={`w-2 h-2 rounded-full shrink-0 ${
                            run.status === 'success' ? 'bg-emerald-500' :
                            run.status === 'failed' ? 'bg-red-500' : 'bg-amber-500'
                          }`} />
                          <div className="min-w-0">
                            <p className="text-xs font-medium text-slate-200 truncate">{run.run_id}</p>
                            <p className="text-[10px] text-slate-500">{run.trigger_info || 'Manual'} · {new Date(run.started_at).toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-500">{run.steps.length} steps</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                            run.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                            run.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'
                          }`}>{run.status}</span>
                          <ChevronRight className="w-3 h-3 text-slate-500" />
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

const Save = (props: any) => (
  <svg {...props} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
    <polyline points="17 21 17 13 7 13 7 21" />
    <polyline points="7 3 7 8 15 8" />
  </svg>
);
