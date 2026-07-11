import { useState, useEffect, useCallback } from 'react';
import {
  Bug, Play, Loader2, CheckCircle, XCircle, RefreshCw, Terminal,
  RotateCw, History, BookTemplate, Search, ChevronRight,
  Clock, AlertTriangle,
  FlaskConical, Wrench, ArrowRight,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/tester';

interface TestResult {
  success: boolean; output?: string; error?: string; duration_ms?: number;
  attempts?: number; analysis?: string;
}

interface HistoryItem {
  command: string; success: boolean; duration_ms: number;
  error?: string; timestamp?: string;
}

interface Preset {
  label: string; cmd: string; category: string;
}

interface TestStats {
  total: number; passed: number; failed: number;
  pass_rate: number; avg_duration_ms: number;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function formatMs(ms: number): string {
  if (ms >= 60000) return `${(ms / 60000).toFixed(1)}m`;
  if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.round(ms)}ms`;
}

const CATEGORIES = ['all', 'python', 'typescript', 'javascript', 'go', 'build'];
const CAT_COLORS: Record<string, string> = {
  python: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  typescript: 'text-blue-500 bg-blue-600/10 border-blue-600/20',
  javascript: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  go: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  build: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
};

export default function SelfTester() {
  const [tab, setTab] = useState('test');
  const [command, setCommand] = useState('');
  const [result, setResult] = useState<TestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [presets, setPresets] = useState<Preset[]>([]);
  const [stats, setStats] = useState<TestStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [presetFilter, setPresetFilter] = useState('all');
  const [outputTab, setOutputTab] = useState<'output' | 'error'>('output');
  const { addToast } = useToast();

  const loadAll = useCallback(async () => {
    try {
      const [hRes, pRes, sRes] = await Promise.all([
        get<{ history: HistoryItem[] }>('/history?limit=50'),
        get<{ presets: Preset[] }>('/commands'),
        get<TestStats>('/stats'),
      ]);
      setHistory(hRes.history);
      setPresets(pRes.presets);
      setStats(sRes);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const runTest = async (cmd: string, fix: boolean = false) => {
    if (!cmd.trim() || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await post<TestResult>(fix ? '/fix' : '/run', { command: cmd, context: 'auto-fix', max_attempts: 5 });
      setResult(res);
      addToast(res.success ? `Passed${res.attempts ? ` (${res.attempts} attempts)` : ''}` : 'Failed', res.success ? 'success' : 'error');
      loadAll();
    } catch {
      setResult({ success: false, error: 'Request failed' });
      addToast('Test request failed', 'error');
    }
    setLoading(false);
  };

  const filteredHistory = history.filter(h =>
    !searchQuery || h.command.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredPresets = presets.filter(p =>
    (presetFilter === 'all' || p.category === presetFilter)
  );

  const tabs = [
    { id: 'test', label: 'Test', icon: FlaskConical },
    { id: 'presets', label: `Presets (${presets.length})`, icon: BookTemplate },
    { id: 'history', label: `History (${history.length})`, icon: History },
  ];

  return (
    <div className="p-6 space-y-6">
      <PageHeader icon={Bug} title="Self Tester" description="Run tests, detect errors, auto-fix, and retry until success" />

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

      {/* ── TEST TAB ── */}
      {tab === 'test' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {/* Input */}
            <Card hover={false} className="space-y-4">
              <div className="flex gap-3">
                <input value={command} onChange={e => setCommand(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !loading && runTest(command)}
                  className="flex-1 bg-slate-950 border border-white/10 rounded-xl px-4 py-3 text-sm text-white font-mono outline-none focus:border-lumina-500/50 placeholder-slate-500"
                  placeholder="python -m pytest tests/ -v" />
                <button onClick={() => runTest(command)} disabled={loading || !command.trim()}
                  className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-5 py-3 text-sm font-medium flex items-center gap-2 transition-all shadow-lg shadow-lumina-500/20">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  Run
                </button>
                <button onClick={() => runTest(command, true)} disabled={loading || !command.trim()}
                  className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-5 py-3 text-sm font-medium flex items-center gap-2 transition-all shadow-lg shadow-emerald-500/20">
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Wrench className="w-4 h-4" />}
                  Auto-Fix
                </button>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {presets.slice(0, 6).map(p => (
                  <button key={p.label} onClick={() => { setCommand(p.cmd); runTest(p.cmd); }}
                    className={`px-3 py-1.5 rounded-lg text-[10px] font-medium transition-all border ${CAT_COLORS[p.category] || 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10'}`}>
                    {p.label}
                  </button>
                ))}
              </div>
            </Card>

            {/* Result */}
            {result && (
              <Card hover={false} className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {result.success
                      ? <CheckCircle className="w-6 h-6 text-emerald-400" />
                      : <XCircle className="w-6 h-6 text-red-400" />}
                    <div>
                      <p className={`text-sm font-medium ${result.success ? 'text-emerald-400' : 'text-red-400'}`}>
                        {result.success ? 'Passed' : 'Failed'}
                        {result.attempts ? ` (attempt ${result.attempts})` : ''}
                      </p>
                      {result.duration_ms && (
                        <p className="text-[10px] text-slate-500">{formatMs(result.duration_ms)}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => runTest(command)} disabled={loading}
                      className="text-[10px] px-2.5 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 flex items-center gap-1.5">
                      <RotateCw className="w-3 h-3" /> Re-run
                    </button>
                    <button onClick={() => runTest(command, true)} disabled={loading}
                      className="text-[10px] px-2.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:text-emerald-300 flex items-center gap-1.5">
                      <Wrench className="w-3 h-3" /> Auto-Fix
                    </button>
                  </div>
                </div>

                {result.analysis && (
                  <div className="bg-lumina-600/5 border border-lumina-500/20 rounded-xl px-4 py-3">
                    <div className="flex items-center gap-1.5 mb-1">
                      <AlertTriangle className="w-3.5 h-3.5 text-lumina-400" />
                      <span className="text-[10px] font-medium text-lumina-300">AI Analysis</span>
                    </div>
                    <p className="text-xs text-slate-300">{result.analysis}</p>
                  </div>
                )}

                {(result.output || result.error) && (
                  <>
                    <div className="flex items-center gap-1 border-b border-white/5 pb-2">
                      {['output', 'error'].map(t => (
                        <button key={t} onClick={() => setOutputTab(t as any)}
                          className={`text-[10px] px-3 py-1.5 rounded-lg font-medium transition-all capitalize ${
                            outputTab === t
                              ? 'bg-white/10 text-slate-200'
                              : 'text-slate-500 hover:text-slate-300'
                          }`}>
                          {t} {t === 'output' && result.output ? `(${result.output.length})` : ''}
                          {t === 'error' && result.error ? `(${result.error.length})` : ''}
                        </button>
                      ))}
                    </div>
                    <pre className={`text-xs font-mono whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto rounded-xl bg-slate-950/50 p-4 ${
                      outputTab === 'error' ? 'text-red-300' : 'text-slate-300'
                    }`}>
                      {outputTab === 'output' ? (result.output || '(no output)') : (result.error || '(no errors)')}
                    </pre>
                  </>
                )}
              </Card>
            )}

            {loading && !result && (
              <Card hover={false}>
                <div className="flex items-center gap-3 py-2">
                  <Loader2 className="w-5 h-5 animate-spin text-lumina-400" />
                  <div className="flex-1">
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full w-1/3 bg-lumina-500 rounded-full animate-pulse" style={{ animationDuration: '1.5s' }} />
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">Running...</span>
                </div>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {stats && (
              <Card hover={false} className="space-y-3">
                <CardSection label="Stats">
                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-white/[0.02] rounded-xl px-3 py-2.5 border border-white/5 text-center">
                      <p className="text-lg font-bold text-white">{stats.total}</p>
                      <p className="text-[9px] text-slate-500">Total Runs</p>
                    </div>
                    <div className="bg-white/[0.02] rounded-xl px-3 py-2.5 border border-white/5 text-center">
                      <p className="text-lg font-bold text-emerald-400">{stats.pass_rate}%</p>
                      <p className="text-[9px] text-slate-500">Pass Rate</p>
                    </div>
                    <div className="bg-white/[0.02] rounded-xl px-3 py-2.5 border border-white/5 text-center">
                      <p className="text-lg font-bold text-emerald-400">{stats.passed}</p>
                      <p className="text-[9px] text-slate-500">Passed</p>
                    </div>
                    <div className="bg-white/[0.02] rounded-xl px-3 py-2.5 border border-white/5 text-center">
                      <p className="text-lg font-bold text-red-400">{stats.failed}</p>
                      <p className="text-[9px] text-slate-500">Failed</p>
                    </div>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${stats.pass_rate}%` }} />
                  </div>
                  <p className="text-[9px] text-slate-600 text-center">Avg: {formatMs(stats.avg_duration_ms)}</p>
                </CardSection>
              </Card>
            )}

            <Card hover={false} className="space-y-3 sticky top-4">
              <CardSection label="Quick Actions">
                <div className="space-y-1">
                  {presets.slice(0, 5).map(p => (
                    <button key={p.label} onClick={() => { setCommand(p.cmd); runTest(p.cmd); }}
                      className="w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] transition-all">
                      <Terminal className="w-3.5 h-3.5 text-lumina-400 shrink-0" />
                      <span className="flex-1 truncate">{p.label}</span>
                      <ChevronRight className="w-3 h-3 text-slate-600 shrink-0" />
                    </button>
                  ))}
                </div>
              </CardSection>

              <CardSection label="Tips">
                <ul className="space-y-1.5 text-[10px] text-slate-500">
                  <li className="flex items-start gap-1.5"><ArrowRight className="w-3 h-3 shrink-0 mt-0.5 text-lumina-400" /> Use Auto-Fix for AI-powered error resolution</li>
                  <li className="flex items-start gap-1.5"><ArrowRight className="w-3 h-3 shrink-0 mt-0.5 text-lumina-400" /> Type any shell command and press Enter</li>
                  <li className="flex items-start gap-1.5"><ArrowRight className="w-3 h-3 shrink-0 mt-0.5 text-lumina-400" /> Check Presets tab for common commands</li>
                </ul>
              </CardSection>
            </Card>
          </div>
        </div>
      )}

      {/* ── PRESETS TAB ── */}
      {tab === 'presets' && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1 max-w-xs">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-300 outline-none focus:border-lumina-500/50 placeholder-slate-500"
                placeholder="Search presets..." />
            </div>
            <div className="flex items-center gap-1">
              {CATEGORIES.map(c => (
                <button key={c} onClick={() => setPresetFilter(c)}
                  className={`text-[10px] px-2.5 py-1.5 rounded-lg font-medium transition-all capitalize ${
                    presetFilter === c ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'text-slate-500 hover:text-slate-300'
                  }`}>{c}</button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredPresets.map(p => (
              <Card key={p.label} onClick={() => { setCommand(p.cmd); setTab('test'); }}
                className="p-4">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg bg-white/[0.03] border border-white/5 flex items-center justify-center">
                    <Terminal className="w-4 h-4 text-lumina-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-slate-200">{p.label}</p>
                    <code className="text-[10px] text-slate-500 font-mono block mt-1 truncate">{p.cmd}</code>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-full mt-1.5 inline-block ${CAT_COLORS[p.category] || 'bg-white/5 text-slate-500'}`}>
                      {p.category}
                    </span>
                  </div>
                  <Play className="w-3.5 h-3.5 text-lumina-400 shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* ── HISTORY TAB ── */}
      {tab === 'history' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="relative flex-1 max-w-xs">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-300 outline-none focus:border-lumina-500/50 placeholder-slate-500"
                placeholder="Search history..." />
            </div>
            <button onClick={loadAll} className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {stats && (
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'Total', value: String(stats.total), color: 'text-slate-200' },
                { label: 'Passed', value: String(stats.passed), color: 'text-emerald-400' },
                { label: 'Failed', value: String(stats.failed), color: 'text-red-400' },
                { label: 'Pass Rate', value: `${stats.pass_rate}%`, color: stats.pass_rate > 80 ? 'text-emerald-400' : 'text-amber-400' },
              ].map(s => (
                <div key={s.label} className="bg-white/[0.02] rounded-xl px-4 py-3 border border-white/5 text-center">
                  <p className={`text-lg font-bold ${s.color}`}>{s.value}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>
          )}

          {filteredHistory.length === 0 ? (
            <Card hover={false} className="text-center py-12">
              <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No test history yet</p>
              <p className="text-xs text-slate-500 mt-1">Run tests to see history here</p>
            </Card>
          ) : (
            <div className="space-y-1.5">
              {filteredHistory.map((h, i) => (
                <Card key={i} onClick={() => { setCommand(h.command); setTab('test'); runTest(h.command); }} className="p-3.5">
                  <div className="flex items-center gap-3">
                    {h.success
                      ? <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                      : <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <code className="text-xs text-slate-300 font-mono truncate">{h.command}</code>
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full shrink-0 ${
                          h.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                        }`}>{h.success ? 'Pass' : 'Fail'}</span>
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {h.duration_ms > 0 && (
                          <span className="text-[10px] text-slate-600 flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {formatMs(h.duration_ms)}
                          </span>
                        )}
                      </div>
                    </div>
                    <RotateCw className="w-3 h-3 text-slate-600 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
