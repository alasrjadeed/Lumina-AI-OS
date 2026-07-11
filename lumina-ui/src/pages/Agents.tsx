import { useState, useEffect, useCallback } from 'react';
import {
  Bot, Play, Loader2, Plus, Trash2, Search,
  Code2, Globe, BarChart3, Bug, FileText, UserPlus, Mail,
  Phone, UserCheck, Headphones, Palette, PenTool, Video, Mic,
  PenLine, Megaphone, History, LayoutDashboard, Layers, ArrowRight,
  ChevronRight, RefreshCw, Zap, Timer,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/agents';

interface AgentInfo {
  id: string; name: string; category: string; description: string;
  icon: string; capabilities: string[]; system_prompt?: string;
}

interface AgentRun {
  run_id: string; agent_id: string; agent_name: string; task: string;
  status: string; output: string; error: string;
  started_at: string; completed_at: string; duration_ms: number;
  model: string; thinking: any[];
}

const ICON_MAP: Record<string, any> = {
  Code2, Globe, BarChart3, Bug, FileText, UserPlus, Mail,
  Phone, UserCheck, Headphones, Palette, PenTool, Video, Mic,
  PenLine, Megaphone, Search, Bot, Zap,
};

function getAgentIcon(name: string) {
  const meta: Record<string, string> = {
    software_engineer: 'Code2', web_developer: 'Globe',
    business_manager: 'BarChart3', marketing_manager: 'Megaphone',
    qa_engineer: 'Bug', data_analyst: 'BarChart3',
    research_analyst: 'Search', lead_gen: 'UserPlus',
    quotation: 'FileText', email_assistant: 'Mail',
    call_assistant: 'Phone', customer_success: 'UserCheck',
    documentation: 'FileText', voice_narrator: 'Headphones',
    designer: 'Palette', media_writer: 'PenTool',
    media_video: 'Video', media_podcast: 'Mic',
    content_writer: 'PenLine',
  };
  const iconName = meta[name] || 'Bot';
  return ICON_MAP[iconName] || Bot;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export default function Agents() {
  const [tab, setTab] = useState('dashboard');
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [_categories, setCategories] = useState<Record<string, AgentInfo[]>>({});
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AgentRun | null>(null);
  const [search, setSearch] = useState('');
  const { addToast } = useToast();

  // Workspace state
  const [selectedAgent, setSelectedAgent] = useState('');
  const [task, setTask] = useState('');
  const [agentSearch, setAgentSearch] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<AgentRun | null>(null);

  // Batch state
  const [batchTasks, setBatchTasks] = useState<{ agent_id: string; task: string }[]>([{ agent_id: '', task: '' }]);
  const [batchResults, setBatchResults] = useState<AgentRun[]>([]);
  const [batchRunning, setBatchRunning] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      const [catsData, historyData] = await Promise.all([
        get<Record<string, AgentInfo[]>>('/categories'),
        get<{ runs: AgentRun[] }>('/runs?limit=50'),
      ]);
      setCategories(catsData);
      const flat: AgentInfo[] = [];
      Object.values(catsData).forEach(arr => flat.push(...arr));
      setAgents(flat);
      setRuns(historyData.runs);
    } catch { addToast('Failed to load agents', 'error'); }
  }, [addToast]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const runAgent = async () => {
    if (!selectedAgent || !task.trim()) return;
    setRunning(true);
    setResult(null);
    try {
      const run = await post<AgentRun>('/run', { agent: selectedAgent, task });
      setResult(run);
      addToast(run.status === 'success' ? 'Agent completed' : 'Agent failed', run.status === 'success' ? 'success' : 'error');
      loadAll();
    } catch {
      addToast('Failed to run agent', 'error');
    }
    setRunning(false);
  };

  const runBatch = async () => {
    const valid = batchTasks.filter(t => t.agent_id && t.task.trim());
    if (valid.length === 0) { addToast('Add at least one task', 'error'); return; }
    setBatchRunning(true);
    setBatchResults([]);
    try {
      const res = await post<{ runs: AgentRun[] }>('/run/batch', {
        tasks: valid.map(t => ({ agent: t.agent_id, task: t.task })),
      });
      setBatchResults(res.runs);
      addToast(`${res.runs.filter(r => r.status === 'success').length}/${res.runs.length} completed`, 'success');
      loadAll();
    } catch { addToast('Batch run failed', 'error'); }
    setBatchRunning(false);
  };

  const filteredAgents = agents.filter(a =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.id.includes(search.toLowerCase()) ||
    a.description.toLowerCase().includes(search.toLowerCase())
  );

  const filteredAgentList = agents.filter(a =>
    a.name.toLowerCase().includes(agentSearch.toLowerCase()) ||
    a.id.includes(agentSearch.toLowerCase())
  );

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const tabs = [
    { id: 'dashboard', label: 'Agents', icon: LayoutDashboard },
    { id: 'workspace', label: 'Workspace', icon: Zap },
    { id: 'batch', label: 'Batch Run', icon: Layers },
    { id: 'history', label: `History (${runs.length})`, icon: History },
  ];

  return (
    <div className="p-6 space-y-6">
      <PageHeader icon={Bot} title="Agent Runner" description="Run AI agents on custom tasks" />

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

      {/* Dashboard - Agent Cards */}
      {tab === 'dashboard' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 flex-1 border border-white/10">
              <Search className="w-4 h-4 text-slate-500" />
              <input value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Search agents..." />
            </div>
            <span className="text-xs text-slate-500">{agents.length} agents</span>
          </div>

          {(['base', 'specialized', 'content'] as const).map(cat => {
            const catAgents = filteredAgents.filter(a => a.category === cat);
            if (catAgents.length === 0) return null;
            return (
              <div key={cat}>
                <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-1">{cat} ({catAgents.length})</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {catAgents.map(a => {
                    const Icon = getAgentIcon(a.id);
                    return (
                      <button key={a.id} onClick={() => { setSelectedAgent(a.id); setTab('workspace'); }}
                        className="text-left bg-white/[0.02] border border-white/10 hover:border-lumina-500/30 hover:bg-white/[0.04] rounded-xl p-4 transition-all group">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-xl bg-lumina-600/15 text-lumina-400 flex items-center justify-center shrink-0 group-hover:bg-lumina-600/25 transition-colors">
                            <Icon className="w-5 h-5" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-slate-200 truncate">{a.name}</p>
                            <p className="text-[10px] text-slate-500 truncate mt-0.5">{a.description}</p>
                            <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                              {a.capabilities?.slice(0, 3).map(c => (
                                <span key={c} className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500">{c}</span>
                              ))}
                            </div>
                          </div>
                          <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-lumina-400 transition-colors shrink-0 mt-1" />
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Workspace */}
      {tab === 'workspace' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card hover={false} className="space-y-4">
              <CardSection label="Select Agent">
                <div className="relative">
                  <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 border border-white/10">
                    <Search className="w-4 h-4 text-slate-500" />
                    <input value={agentSearch} onChange={e => setAgentSearch(e.target.value)}
                      className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                      placeholder="Search agents..." />
                  </div>
                  <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-1.5 max-h-48 overflow-y-auto">
                    {filteredAgentList.map(a => {
                      const Icon = getAgentIcon(a.id);
                      return (
                        <button key={a.id} onClick={() => setSelectedAgent(a.id)}
                          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-all ${
                            selectedAgent === a.id ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'bg-white/5 text-slate-400 hover:text-slate-200 border border-transparent'
                          }`}>
                          <Icon className="w-3.5 h-3.5 shrink-0" />
                          <span className="truncate">{a.name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </CardSection>
              <CardSection label="Task">
                <textarea value={task} onChange={e => setTask(e.target.value)} rows={4}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 resize-none"
                  placeholder="Describe the task for this agent..." />
              </CardSection>
              <button onClick={runAgent} disabled={running || !selectedAgent || !task.trim()}
                className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-6 py-2.5 text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-lumina-500/20 w-fit">
                {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {running ? 'Running...' : `Run${selectedAgent ? ' ' + agents.find(a => a.id === selectedAgent)?.name || '' : ''}`}
              </button>
            </Card>

            {result && (
              <Card hover={false} className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${result.status === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                    <span className="text-sm font-medium text-slate-200">{result.agent_name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      result.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                    }`}>{result.status}</span>
                    <span className="text-[10px] text-slate-600 flex items-center gap-1"><Timer className="w-3 h-3" /> {formatDuration(result.duration_ms)}</span>
                  </div>
                </div>
                <div className="bg-slate-950/50 rounded-xl p-4 border border-white/5">
                  {result.status === 'success' ? (
                    <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">{result.output}</pre>
                  ) : (
                    <pre className="text-sm text-red-400 whitespace-pre-wrap font-mono">{result.error}</pre>
                  )}
                </div>
              </Card>
            )}
          </div>

          <div className="space-y-4">
            <Card hover={false} className="space-y-4 sticky top-4">
              <CardSection label="Agent Info">
                {selectedAgent ? (() => {
                  const a = agents.find(x => x.id === selectedAgent);
                  if (!a) return <p className="text-xs text-slate-500">Select an agent</p>;
                  const Icon = getAgentIcon(a.id);
                  return (
                    <div className="space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-lumina-600/15 text-lumina-400 flex items-center justify-center">
                          <Icon className="w-6 h-6" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-200">{a.name}</p>
                          <p className="text-[10px] text-slate-500">{a.id}</p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-400">{a.description}</p>
                      <div>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Capabilities</p>
                        <div className="flex flex-wrap gap-1">
                          {a.capabilities?.map(c => (
                            <span key={c} className="text-[9px] px-2 py-0.5 rounded-full bg-white/5 text-slate-400">{c}</span>
                          ))}
                        </div>
                      </div>
                      <div className="text-[10px] text-slate-600">
                        <p>Category: {a.category}</p>
                        <p>Recent runs: {runs.filter(r => r.agent_id === a.id).length}</p>
                      </div>
                    </div>
                  );
                })() : (
                  <p className="text-xs text-slate-500">Select an agent to see details</p>
                )}
              </CardSection>
            </Card>
          </div>
        </div>
      )}

      {/* Batch Run */}
      {tab === 'batch' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <Card hover={false} className="space-y-4">
              <CardSection label="Batch Tasks" action={
                <button onClick={() => setBatchTasks(prev => [...prev, { agent_id: '', task: '' }])}
                  className="text-xs text-lumina-400 hover:text-lumina-300 flex items-center gap-1">
                  <Plus className="w-3 h-3" /> Add
                </button>
              }>
                {batchTasks.map((bt, idx) => (
                  <div key={idx} className="bg-white/[0.02] border border-white/10 rounded-xl p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-slate-500 font-medium">Task {idx + 1}</span>
                      {batchTasks.length > 1 && (
                        <button onClick={() => setBatchTasks(prev => prev.filter((_, i) => i !== idx))}
                          className="text-slate-500 hover:text-red-400 transition-colors">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                    <select value={bt.agent_id} onChange={e => {
                      const next = [...batchTasks];
                      next[idx] = { ...next[idx], agent_id: e.target.value };
                      setBatchTasks(next);
                    }}
                      className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-300 outline-none focus:border-lumina-500/50">
                      <option value="">Select agent...</option>
                      {agents.map(a => (
                        <option key={a.id} value={a.id}>{a.name}</option>
                      ))}
                    </select>
                    <textarea value={bt.task} onChange={e => {
                      const next = [...batchTasks];
                      next[idx] = { ...next[idx], task: e.target.value };
                      setBatchTasks(next);
                    }} rows={2}
                      className="w-full bg-slate-950 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 resize-none"
                      placeholder="Task description..." />
                  </div>
                ))}
              </CardSection>
              <button onClick={runBatch} disabled={batchRunning}
                className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-6 py-2.5 text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-lumina-500/20">
                {batchRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Layers className="w-4 h-4" />}
                {batchRunning ? 'Running...' : `Run ${batchTasks.filter(t => t.agent_id && t.task.trim()).length} Tasks`}
              </button>
            </Card>
          </div>

          <div className="space-y-3">
            {batchResults.length > 0 && (
              <Card hover={false} className="space-y-3">
                <CardSection label={`Results (${batchResults.filter(r => r.status === 'success').length}/${batchResults.length})`}>
                  {batchResults.map((r, _i) => (
                    <div key={r.run_id} className={`rounded-xl border p-4 ${
                      r.status === 'success' ? 'bg-emerald-500/5 border-emerald-800/30' : 'bg-red-500/5 border-red-800/30'
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${r.status === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                          <span className="text-xs font-medium text-slate-200">{r.agent_name}</span>
                          <span className="text-[10px] text-slate-600">{formatDuration(r.duration_ms)}</span>
                        </div>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                          r.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                        }`}>{r.status}</span>
                      </div>
                      <p className="text-[10px] text-slate-500 truncate mb-1">{r.task.slice(0, 100)}</p>
                      {r.status === 'success' ? (
                        <pre className="text-[10px] text-slate-400 whitespace-pre-wrap font-sans line-clamp-3">{r.output?.slice(0, 300)}</pre>
                      ) : (
                        <p className="text-[10px] text-red-400">{r.error}</p>
                      )}
                    </div>
                  ))}
                </CardSection>
              </Card>
            )}
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
                  <div className="flex items-center gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${selectedRun.status === 'success' ? 'bg-emerald-500' : 'bg-red-500'}`} />
                    <div>
                      <p className="text-sm font-medium text-slate-200">{selectedRun.agent_name}</p>
                      <p className="text-[10px] text-slate-500">{selectedRun.run_id} · {new Date(selectedRun.started_at).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-600 flex items-center gap-1"><Timer className="w-3 h-3" /> {formatDuration(selectedRun.duration_ms)}</span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${
                      selectedRun.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                    }`}>{selectedRun.status}</span>
                  </div>
                </div>
                <div className="bg-white/5 rounded-lg px-4 py-2">
                  <p className="text-[10px] text-slate-500 mb-1">Task</p>
                  <p className="text-xs text-slate-300">{selectedRun.task}</p>
                </div>
                <div className="bg-slate-950/50 rounded-xl p-4 border border-white/5">
                  <p className="text-[10px] text-slate-500 mb-2">Output</p>
                  {selectedRun.status === 'success' ? (
                    <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">{selectedRun.output}</pre>
                  ) : (
                    <pre className="text-xs text-red-400 font-mono whitespace-pre-wrap">{selectedRun.error}</pre>
                  )}
                </div>
              </Card>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <select onChange={e => {
                    const val = e.target.value;
                    get<{ runs: AgentRun[] }>(`/runs?limit=50${val ? `&agent_id=${val}` : ''}`).then(d => setRuns(d.runs)).catch(() => {});
                  }}
                    className="bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-slate-300 outline-none focus:border-lumina-500/50">
                    <option value="">All agents</option>
                    {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  </select>
                  <span className="text-xs text-slate-500">{runs.length} runs</span>
                </div>
                <button onClick={loadAll} className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              {runs.length === 0 ? (
                <Card hover={false} className="text-center py-12">
                  <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-sm text-slate-400">No runs yet</p>
                  <p className="text-xs text-slate-500 mt-1">Run an agent to see history here</p>
                </Card>
              ) : (
                <div className="space-y-2">
                  {runs.map(r => {
                    const Icon = getAgentIcon(r.agent_id);
                    return (
                      <Card key={r.run_id} onClick={() => setSelectedRun(r)} className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3 min-w-0">
                            <Icon className="w-4 h-4 text-lumina-400 shrink-0" />
                            <div className="min-w-0">
                              <p className="text-xs font-medium text-slate-200 truncate">{r.agent_name}</p>
                              <p className="text-[10px] text-slate-500 truncate">{r.task.slice(0, 80)}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <span className="text-[10px] text-slate-600">{formatDuration(r.duration_ms)}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                              r.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                              r.status === 'failed' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'
                            }`}>{r.status}</span>
                            <ChevronRight className="w-3 h-3 text-slate-500" />
                          </div>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
