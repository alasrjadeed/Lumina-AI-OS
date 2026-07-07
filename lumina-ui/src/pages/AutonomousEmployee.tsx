import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Bot, Play, Loader2, CheckCircle, XCircle, Clock, AlertCircle,
  Sparkles, Globe, Code2, Terminal, FileText, Folder, BookOpen,
  Bell, Search, Activity, ChevronRight, Send, RefreshCw, Trash2,
  Brain, Zap, MessageSquare,
} from 'lucide-react';

interface ToolCall {
  tool: string;
  args: Record<string, any>;
  result?: string;
  status: string;
  error?: string;
}

interface Step {
  id: string;
  name: string;
  description: string;
  status: string;
  error?: string;
  tool_calls?: ToolCall[];
}

interface StreamEvent {
  type: string;
  mission_id?: string;
  step_id?: string;
  summary?: string;
  steps?: Step[];
  name?: string;
  description?: string;
  tool?: string;
  args?: Record<string, any>;
  result?: string;
  error?: string;
  report?: string;
  duration?: number;
  steps_total?: number;
  steps_ok?: number;
}

const toolIcons: Record<string, any> = {
  web_search: Search,
  web_fetch: Globe,
  execute_code: Code2,
  shell_command: Terminal,
  read_file: FileText,
  write_file: FileText,
  list_dir: Folder,
  remember: BookOpen,
  recall: BookOpen,
  send_notification: Bell,
};

const toolLabels: Record<string, string> = {
  web_search: 'Web Search',
  web_fetch: 'Fetch Page',
  execute_code: 'Execute Code',
  shell_command: 'Shell',
  read_file: 'Read File',
  write_file: 'Write File',
  list_dir: 'List Directory',
  remember: 'Remember',
  recall: 'Recall',
  send_notification: 'Notify',
};

export default function AutonomousEmployee() {
  const [goal, setGoal] = useState('');
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [report, setReport] = useState('');
  const [output, setOutput] = useState<string[]>([]);
  const [activeTool, setActiveTool] = useState<string | null>(null);
  const [tools, setTools] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [memory, setMemory] = useState<any>(null);
  const [tab, setTab] = useState<'execute' | 'history' | 'memory'>('execute');
  const logEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    fetch('/api/employee/tools').then(r => r.json()).then(d => setTools(d.tools || [])).catch(() => {});
    fetchHistory();
    fetchMemory();
  }, []);

  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [output]);

  const fetchHistory = async () => {
    try {
      const r = await fetch('/api/employee/history');
      const d = await r.json();
      setHistory(d.missions || []);
    } catch {}
  };

  const fetchMemory = async () => {
    try {
      const r = await fetch('/api/employee/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get' }),
      });
      const d = await r.json();
      setMemory(d);
    } catch {}
  };

  const execute = async () => {
    if (!goal.trim() || running) return;
    setRunning(true);
    setSteps([]);
    setReport('');
    setOutput([`🚀 Starting mission: "${goal}"`]);
    setActiveTool(null);

    try {
      const res = await fetch('/api/employee/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal }),
      });
      const data = await res.json();
      setSteps(data.steps || []);
      setReport(data.report || '');
      setOutput(o => [...o,
        `✅ Completed in ${data.duration_seconds}s`,
        `📊 ${(data.steps || []).filter((s: any) => s.status === 'success').length}/${(data.steps || []).length} steps succeeded`,
      ]);
      fetchHistory();
      fetchMemory();
    } catch (e: any) {
      setOutput(o => [...o, `❌ Error: ${e.message}`]);
    }
    setRunning(false);
    setActiveTool(null);
  };

  // Cleanup
  useEffect(() => {
    return () => { eventSourceRef.current?.close(); };
  }, []);

  const statusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />;
      case 'failed': return <XCircle className="w-4 h-4 text-red-400 shrink-0" />;
      case 'running': return <Loader2 className="w-4 h-4 text-lumina-400 animate-spin shrink-0" />;
      case 'pending': return <Clock className="w-4 h-4 text-slate-600 shrink-0" />;
      default: return <AlertCircle className="w-4 h-4 text-slate-500 shrink-0" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-lumina-400 via-violet-500 to-emerald-500 flex items-center justify-center shadow-xl shadow-lumina-500/20">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Autonomous Employee</h1>
            <p className="text-sm text-slate-400">Multi-tool AI agent with web search, code exec, file ops & memory</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-500 bg-white/5 px-2 py-1 rounded-full">{tools.length} tools</span>
          <span className="text-[10px] text-slate-500 bg-white/5 px-2 py-1 rounded-full">{memory?.knowledge ? Object.keys(memory.knowledge).length : 0} facts</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/5 w-fit">
        {(['execute', 'history', 'memory'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              tab === t ? 'bg-lumina-600/20 text-lumina-300' : 'text-slate-500 hover:text-slate-300'
            }`}>
            {t === 'execute' ? <Zap className="w-3.5 h-3.5" /> : t === 'history' ? <Activity className="w-3.5 h-3.5" /> : <Brain className="w-3.5 h-3.5" />}
            {t === 'execute' ? 'Execute' : t === 'history' ? `History (${history.length})` : 'Memory'}
          </button>
        ))}
      </div>

      {tab === 'execute' && (
        <>
          {/* Input */}
          <div className="bento-card">
            <div className="flex gap-3">
              <input value={goal} onChange={e => setGoal(e.target.value)}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-5 py-3.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50"
                placeholder="Describe a mission... e.g. Research competitors and write a report"
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), execute())} />
              <button onClick={execute} disabled={running || !goal.trim()}
                className="bg-gradient-to-r from-lumina-500 to-violet-500 hover:from-lumina-400 hover:to-violet-400 disabled:from-slate-800 disabled:to-slate-800 text-white rounded-xl px-6 py-3 text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-lumina-500/20">
                {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                {running ? 'Working...' : 'Execute'}
              </button>
            </div>
          </div>

          {/* Quick missions */}
          <div className="flex flex-wrap gap-2">
            {[
              'Research competitors and summarize',
              'Search for latest AI news',
              'Create a project folder structure',
              'Write a Python script to sort files',
              'Remember my name is Alex',
            ].map(ex => (
              <button key={ex} onClick={() => setGoal(ex)}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-[11px] text-slate-400 hover:text-slate-200 transition-all">
                {ex}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Steps */}
            <div className="lg:col-span-2 space-y-3">
              {steps.length > 0 ? (
                steps.map((step, i) => (
                  <div key={step.id || i} className={`bento-card border transition-all ${
                    step.status === 'success' ? 'border-emerald-500/20' :
                    step.status === 'failed' ? 'border-red-500/20' : 'border-white/5'
                  }`}>
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">{statusIcon(step.status)}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm text-white font-medium">{step.name}</span>
                          <span className="text-[10px] text-slate-600 bg-white/5 px-1.5 py-0.5 rounded-full">{step.status}</span>
                        </div>
                        <p className="text-xs text-slate-400 mb-2">{step.description}</p>

                        {/* Tool calls */}
                        {step.tool_calls && step.tool_calls.length > 0 && (
                          <div className="space-y-1.5 mt-2">
                            {step.tool_calls.map((tc, j) => {
                              const TIcon = toolIcons[tc.tool] || Bot;
                              return (
                                <div key={j} className={`flex items-start gap-2.5 px-3 py-2 rounded-lg text-xs ${
                                  tc.status === 'success' ? 'bg-emerald-500/5 border border-emerald-500/10' :
                                  tc.status === 'failed' ? 'bg-red-500/5 border border-red-500/10' :
                                  'bg-white/[0.02] border border-white/5'
                                }`}>
                                  <TIcon className="w-3.5 h-3.5 text-lumina-400 shrink-0 mt-0.5" />
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className="text-slate-300 font-medium">{toolLabels[tc.tool] || tc.tool}</span>
                                      {tc.status === 'running' && <Loader2 className="w-3 h-3 text-lumina-400 animate-spin" />}
                                    </div>
                                    {tc.args && Object.keys(tc.args).length > 0 && (
                                      <p className="text-[10px] text-slate-500 font-mono truncate mt-0.5">
                                        {JSON.stringify(tc.args).slice(0, 100)}
                                      </p>
                                    )}
                                    {tc.result && (
                                      <p className="text-[10px] text-slate-400 font-mono mt-0.5 line-clamp-2">{tc.result}</p>
                                    )}
                                    {tc.error && (
                                      <p className="text-[10px] text-red-400 font-mono mt-0.5">{tc.error}</p>
                                    )}
                                  </div>
                                  {tc.status === 'success' && <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />}
                                  {tc.status === 'failed' && <XCircle className="w-3 h-3 text-red-400 shrink-0" />}
                                </div>
                              );
                            })}
                          </div>
                        )}

                        {step.error && (
                          <p className="text-xs text-red-400 mt-2 font-mono">{step.error}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="bento-card">
                  <div className="text-center py-12">
                    <Bot className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">Enter a mission above to start</p>
                    <p className="text-xs text-slate-600 mt-1">The AI employee will plan, use tools, and report results</p>
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-4">
              {/* Live output */}
              <div className="bento-card">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5" /> Live Output
                </h2>
                <div className="space-y-1 max-h-[500px] overflow-auto font-mono text-[11px]">
                  {output.map((l, i) => (
                    <div key={i} className={`px-2 py-0.5 rounded ${
                      l.startsWith('🚀') ? 'text-lumina-400 font-semibold' :
                      l.startsWith('✅') ? 'text-emerald-400' :
                      l.startsWith('❌') ? 'text-red-400' :
                      l.startsWith('📊') ? 'text-slate-300' :
                      'text-slate-500'
                    }`}>{l}</div>
                  ))}
                  {running && (
                    <div className="flex items-center gap-2 px-2 py-1 text-lumina-400">
                      <Loader2 className="w-3 h-3 animate-spin" />
                      AI employee working...
                    </div>
                  )}
                  <div ref={logEndRef} />
                </div>
              </div>

              {/* Available tools */}
              <div className="bento-card">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Tools</h2>
                <div className="space-y-1">
                  {tools.map((t: any) => {
                    const TIcon = toolIcons[t.name] || Bot;
                    return (
                      <div key={t.name}
                        className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-[11px] text-slate-400 hover:bg-white/5 transition-all cursor-default">
                        <TIcon className="w-3 h-3 text-lumina-400 shrink-0" />
                        <span className="truncate">{t.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Report */}
              {report && (
                <div className="bento-card bg-lumina-500/5 border-lumina-500/20">
                  <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Report</h2>
                  <p className="text-xs text-slate-300 leading-relaxed">{report}</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {tab === 'history' && (
        <div className="bento-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Mission History</h2>
            <button onClick={fetchHistory} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200">
              <RefreshCw className="w-3 h-3" /> Refresh
            </button>
          </div>
          {history.length > 0 ? (
            <div className="space-y-2">
              {[...history].reverse().map((m: any, i: number) => (
                <div key={m.id || i} className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm ${
                  m.success !== false ? 'bg-white/[0.02] border-white/5' : 'bg-red-500/5 border-red-500/10'
                }`}>
                  {m.success !== false
                    ? <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                    : <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-200 truncate">{m.goal || m.summary}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">
                      {m.completed ? new Date(m.completed * 1000).toLocaleString() : ''}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No missions completed yet</p>
          )}
        </div>
      )}

      {tab === 'memory' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bento-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Knowledge</h2>
            {memory?.knowledge && Object.keys(memory.knowledge).length > 0 ? (
              <div className="space-y-2">
                {Object.entries(memory.knowledge).map(([key, val]) => (
                  <div key={key} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                    <BookOpen className="w-3.5 h-3.5 text-lumina-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-xs text-slate-300 font-medium">{key}</p>
                      <p className="text-[11px] text-slate-500">{String(val).slice(0, 200)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 text-center py-8">No knowledge stored yet</p>
            )}
          </div>
          <div className="bento-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Context</h2>
            {memory?.contexts?.current ? (
              <div className="px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                <p className="text-xs text-slate-300">{memory.contexts.current}</p>
              </div>
            ) : (
              <p className="text-sm text-slate-500 text-center py-8">No context set</p>
            )}
            <div className="mt-4">
              <h3 className="text-xs text-slate-400 font-medium mb-2">Completed Missions</h3>
              <p className="text-sm text-slate-300">{history.length} missions completed</p>
            </div>
            <button onClick={async () => {
              await fetch('/api/employee/memory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'clear' }),
              });
              fetchMemory();
            }} className="mt-4 flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-xs text-red-400 transition-all">
              <Trash2 className="w-3.5 h-3.5" /> Clear Memory
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
