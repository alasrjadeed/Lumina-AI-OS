import { useState, useEffect } from 'react';
import {
  Layers, Play, Plus, Trash2, Loader2, CheckCircle, XCircle,
  Clock, BarChart3, List, Settings,
  Terminal, Save, Search, ArrowUp,
  ArrowDown, Database, Wrench, FileCode, Globe,
  Brain, Camera, Mail,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/queue';

interface Pipeline {
  id: string; name: string; tasks: TaskDef[]; status?: string; created?: string;
}

interface TaskDef {
  module: string; action: string; params: Record<string, unknown>;
}

interface PipelineStats {
  total: number; running: number; completed: number; failed: number;
}

const MODULES = [
  { key: 'browser', label: 'Browser', icon: Globe, color: 'text-blue-400' },
  { key: 'vision', label: 'Vision', icon: Camera, color: 'text-violet-400' },
  { key: 'writer', label: 'Writer', icon: FileCode, color: 'text-emerald-400' },
  { key: 'agent', label: 'Agent', icon: Brain, color: 'text-lumina-400' },
  { key: 'terminal', label: 'Terminal', icon: Terminal, color: 'text-amber-400' },
  { key: 'email', label: 'Email', icon: Mail, color: 'text-red-400' },
  { key: 'tool', label: 'Tool', icon: Wrench, color: 'text-slate-400' },
  { key: 'data', label: 'Data', icon: Database, color: 'text-cyan-400' },
];

export default function TaskQueue() {
  const [tab, setTab] = useState('pipelines');
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [stats, setStats] = useState<PipelineStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [newName, setNewName] = useState('');
  const [newTasks, setNewTasks] = useState<TaskDef[]>([]);
  const [newModule, setNewModule] = useState('browser');
  const [newAction, setNewAction] = useState('');
  const [newParams, setNewParams] = useState('{}');
  const [searchQuery, setSearchQuery] = useState('');
  const { addToast } = useToast();

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [sRes, pRes] = await Promise.all([
        fetch(`${BASE}/stats`).then(r => r.json()),
        fetch(`${BASE}/pipelines`).then(r => r.json()),
      ]);
      setStats(sRes.stats || sRes);
      setPipelines(pRes.pipelines || []);
    } catch {} finally { setLoading(false); }
  };

  const createPipeline = async () => {
    if (!newName.trim() || newTasks.length === 0) return;
    try {
      const res = await fetch(`${BASE}/pipelines`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName, tasks: newTasks }),
      });
      if (!res.ok) throw new Error('Failed to create');
      addToast('Pipeline created', 'success');
      setShowBuilder(false);
      setNewName('');
      setNewTasks([]);
      loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  };

  const runPipeline = async (id: string) => {
    setRunningId(id);
    try {
      const res = await fetch(`${BASE}/pipelines/${id}/run`, { method: 'POST' });
      const data = await res.json();
      addToast(data.status === 'ok' ? 'Pipeline started' : 'Pipeline failed', data.status === 'ok' ? 'success' : 'error');
      loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
    finally { setRunningId(null); }
  };

  const deletePipeline = async (id: string) => {
    try {
      await fetch(`${BASE}/pipelines/${id}`, { method: 'DELETE' });
      addToast('Pipeline deleted', 'success');
      loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  };

  const addTaskToBuilder = () => {
    let params: Record<string, unknown> = {};
    try { params = JSON.parse(newParams || '{}'); } catch {}
    setNewTasks([...newTasks, { module: newModule, action: newAction, params }]);
    setNewAction('');
    setNewParams('{}');
  };

  const removeBuilderTask = (i: number) => {
    setNewTasks(newTasks.filter((_, idx) => idx !== i));
  };

  const moveTask = (i: number, dir: 'up' | 'down') => {
    const idx = dir === 'up' ? i - 1 : i + 1;
    if (idx < 0 || idx >= newTasks.length) return;
    const items = [...newTasks];
    [items[i], items[idx]] = [items[idx], items[i]];
    setNewTasks(items);
  };

  const filteredPipelines = pipelines.filter(p =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusIcon = (status?: string) => {
    if (status === 'running') return <Loader2 className="w-3.5 h-3.5 text-lumina-400 animate-spin" />;
    if (status === 'completed') return <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />;
    if (status === 'failed') return <XCircle className="w-3.5 h-3.5 text-red-400" />;
    return <Clock className="w-3.5 h-3.5 text-slate-500" />;
  };

  const getModuleIcon = (key: string) => {
    const m = MODULES.find(m => m.key === key);
    return m?.icon || Wrench;
  };

  const getModuleColor = (key: string) => {
    const m = MODULES.find(m => m.key === key);
    return m?.color || 'text-slate-400';
  };

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Layers} title="Task Queue" description="Orchestrate multi-step pipelines" />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['pipelines', 'stats', 'builder'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'pipelines' ? <List className="w-3.5 h-3.5" /> : t === 'stats' ? <BarChart3 className="w-3.5 h-3.5" /> : <Settings className="w-3.5 h-3.5" />}
            {t === 'builder' ? 'Builder' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {tab === 'pipelines' && (
          <CardSection label="Pipelines" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-32"
                />
              </div>
              <button onClick={() => { setShowBuilder(true); setTab('builder'); }}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
              ><Plus className="w-3.5 h-3.5" />New</button>
            </div>
          }>
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-5 h-5 text-lumina-400 animate-spin" />
              </div>
            ) : filteredPipelines.length === 0 ? (
              <div className="text-center py-12">
                <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No pipelines yet</p>
                <p className="text-xs text-slate-600 mt-1">Create a pipeline to automate multi-step tasks</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredPipelines.map(p => (
                  <div key={p.id}
                    className="flex items-center gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all group"
                  >
                    <div className="w-9 h-9 rounded-lg bg-lumina-500/10 flex items-center justify-center shrink-0">
                      <Layers className="w-4 h-4 text-lumina-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white truncate">{p.name}</p>
                        {statusIcon(p.status)}
                      </div>
                      <p className="text-[10px] text-slate-500">{p.tasks?.length || 0} task(s)</p>
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => runPipeline(p.id)} disabled={runningId === p.id}
                        className="p-1.5 rounded hover:bg-emerald-500/10 text-slate-500 hover:text-emerald-400"
                      >{runningId === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}</button>
                      <button onClick={() => deletePipeline(p.id)}
                        className="p-1.5 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400"
                      ><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardSection>
        )}

        {tab === 'stats' && (
          <div className="space-y-5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'Total', value: stats?.total || 0, icon: Layers, color: 'from-lumina-500 to-lumina-700' },
                { label: 'Running', value: stats?.running || 0, icon: Play, color: 'from-blue-500 to-blue-700' },
                { label: 'Completed', value: stats?.completed || 0, icon: CheckCircle, color: 'from-emerald-500 to-emerald-700' },
                { label: 'Failed', value: stats?.failed || 0, icon: XCircle, color: 'from-red-500 to-red-700' },
              ].map(s => (
                <div key={s.label} className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${s.color} p-[1px]`}>
                  <div className="rounded-2xl bg-slate-950/90 backdrop-blur-sm p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-[10px] font-medium text-white/60 uppercase tracking-wider">{s.label}</p>
                        <p className="text-lg font-bold text-white mt-1">{s.value}</p>
                      </div>
                      <s.icon className="w-5 h-5 text-white/30" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === 'builder' && (
          <div className="max-w-2xl space-y-4">
            <Card>
              <CardSection label="New Pipeline">
                <div className="space-y-4">
                  <input type="text" value={newName} onChange={e => setNewName(e.target.value)}
                    placeholder="Pipeline name" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                  />

                  {/* Task list */}
                  <div className="space-y-2">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">Tasks ({newTasks.length})</p>
                    {newTasks.length === 0 ? (
                      <div className="text-center py-6 rounded-xl border border-dashed border-white/10">
                        <Plus className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                        <p className="text-xs text-slate-500">No tasks yet — add one below</p>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        {newTasks.map((t, i) => {
                          const Icon = getModuleIcon(t.module);
                          const color = getModuleColor(t.module);
                          return (
                            <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/5 text-xs group">
                              <div className="flex flex-col gap-0.5">
                                <button onClick={() => moveTask(i, 'up')} disabled={i === 0} className="p-0.5 text-slate-600 hover:text-white disabled:opacity-30"><ArrowUp className="w-3 h-3" /></button>
                                <button onClick={() => moveTask(i, 'down')} disabled={i === newTasks.length - 1} className="p-0.5 text-slate-600 hover:text-white disabled:opacity-30"><ArrowDown className="w-3 h-3" /></button>
                              </div>
                              <Icon className={`w-4 h-4 shrink-0 ${color}`} />
                              <span className="flex-1 text-slate-300">{t.action || t.module}</span>
                              <button onClick={() => removeBuilderTask(i)}
                                className="p-1 text-slate-500 hover:text-red-400"
                              ><Trash2 className="w-3.5 h-3.5" /></button>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Add task form */}
                  <div className="border-t border-white/5 pt-4 space-y-3">
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider">Add Task</p>
                    <div className="grid grid-cols-3 gap-3">
                      <select value={newModule} onChange={e => setNewModule(e.target.value)}
                        className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-lumina-500/50"
                      >{MODULES.map(m => <option key={m.key} value={m.key}>{m.label}</option>)}</select>
                      <input type="text" value={newAction} onChange={e => setNewAction(e.target.value)}
                        placeholder="Action (e.g. navigate)" className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                      />
                      <input type="text" value={newParams} onChange={e => setNewParams(e.target.value)}
                        placeholder='Params (JSON, e.g. {"url":"..."})' className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-lumina-500/50"
                      />
                    </div>
                    <button onClick={addTaskToBuilder} disabled={!newAction}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 disabled:opacity-40 transition-colors"
                    ><Plus className="w-3.5 h-3.5" />Add Task</button>
                  </div>

                  {/* Save */}
                  <button onClick={createPipeline} disabled={!newName.trim() || newTasks.length === 0}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-lumina-500 to-lumina-600 rounded-xl text-xs font-medium text-white disabled:opacity-40 hover:from-lumina-400 hover:to-lumina-500 transition-all shadow-lg shadow-lumina-500/20"
                  ><Save className="w-3.5 h-3.5" />Save Pipeline</button>
                </div>
              </CardSection>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
