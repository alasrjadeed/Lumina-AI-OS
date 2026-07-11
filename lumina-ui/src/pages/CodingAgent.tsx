import { useState, useRef, useEffect } from 'react';
import {
  Bot, Code2, Play, Loader2, CheckCircle, XCircle, AlertCircle,
  GitCommit, FileSearch, TestTube, RefreshCw,
  Wrench, Brain, BookOpen, Settings2, ChevronRight,
  FolderOpen, FileCode, Terminal, Bug, Star,
} from 'lucide-react';

interface Phase {
  phase: string;
  status: string;
  ok?: number;
  total?: number;
  steps?: number;
  summary?: string;
  error?: string;
  project_type?: string;
  attempts?: number;
  iterations?: number;
}

export default function CodingAgent() {
  const [task, setTask] = useState('');
  const [projectPath, setProjectPath] = useState('.');
  const [running, setRunning] = useState(false);
  const [phases, setPhases] = useState<Phase[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  const [memory, setMemory] = useState<any>(null);
  const [understand, setUnderstand] = useState<any>(null);
  const [tab, setTab] = useState<'agent' | 'memory' | 'explorer'>('agent');
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { fetchMemory(); }, []);

  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);

  const fetchMemory = async () => {
    try {
      const r = await fetch('/coding-agent/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: 'all', action: 'get' }),
      });
      setMemory(await r.json());
    } catch {}
  };

  const addLog = (msg: string) => setLogs(l => [...l, msg]);

  const runPipeline = async () => {
    if (!task.trim() || running) return;
    setRunning(true);
    setResult(null);
    setPhases([]);
    setLogs([]);
    addLog(`🚀 Starting: "${task}"`);
    addLog(`📁 Project: ${projectPath}`);

    try {
      const r = await fetch('/coding-agent/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, project_path: projectPath, auto_commit: false }),
      });
      const data = await r.json();

      setResult(data);
      setPhases(data.phases || []);
      (data.phases || []).forEach((p: Phase) => {
        const icon = p.status === 'ok' ? '✅' : p.status === 'skipped' ? '⏭️' : '❌';
        addLog(`${icon} ${p.phase}: ${p.status}${p.summary ? ` — ${p.summary}` : ''}${p.error ? ` — ${p.error}` : ''}`);
      });
      addLog(`⏱️ Duration: ${data.duration_seconds}s`);
      addLog(data.success ? '✅ All phases complete!' : '❌ Some phases failed');
      await fetchMemory();
    } catch (e: any) {
      addLog(`❌ Error: ${e.message}`);
    }
    setRunning(false);
  };

  const understandProject = async () => {
    addLog(`📖 Understanding project: ${projectPath}...`);
    try {
      const r = await fetch('/coding-agent/understand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: projectPath }),
      });
      const data = await r.json();
      setUnderstand(data);
      addLog(`📁 ${data.file_count} files, ${data.dir_count} dirs — ${data.project_type}`);
      addLog(`🧠 ${data.memory?.known_bugs?.length || 0} known bugs, ${Object.keys(data.memory?.coding_style || {}).length} style rules`);
    } catch (e: any) {
      addLog(`❌ ${e.message}`);
    }
  };

  const quickTasks = [
    'Add dark mode support',
    'Fix all TypeScript errors',
    'Add input validation',
    'Optimize database queries',
    'Add error handling',
    'Refactor the main component',
    'Add unit tests',
  ];

  const phaseIcons: Record<string, any> = {
    understand: FileSearch,
    plan: Brain,
    execute: Code2,
    test: TestTube,
    heal: Wrench,
    commit: GitCommit,
  };

  const phaseLabels: Record<string, string> = {
    understand: 'Understanding',
    plan: 'Planning',
    execute: 'Executing',
    test: 'Testing',
    heal: 'Healing',
    commit: 'Committing',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <Bot className="w-7 h-7 text-lumina-400" /> Coding Agent
          </h1>
          <p className="text-sm text-slate-400 mt-1">Autonomous AI software engineer — tell it what to build</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-xs text-slate-400">
            <Brain className="w-3.5 h-3.5 text-lumina-400" />
            {memory?.bugs?.length || 0} bugs remembered
          </div>
          <button onClick={() => { setLogs([]); setResult(null); setPhases([]); }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-400 hover:text-slate-200 transition-all">
            <RefreshCw className="w-3.5 h-3.5" /> Clear
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/5 w-fit">
        {(['agent', 'memory', 'explorer'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              tab === t ? 'bg-lumina-600/20 text-lumina-300' : 'text-slate-500 hover:text-slate-300'
            }`}>
            {t === 'agent' ? <Bot className="w-3.5 h-3.5" /> : t === 'memory' ? <BookOpen className="w-3.5 h-3.5" /> : <FolderOpen className="w-3.5 h-3.5" />}
            {t === 'agent' ? 'Agent' : t === 'memory' ? `Memory (${memory?.bugs?.length || 0})` : 'Explorer'}
          </button>
        ))}
      </div>

      {tab === 'agent' && (
        <>
          {/* Input */}
          <div className="bento-card">
            <div className="flex gap-3 mb-3">
              <input value={task} onChange={e => setTask(e.target.value)}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-5 py-3.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50"
                placeholder='e.g. "Add Dark Mode support"'
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), runPipeline())} />
              <button onClick={runPipeline} disabled={running || !task.trim()}
                className="px-6 py-3 rounded-xl bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-sm font-medium transition-all flex items-center gap-2">
                {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {running ? 'Working...' : 'Run'}
              </button>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 flex-1">
                <FolderOpen className="w-3.5 h-3.5 text-slate-500" />
                <input value={projectPath} onChange={e => setProjectPath(e.target.value)}
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none font-mono focus:border-lumina-500/50"
                  placeholder="Project path (default: .)" />
              </div>
              <button onClick={understandProject} disabled={running}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 hover:text-white transition-all flex items-center gap-1.5 disabled:opacity-50">
                <FileSearch className="w-3.5 h-3.5" /> Understand
              </button>
            </div>
          </div>

          {/* Quick tasks */}
          <div className="flex flex-wrap gap-2">
            {quickTasks.map(ex => (
              <button key={ex} onClick={() => setTask(ex)}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-[11px] text-slate-400 hover:text-slate-200 transition-all">
                {ex}
              </button>
            ))}
          </div>

          {/* Pipeline visualization */}
          <div className="bento-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Pipeline</h2>
            <div className="flex items-center gap-1 mb-6 overflow-x-auto pb-2">
              {['understand', 'plan', 'execute', 'test', 'heal', 'commit'].map((phase, i) => {
                const found = phases.find(p => p.phase === phase);
                const Icon = phaseIcons[phase];
                const isActive = running && phases.length === i;
                const isDone = found?.status === 'ok';
                const isError = found?.status === 'error' || found?.status === 'failed';
                const isSkipped = found?.status === 'skipped';
                return (
                  <div key={phase} className="flex items-center gap-1">
                    <div className={`flex flex-col items-center px-3 py-2 rounded-xl border transition-all min-w-[80px] ${
                      isDone ? 'bg-emerald-500/10 border-emerald-500/20' :
                      isError ? 'bg-red-500/10 border-red-500/20' :
                      isSkipped ? 'bg-slate-800/50 border-slate-700/30 text-slate-500' :
                      isActive ? 'bg-lumina-500/10 border-lumina-500/20 animate-pulse' :
                      'bg-white/[0.02] border-white/5 text-slate-500'
                    }`}>
                      <Icon className={`w-5 h-5 mb-1 ${
                        isDone ? 'text-emerald-400' : isError ? 'text-red-400' :
                        isActive ? 'text-lumina-400' : 'text-slate-500'
                      }`} />
                      <span className="text-[10px] font-medium">{phaseLabels[phase]}</span>
                      {found && (
                        <span className={`text-[9px] mt-0.5 ${
                          isDone ? 'text-emerald-400' : isError ? 'text-red-400' : 'text-slate-600'
                        }`}>
                          {isDone ? (found.ok !== undefined ? `${found.ok}/${found.total}` : '✓') :
                           isError ? '✗' : isSkipped ? '—' : ''}
                        </span>
                      )}
                    </div>
                    {i < 5 && <ChevronRight className="w-4 h-4 text-slate-700 shrink-0" />}
                  </div>
                );
              })}
            </div>

            {/* Phase details */}
            {phases.length > 0 && (
              <div className="space-y-2">
                {phases.map((p, i) => (
                  <div key={i} className={`flex items-start gap-3 px-4 py-3 rounded-xl border text-sm ${
                    p.status === 'ok' ? 'bg-emerald-500/5 border-emerald-500/10' :
                    p.status === 'error' || p.status === 'failed' ? 'bg-red-500/5 border-red-500/10' :
                    p.status === 'skipped' ? 'bg-slate-800/30 border-slate-700/30' :
                    'bg-amber-500/5 border-amber-500/10'
                  }`}>
                    {p.status === 'ok' ? <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" /> :
                     p.status === 'skipped' ? <AlertCircle className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" /> :
                     <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />}
                    <div>
                      <p className="text-slate-200 font-medium capitalize">{p.phase}</p>
                      {p.summary && <p className="text-xs text-slate-400 mt-0.5">{p.summary}</p>}
                      {p.error && <p className="text-xs text-red-400 mt-0.5 font-mono">{p.error}</p>}
                      {p.ok !== undefined && <p className="text-xs text-slate-500 mt-0.5">{p.ok}/{p.total} steps succeeded</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Log */}
          <div className="bento-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-lumina-400" /> Log
            </h2>
            <div className="space-y-1 max-h-[300px] overflow-auto font-mono text-xs">
              {logs.map((l, i) => (
                <div key={i} className={`px-2 py-1 rounded ${
                  l.startsWith('✅') ? 'text-emerald-400' :
                  l.startsWith('❌') ? 'text-red-400' :
                  l.startsWith('🚀') ? 'text-lumina-400 font-semibold' :
                  l.startsWith('📁') || l.startsWith('📖') || l.startsWith('🧠') || l.startsWith('⏱️') || l.startsWith('⏭️') ? 'text-slate-300' :
                  'text-slate-500'
                }`}>{l}</div>
              ))}
              <div ref={logEndRef} />
            </div>
          </div>

          {/* Full result JSON */}
          {result && !result.success && (
            <div className="bento-card">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Bug className="w-4 h-4 text-red-400" /> Raw Output
              </h2>
              <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap bg-white/[0.02] rounded-xl p-4 border border-white/5 max-h-[400px] overflow-auto">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </>
      )}

      {tab === 'memory' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bugs */}
          <div className="bento-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
              <Bug className="w-4 h-4 text-red-400" /> Known Bugs ({memory?.bugs?.length || 0})
            </h2>
            {memory?.bugs?.length > 0 ? (
              <div className="space-y-2 max-h-[400px] overflow-auto">
                {[...memory.bugs].reverse().slice(0, 20).map((bug: any, i: number) => (
                  <div key={i} className="px-3 py-2.5 rounded-lg bg-white/[0.02] border border-white/5">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-300 font-medium">{bug.project || 'Unknown'}</span>
                      <span className="text-[10px] text-slate-600">{bug.timestamp ? new Date(bug.timestamp * 1000).toLocaleDateString() : ''}</span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono truncate">{bug.error || bug.task || ''}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500 text-center py-8">No bugs remembered yet</p>
            )}
          </div>

          {/* Style & Preferences */}
          <div className="space-y-4">
            <div className="bento-card">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Star className="w-4 h-4 text-amber-400" /> Coding Style
              </h2>
              {memory?.style && Object.keys(memory.style).length > 0 ? (
                <div className="space-y-1">
                  {Object.entries(memory.style).map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">{k}</span>
                      <span className="text-slate-300 font-mono">{String(v)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500">No style configured. The agent will learn from your projects.</p>
              )}
            </div>

            <div className="bento-card">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Settings2 className="w-4 h-4 text-lumina-400" /> Preferences
              </h2>
              {memory?.preferences && Object.keys(memory.preferences).length > 0 ? (
                <div className="space-y-1">
                  {Object.entries(memory.preferences).map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">{k}</span>
                      <span className="text-slate-300">{String(v)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500">No preferences stored yet.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {tab === 'explorer' && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <input value={projectPath} onChange={e => setProjectPath(e.target.value)}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none font-mono focus:border-lumina-500/50"
              placeholder="Project path" />
            <button onClick={understandProject} disabled={running}
              className="px-5 py-2.5 rounded-xl bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 text-white text-sm font-medium transition-all flex items-center gap-2">
              <FileSearch className="w-4 h-4" /> Analyze
            </button>
          </div>

          {understand && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="bento-card">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Project</h2>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between"><span className="text-slate-500">Name</span><span className="text-slate-200">{understand.project_name}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Type</span><span className="text-slate-200">{understand.project_type}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Files</span><span className="text-slate-200">{understand.file_count}</span></div>
                  <div className="flex justify-between"><span className="text-slate-500">Dirs</span><span className="text-slate-200">{understand.dir_count}</span></div>
                </div>
              </div>

              <div className="lg:col-span-2 bento-card">
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Key Files</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-1.5 max-h-[300px] overflow-auto">
                  {understand.files?.slice(0, 60).map((f: any) => (
                    <div key={f.path} className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/[0.02] text-[11px] text-slate-400 font-mono truncate hover:bg-white/5">
                      <FileCode className="w-3 h-3 shrink-0 text-slate-600" />
                      <span className="truncate">{f.path}</span>
                    </div>
                  ))}
                </div>
              </div>

              {understand.memory?.known_bugs?.length > 0 && (
                <div className="lg:col-span-3 bento-card">
                  <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Previous Bugs (from memory)</h2>
                  <div className="space-y-1">
                    {understand.memory.known_bugs.map((bug: any, i: number) => (
                      <div key={i} className="text-xs text-slate-500 font-mono px-2 py-1 rounded bg-white/[0.02]">{bug}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
