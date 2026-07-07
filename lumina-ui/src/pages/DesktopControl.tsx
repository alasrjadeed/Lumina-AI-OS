import { useState, useEffect, useCallback } from 'react';
import {
  Monitor, Play, Loader2, CheckCircle, XCircle, AlertCircle,
  Terminal, Grid3X3, Maximize2, Minimize2, X, Clipboard,
  Bell, HardDrive, Cpu, BarChart3, ExternalLink, Palette,
  Globe, Code2, FileText, Send, ChevronRight, RefreshCw,
} from 'lucide-react';

interface CmdResult {
  action: string;
  status: string;
  detail?: string;
  data?: any;
  return_code?: number;
}

const quickApps = [
  { name: 'code', label: 'VS Code', icon: Code2 },
  { name: 'google-chrome', label: 'Chrome', icon: Globe },
  { name: 'firefox', label: 'Firefox', icon: Globe },
  { name: 'gnome-terminal', label: 'Terminal', icon: Terminal },
  { name: 'gimp', label: 'GIMP', icon: Palette },
  { name: 'spotify', label: 'Spotify', icon: ExternalLink },
];

const examples = [
  'Open VS Code and Chrome',
  'Open Terminal and run ls -la',
  'Show me my system info',
  'Create a folder called projects',
  'Send a notification saying "Task done"',
  'Maximize the terminal window',
  'List all running windows',
];

export default function DesktopControl() {
  const [task, setTask] = useState('');
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<CmdResult[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [apps, setApps] = useState<any[]>([]);
  const [windows, setWindows] = useState<any[]>([]);
  const [clipboard, setClipboard] = useState('');
  const [tab, setTab] = useState<'agent' | 'apps' | 'windows' | 'system'>('agent');

  const fetchStats = useCallback(async () => {
    try {
      const r = await fetch('/desktop/stats');
      setStats(await r.json());
    } catch {}
  }, []);

  const fetchApps = useCallback(async () => {
    try {
      const r = await fetch('/desktop/apps?running_only=true');
      const d = await r.json();
      setApps(d.apps || []);
    } catch {}
  }, []);

  const fetchWindows = useCallback(async () => {
    try {
      const r = await fetch('/desktop/windows');
      const d = await r.json();
      setWindows(d.windows || []);
    } catch {}
  }, []);

  const fetchClipboard = useCallback(async () => {
    try {
      const r = await fetch('/desktop/clipboard');
      const d = await r.json();
      setClipboard(d.content || '');
    } catch {}
  }, []);

  useEffect(() => { fetchStats(); fetchWindows(); }, []);

  const runAgent = async () => {
    if (!task.trim() || running) return;
    setRunning(true);
    setResults([]);
    setLogs(l => [...l, `> ${task}`]);
    try {
      const r = await fetch('/desktop/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, timeout: 60 }),
      });
      const data = await r.json();
      setResults(data.results || []);
      setLogs(l => [...l, ...(data.results || []).map((res: any) =>
        `${res.status === 'ok' ? '✓' : '✗'} ${res.action}: ${res.detail || ''}`
      )]);
      setLogs(l => [...l, `Done in ${data.duration_seconds}s`]);
      await fetchApps();
      await fetchWindows();
    } catch (e: any) {
      setLogs(l => [...l, `Error: ${e.message}`]);
    }
    setRunning(false);
    setTask('');
  };

  const launchApp = async (name: string) => {
    setLogs(l => [...l, `> Launching ${name}...`]);
    try {
      const r = await fetch('/desktop/apps/launch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, path: name, args: [] }),
      });
      const d = await r.json();
      setLogs(l => [...l, `✓ ${name} launched (PID ${d.app?.pid || '?'})`]);
      await fetchApps();
    } catch (e: any) {
      setLogs(l => [...l, `✗ ${name}: ${e.message}`]);
    }
  };

  const winAction = async (action: string, title: string) => {
    setLogs(l => [...l, `> ${action} "${title}"...`]);
    try {
      await fetch(`/desktop/windows/${action}?title=${encodeURIComponent(title)}`, { method: 'POST' });
      setLogs(l => [...l, `✓ ${action} ${title}`]);
      await fetchWindows();
    } catch (e: any) {
      setLogs(l => [...l, `✗ ${e.message}`]);
    }
  };

  const formatBytes = (b: number) => {
    if (!b) return '0 B';
    const u = ['B','KB','MB','GB','TB'];
    const i = Math.floor(Math.log(b) / Math.log(1024));
    return `${(b / Math.pow(1024, i)).toFixed(1)} ${u[i]}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <Monitor className="w-7 h-7 text-lumina-400" /> Desktop Control
          </h1>
          <p className="text-sm text-slate-400 mt-1">Your AI employee — tell it what to do on your computer</p>
        </div>
        <button onClick={() => { fetchStats(); fetchApps(); fetchWindows(); fetchClipboard(); }}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-400 hover:text-slate-200 transition-all">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Quick Launch + Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3 bento-card">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Launch</h2>
          <div className="flex flex-wrap gap-2">
            {quickApps.map(a => (
              <button key={a.name} onClick={() => launchApp(a.name)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white/5 hover:bg-lumina-600/15 border border-white/5 hover:border-lumina-500/30 text-xs text-slate-300 hover:text-lumina-300 transition-all">
                <a.icon className="w-4 h-4" /> {a.label}
              </button>
            ))}
          </div>
        </div>
        <div className="bento-card">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">System</h2>
          {stats ? (
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between"><span className="text-slate-500">CPU</span><span className="text-slate-300">{stats.cpu_count} cores</span></div>
              <div className="flex items-center justify-between"><span className="text-slate-500">Disk</span><span className="text-slate-300">{stats.disk_percent}% used</span></div>
              <div className="w-full bg-slate-800 rounded-full h-1.5"><div className="bg-lumina-500 h-1.5 rounded-full" style={{ width: `${stats.disk_percent}%` }} /></div>
              <div className="flex items-center justify-between text-[10px] text-slate-600">
                <span>{formatBytes(stats.disk_used)}</span>
                <span>{formatBytes(stats.disk_total)}</span>
              </div>
              <div className="text-slate-600 truncate">{stats.hostname}</div>
            </div>
          ) : <p className="text-xs text-slate-500">Loading...</p>}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/5 w-fit">
        {(['agent', 'apps', 'windows', 'system'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${tab === t ? 'bg-lumina-600/20 text-lumina-300' : 'text-slate-500 hover:text-slate-300'}`}>
            {t === 'agent' ? 'AI Agent' : t === 'apps' ? `Apps (${apps.length})` : t === 'windows' ? `Windows (${windows.length})` : 'System'}
          </button>
        ))}
      </div>

      {tab === 'agent' && (
        <div className="space-y-4">
          {/* Command Input */}
          <div className="bento-card">
            <div className="flex gap-3">
              <input value={task} onChange={e => setTask(e.target.value)}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-5 py-3.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50"
                placeholder="Tell me what to do... e.g. Open VS Code and Chrome"
                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), runAgent())} />
              <button onClick={runAgent} disabled={running || !task.trim()}
                className="px-6 py-3 rounded-xl bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white text-sm font-medium transition-all flex items-center gap-2">
                {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {running ? 'Working...' : 'Execute'}
              </button>
            </div>
          </div>

          {/* Examples */}
          <div className="flex flex-wrap gap-2">
            {examples.map(ex => (
              <button key={ex} onClick={() => setTask(ex)}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-[11px] text-slate-400 hover:text-slate-200 transition-all">
                {ex}
              </button>
            ))}
          </div>

          {/* Results + Logs */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bento-card">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Results</h2>
              {results.length > 0 ? (
                <div className="space-y-2">
                  {results.map((r, i) => (
                    <div key={i} className={`flex items-start gap-3 px-3 py-2.5 rounded-lg border text-sm ${
                      r.status === 'ok' ? 'bg-emerald-500/5 border-emerald-500/10' :
                      r.status === 'error' ? 'bg-red-500/5 border-red-500/10' : 'bg-amber-500/5 border-amber-500/10'
                    }`}>
                      {r.status === 'ok' ? <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" /> :
                       r.status === 'error' ? <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" /> :
                       <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />}
                      <div>
                        <p className="text-slate-200 font-medium">{r.action}</p>
                        {r.detail && <p className="text-xs text-slate-400 mt-0.5">{r.detail}</p>}
                        {r.data && <pre className="text-[10px] text-slate-500 mt-1 font-mono">{JSON.stringify(r.data, null, 2)}</pre>}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500 text-center py-8">Results will appear here</p>
              )}
            </div>
            <div className="bento-card">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Log</h2>
              <div className="space-y-1 max-h-[400px] overflow-auto">
                {logs.length > 0 ? logs.map((l, i) => (
                  <div key={i} className={`text-xs font-mono px-2 py-1 rounded ${
                    l.startsWith('✓') ? 'text-emerald-400' :
                    l.startsWith('✗') ? 'text-red-400' :
                    l.startsWith('>') ? 'text-lumina-400' : 'text-slate-500'
                  }`}>{l}</div>
                )) : (
                  <p className="text-xs text-slate-500 text-center py-8">Command log will appear here</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {tab === 'apps' && (
        <div className="bento-card">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Running Applications</h2>
          {apps.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {apps.map((a: any) => (
                <div key={a.name} className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <div>
                    <p className="text-sm text-slate-200 font-medium">{a.name}</p>
                    <p className="text-[10px] text-slate-500">PID {a.pid}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <button onClick={() => fetch('/desktop/apps/kill?' + new URLSearchParams({ name: a.name }), { method: 'POST' }).then(() => fetchApps())}
                      className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No tracked running applications. Launch one above.</p>
          )}
        </div>
      )}

      {tab === 'windows' && (
        <div className="bento-card">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Desktop Windows</h2>
          {windows.length > 0 ? (
            <div className="space-y-2">
              {windows.map((w: any) => (
                <div key={w.id} className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-all ${
                  w.focused ? 'bg-lumina-600/10 border-lumina-500/20' : 'bg-white/[0.02] border-white/5'
                }`}>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-slate-200 font-medium truncate">{w.title || '(no title)'}</p>
                    <p className="text-[10px] text-slate-500">{w.width}×{w.height} {w.maximized ? '(maximized)' : w.minimized ? '(minimized)' : ''}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0 ml-3">
                    <button onClick={() => winAction('focus', w.title)} className="p-1.5 rounded-lg hover:bg-lumina-500/10 text-slate-500 hover:text-lumina-400 transition-all" title="Focus"><Maximize2 className="w-3.5 h-3.5" /></button>
                    <button onClick={() => winAction('minimize', w.title)} className="p-1.5 rounded-lg hover:bg-lumina-500/10 text-slate-500 hover:text-lumina-400 transition-all" title="Minimize"><Minimize2 className="w-3.5 h-3.5" /></button>
                    <button onClick={() => winAction('close', w.title)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-all" title="Close"><X className="w-3.5 h-3.5" /></button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500 text-center py-8">No windows found (requires xdotool/wmctrl on Linux)</p>
          )}
        </div>
      )}

      {tab === 'system' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bento-card space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Clipboard</h2>
            <div className="flex gap-2">
              <button onClick={fetchClipboard}
                className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all">Read Clipboard</button>
            </div>
            {clipboard && (
              <pre className="text-xs text-slate-400 font-mono bg-white/[0.02] rounded-xl p-3 border border-white/5 max-h-[200px] overflow-auto whitespace-pre-wrap break-all">{clipboard}</pre>
            )}
          </div>
          <div className="bento-card space-y-3">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Quick Actions</h2>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => fetch('/desktop/notify?' + new URLSearchParams({ title: 'Lumina', message: 'Desktop Control active', level: 'info' }), { method: 'POST' })}
                className="px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all flex items-center gap-2">
                <Bell className="w-3.5 h-3.5" /> Test Notification
              </button>
              <button onClick={() => fetch('/desktop/apps/launch/terminal', { method: 'POST' })}
                className="px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5" /> Open Terminal
              </button>
              <button onClick={async () => {
                const r = await fetch('/desktop/execute', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ command: 'date' }),
                });
                const d = await r.json();
                setLogs(l => [...l, `> date: ${d.stdout}`]);
              }} className="px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all flex items-center gap-2">
                <BarChart3 className="w-3.5 h-3.5" /> Run: date
              </button>
              <button onClick={async () => {
                const r = await fetch('/desktop/processes');
                const d = await r.json();
                setLogs(l => [...l, `> ${d.count} processes running`]);
              }} className="px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-xs text-slate-300 transition-all flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5" /> List Processes
              </button>
            </div>
          </div>
          <div className="md:col-span-2 bento-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">System Log</h2>
            <div className="space-y-1 max-h-[200px] overflow-auto">
              {logs.filter(l => l.startsWith('>')).slice(-10).map((l, i) => (
                <div key={i} className="text-xs text-slate-500 font-mono px-2 py-1">{l}</div>
              ))}
              {logs.length === 0 && <p className="text-xs text-slate-500">No activity yet</p>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
