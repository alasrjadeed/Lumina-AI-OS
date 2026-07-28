import { useState, useEffect, useCallback } from 'react';
import { Brain, Activity, Zap, Eye, Command, History, Play, Square, Clock, Target, Sparkles, AlertTriangle, CheckCircle, Loader2, RefreshCw } from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import { useToast } from '../hooks/useToast';

const BASE = '/api/brain';

type Thought = {
  id: string; timestamp: number; observation: Record<string, any>;
  analysis: string; commands: any[]; executed: boolean; results: any[] | null;
};

function ObservationCard({ label, data, icon: Icon }: { label: string; data: any; icon: any }) {
  return (
    <div className="bento-card p-3">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-3.5 h-3.5 text-lumina-400" />
        <span className="text-xs font-semibold text-[var(--text-primary)]">{label}</span>
      </div>
      <pre className="text-2xs text-[var(--text-tertiary)] overflow-auto max-h-24 font-mono">{JSON.stringify(data, null, 1)}</pre>
    </div>
  );
}

export default function BrainPage() {
  const [tab, setTab] = useState<'dashboard' | 'history' | 'observe'>('dashboard');
  const [thinking, setThinking] = useState(false);
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [thoughts, setThoughts] = useState<Thought[]>([]);
  const [observation, setObservation] = useState<any>(null);
  const [analysis, setAnalysis] = useState('');
  const [interval, setInterval] = useState(120);
  const { addToast } = useToast();

  const loadStatus = useCallback(async () => {
    try { setStatus(await (await fetch(`${BASE}/status`)).json()); } catch {}
  }, []);

  const loadHistory = useCallback(async () => {
    try { setThoughts(await (await fetch(`${BASE}/history`)).json()); } catch {}
  }, []);

  const loadObservation = useCallback(async () => {
    try { setObservation(await (await fetch(`${BASE}/observe`)).json()); } catch {}
  }, []);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  const handleThink = async () => {
    setThinking(true); setAnalysis('');
    try {
      const res = await fetch(`${BASE}/think`, { method: 'POST' });
      const thought: Thought = await res.json();
      setAnalysis(thought.analysis);
      setObservation(thought.observation);
      addToast('Brain finished thinking', 'success');
      loadHistory(); loadStatus();
    } catch { addToast('Thinking failed', 'error'); }
    setThinking(false);
  };

  const handleThinkAndCommand = async () => {
    setThinking(true); setAnalysis('');
    try {
      const res = await fetch(`${BASE}/think-and-command`, { method: 'POST' });
      const thought: Thought = await res.json();
      setAnalysis(thought.analysis);
      setObservation(thought.observation);
      addToast(`Brain completed ${thought.commands.length} commands`, 'success');
      loadHistory(); loadStatus();
    } catch { addToast('Think & command failed', 'error'); }
    setThinking(false);
  };

  const handleObserve = async () => {
    await loadObservation();
    addToast('Observation captured', 'success');
  };

  const handleToggleLoop = async () => {
    try {
      if (running) {
        await fetch(`${BASE}/stop`, { method: 'POST' });
        setRunning(false);
        addToast('Brain loop stopped', 'info');
      } else {
        await fetch(`${BASE}/start`, { method: 'POST' });
        setRunning(true);
        addToast('Brain loop started', 'success');
      }
    } catch { addToast('Failed to toggle loop', 'error'); }
    loadStatus();
  };

  const handleSetInterval = async () => {
    try {
      await fetch(`${BASE}/interval`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ interval }) });
      addToast(`Interval set to ${interval}s`, 'success');
    } catch { addToast('Failed to set interval', 'error'); }
  };

  const tabs = [
    { id: 'dashboard' as const, label: 'Dashboard', icon: Brain },
    { id: 'history' as const, label: 'History', icon: History },
    { id: 'observe' as const, label: 'Observe', icon: Eye },
  ];

  return (
    <div className="p-4 max-w-7xl mx-auto space-y-4">
      <PageHeader icon={Brain} title="Brain" description="Think. Observe. Command."
        status={
          <span className={`flex items-center gap-1.5 text-2xs px-2 py-1 rounded-full ${running ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${running ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
            {running ? 'Running' : 'Idle'}
          </span>
        }
      />

      <div className="flex items-center gap-2">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              tab === t.id ? 'bg-[var(--brand-500)] text-white shadow-lg shadow-[var(--brand-500)/20]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--bg-tertiary)]'
            }`}
          ><t.icon className="w-3.5 h-3.5" />{t.label}</button>
        ))}
      </div>

      {tab === 'dashboard' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
            <div className="bento-card p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 flex items-center justify-center"><Brain className="w-5 h-5 text-violet-400" /></div>
              <div><p className="text-2xs text-[var(--text-tertiary)]">Thoughts</p><p className="text-xl font-bold text-[var(--text-primary)]">{status?.total_thoughts || 0}</p></div>
            </div>
            <div className="bento-card p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 flex items-center justify-center"><Activity className="w-5 h-5 text-blue-400" /></div>
              <div><p className="text-2xs text-[var(--text-tertiary)]">Interval</p><p className="text-xl font-bold text-[var(--text-primary)]">{status?.thinking_interval || 120}s</p></div>
            </div>
            <div className="bento-card p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 flex items-center justify-center"><Zap className="w-5 h-5 text-amber-400" /></div>
              <div><p className="text-2xs text-[var(--text-tertiary)]">Status</p><p className="text-xl font-bold text-[var(--text-primary)]">{running ? 'Active' : 'Idle'}</p></div>
            </div>
            <div className="bento-card p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/20 to-green-500/20 flex items-center justify-center"><Target className="w-5 h-5 text-emerald-400" /></div>
              <div><p className="text-2xs text-[var(--text-tertiary)]">Commands</p><p className="text-xl font-bold text-[var(--text-primary)]">{status?.last_thought?.commands?.length || 0}</p></div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button onClick={handleThink} disabled={thinking}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--brand-500)] text-white hover:brightness-110 transition-all disabled:opacity-50">
              {thinking ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Think
            </button>
            <button onClick={handleThinkAndCommand} disabled={thinking}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:brightness-110 transition-all disabled:opacity-50">
              {thinking ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
              Think & Command
            </button>
            <button onClick={handleToggleLoop}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                running ? 'bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30'
              }`}>
              {running ? <Square className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
              {running ? 'Stop Loop' : 'Start Loop'}
            </button>
            <button onClick={handleObserve}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">
              <Eye className="w-3.5 h-3.5" />Observe Now
            </button>
          </div>

          <div className="flex items-center gap-2">
            <input type="number" value={interval} onChange={e => setInterval(Number(e.target.value))} min={10} max={3600}
              className="w-20 px-2 py-1 rounded-lg text-xs bg-[var(--bg-tertiary)] border border-[var(--border-primary)] text-[var(--text-primary)]" />
            <span className="text-2xs text-[var(--text-tertiary)]">seconds interval</span>
            <button onClick={handleSetInterval}
              className="px-2 py-1 rounded-lg text-2xs font-medium bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">
              Set
            </button>
          </div>

          {analysis && (
            <div className="bento-card p-4">
              <h3 className="text-xs font-semibold text-[var(--text-primary)] mb-2">Last Analysis</h3>
              <pre className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-auto">{analysis}</pre>
            </div>
          )}

          {observation && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {observation.goals && <ObservationCard label="Goals" data={observation.goals} icon={Target} />}
              {observation.tasks && <ObservationCard label="Tasks" data={observation.tasks} icon={Activity} />}
              {observation.system && <ObservationCard label="System" data={observation.system} icon={Brain} />}
              {observation.tools && <ObservationCard label="Tools" data={observation.tools} icon={Zap} />}
            </div>
          )}
        </div>
      )}

      {tab === 'history' && (
        <div className="space-y-3">
          <button onClick={loadHistory}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">
            <RefreshCw className="w-3.5 h-3.5" />Refresh
          </button>
          {thoughts.length === 0 && <p className="text-xs text-[var(--text-tertiary)]">No thoughts yet. Click "Think" to start.</p>}
          {thoughts.slice().reverse().map(t => (
            <div key={t.id} className="bento-card p-4 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-violet-400" />
                  <span className="text-xs font-semibold text-[var(--text-primary)]">{t.id}</span>
                  {t.executed && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
                </div>
                <span className="text-2xs text-[var(--text-tertiary)]">{new Date(t.timestamp * 1000).toLocaleString()}</span>
              </div>
              <pre className="text-2xs text-[var(--text-secondary)] whitespace-pre-wrap font-mono max-h-32 overflow-auto">{t.analysis}</pre>
              {t.commands.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {t.commands.map((c, i) => (
                    <span key={i} className="px-2 py-0.5 rounded-full text-2xs bg-violet-500/10 text-violet-300 border border-violet-500/20">
                      {c.command || c.name}{c.reason ? `: ${c.reason.slice(0, 40)}` : ''}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'observe' && (
        <div className="space-y-3">
          <button onClick={handleObserve}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--bg-tertiary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all">
            <RefreshCw className="w-3.5 h-3.5" />Refresh Observation
          </button>
          {observation ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {Object.entries(observation).map(([key, val]) => (
                <div key={key} className="bento-card p-4">
                  <h3 className="text-xs font-semibold text-[var(--text-primary)] mb-2 capitalize">{key}</h3>
                  <pre className="text-2xs text-[var(--text-tertiary)] font-mono overflow-auto max-h-48">{JSON.stringify(val, null, 2)}</pre>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-[var(--text-tertiary)]">No observation yet. Click "Observe Now" to capture system state.</p>
          )}
        </div>
      )}
    </div>
  );
}
