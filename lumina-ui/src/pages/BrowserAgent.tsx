import { useState, useEffect, useRef } from 'react';
import {
  Globe, MousePointer, Type, Camera, Navigation, Play,
  Square, Terminal, Loader2, CheckCircle, XCircle, AlertCircle,
  Clock, Copy, ExternalLink, RefreshCw, History, Code,
  Pen, Target, Eye, FileText, Link, ChevronRight,
  ArrowLeft, ArrowRight, Home, Search, Zap,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/browser';

interface LogEntry {
  step: string; status: 'ok' | 'error'; timestamp: number;
}

export default function BrowserAgent() {
  const [tab, setTab] = useState('agent');
  const [url, setUrl] = useState('https://google.com');
  const [taskInput, setTaskInput] = useState('');
  const [log, setLog] = useState<LogEntry[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [content, setContent] = useState('');
  const [links, setLinks] = useState<{text: string; href: string}[]>([]);
  const [selector, setSelector] = useState('');
  const [fillSelector, setFillSelector] = useState('');
  const [fillValue, setFillValue] = useState('');
  const [taskHistory, setTaskHistory] = useState<string[]>([]);
  const [showFullContent, setShowFullContent] = useState(false);
  const { addToast } = useToast();
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [log]);

  const addLog = (step: string, status: 'ok' | 'error') => {
    setLog(prev => [...prev, { step, status, timestamp: Date.now() }]);
  };

  const navigate = async () => {
    if (!url.trim()) return;
    setLoading('navigate');
    setLog([]);
    setContent('');
    setLinks([]);
    setResult(null);
    try {
      const res = await fetch(`${BASE}/navigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.includes('://') ? url : `https://${url}` }),
      });
      if (!res.ok) throw new Error('Navigation failed');
      addLog(`Navigated to ${url}`, 'ok');
      addToast('Page loaded', 'success');
      await loadContent();
    } catch (e: any) {
      addLog(`Navigation error: ${e.message}`, 'error');
      addToast(e.message, 'error');
    } finally { setLoading(null); }
  };

  const loadContent = async () => {
    try {
      const [cRes, lRes] = await Promise.all([
        fetch(`${BASE}/content`).then(r => r.json()),
        fetch(`${BASE}/links`).then(r => r.json()),
      ]);
      setContent(cRes.content || cRes.html || '');
      setLinks(lRes.links || []);
    } catch {}
  };

  const clickElement = async () => {
    if (!selector.trim()) return;
    setLoading('click');
    try {
      const res = await fetch(`${BASE}/click`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selector: selector.trim() }),
      });
      if (!res.ok) throw new Error('Click failed');
      addLog(`Clicked "${selector}"`, 'ok');
      addToast('Element clicked', 'success');
      setTimeout(loadContent, 500);
    } catch (e: any) {
      addLog(`Click error: ${e.message}`, 'error');
      addToast(e.message, 'error');
    } finally { setLoading(null); }
  };

  const fillForm = async () => {
    if (!fillSelector.trim() || !fillValue.trim()) return;
    setLoading('fill');
    try {
      const res = await fetch(`${BASE}/fill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ selector: fillSelector.trim(), value: fillValue }),
      });
      if (!res.ok) throw new Error('Fill failed');
      addLog(`Filled "${fillSelector}" with "${fillValue}"`, 'ok');
      addToast('Form filled', 'success');
    } catch (e: any) {
      addLog(`Fill error: ${e.message}`, 'error');
      addToast(e.message, 'error');
    } finally { setLoading(null); }
  };

  const takeScreenshot = async () => {
    setLoading('screenshot');
    try {
      const res = await fetch(`${BASE}/screenshot`, { method: 'POST' });
      const data = await res.json();
      setResult(data);
      addLog('Screenshot captured', 'ok');
      addToast('Screenshot taken', 'success');
    } catch (e: any) {
      addLog(`Screenshot error: ${e.message}`, 'error');
      addToast(e.message, 'error');
    } finally { setLoading(null); }
  };

  const runAgent = async () => {
    if (!taskInput.trim()) return;
    setLoading('agent');
    setLog([]);
    setResult(null);
    setTaskHistory(prev => [taskInput, ...prev].slice(0, 20));
    try {
      const res = await fetch(`${BASE}/agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: taskInput, headless: false }),
      });
      if (!res.ok) throw new Error('Agent failed');
      const data = await res.json();
      setResult(data);
      const steps = data.steps || data.log || [];
      if (Array.isArray(steps)) {
        steps.forEach((s: any, i: number) => {
          setTimeout(() => addLog(s.message || s.step || `Step ${i + 1}`, s.status || 'ok'), i * 300);
        });
      } else {
        addLog('Task completed', 'ok');
      }
      addToast('Agent task completed', 'success');
    } catch (e: any) {
      addLog(`Agent error: ${e.message}`, 'error');
      addToast(e.message, 'error');
    } finally { setLoading(null); }
  };

  const EXAMPLE_TASKS = [
    'Search for "Lumina AI" on Google',
    'Go to github.com and find the trending repos',
    'Go to wikipedia.org and search for Artificial Intelligence',
  ];

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Globe} title="Browser Agent" description="AI-powered browser automation & manual control" />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['agent', 'console', 'history'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'agent' ? <Zap className="w-3.5 h-3.5" /> : t === 'console' ? <Terminal className="w-3.5 h-3.5" /> : <History className="w-3.5 h-3.5" />}
            {t === 'agent' ? 'AI Agent' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {tab === 'agent' && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            {/* Left: Task input + examples */}
            <div className="lg:col-span-3 space-y-4">
              <Card>
                <CardSection label="Task">
                  <textarea value={taskInput} onChange={e => setTaskInput(e.target.value)}
                    placeholder="Describe what you want the browser to do...&#10;e.g. 'Go to google.com and search for Lumina AI'"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 resize-none h-24 transition-colors"
                  />
                  <div className="flex items-center gap-2 mt-3">
                    <button onClick={runAgent} disabled={loading === 'agent' || !taskInput.trim()}
                      className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-lumina-500 to-lumina-600 rounded-xl text-xs font-medium text-white disabled:opacity-40 hover:from-lumina-400 hover:to-lumina-500 transition-all shadow-lg shadow-lumina-500/20"
                    >{loading === 'agent' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                      {loading === 'agent' ? 'Running...' : 'Run Task'}
                    </button>
                    <button onClick={() => setTaskInput('')}
                      className="px-3 py-2 rounded-lg text-xs text-slate-400 hover:bg-white/5 transition-colors"
                    >Clear</button>
                  </div>
                </CardSection>
              </Card>

              {/* Example tasks */}
              <Card>
                <CardSection label="Quick Examples">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {EXAMPLE_TASKS.map(t => (
                      <button key={t} onClick={() => setTaskInput(t)}
                        className="text-left px-3 py-2 rounded-lg border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all text-xs text-slate-300"
                      >{t}</button>
                    ))}
                  </div>
                </CardSection>
              </Card>

              {/* Result */}
              {result && (
                <Card>
                  <CardSection label="Result">
                    {result.html ? (
                      <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto bg-white/[0.02] rounded-lg p-3">
                        {result.html.slice(0, 3000)}
                      </pre>
                    ) : result.content ? (
                      <p className="text-sm text-slate-200 whitespace-pre-wrap">{result.content}</p>
                    ) : result.screenshot ? (
                      <div className="text-center py-4">
                        <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                        <p className="text-xs text-slate-400">Screenshot captured</p>
                        <img src={`data:image/png;base64,${result.screenshot}`} alt="Screenshot" className="mt-3 rounded-lg max-h-64 mx-auto" />
                      </div>
                    ) : (
                      <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto">{JSON.stringify(result, null, 2)}</pre>
                    )}
                  </CardSection>
                </Card>
              )}
            </div>

            {/* Right: Task history + log */}
            <div className="lg:col-span-2 space-y-4">
              {/* History */}
              {taskHistory.length > 0 && (
                <Card>
                  <CardSection label="Task History">
                    <div className="space-y-1">
                      {taskHistory.map((t, i) => (
                        <button key={i} onClick={() => setTaskInput(t)}
                          className="w-full text-left px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:bg-white/5 truncate transition-colors"
                        >{t}</button>
                      ))}
                    </div>
                  </CardSection>
                </Card>
              )}

              {/* Log */}
              {log.length > 0 && (
                <Card>
                  <CardSection label={`${log.filter(l => l.status === 'ok').length}/${log.length} Steps`}>
                    <div className="space-y-1 max-h-80 overflow-y-auto">
                      {log.map((l, i) => (
                        <div key={i} className={`flex items-start gap-2 px-3 py-1.5 rounded-lg text-xs ${
                          l.status === 'ok' ? 'text-slate-300' : 'text-red-400'
                        }`}>
                          {l.status === 'ok'
                            ? <CheckCircle className="w-3 h-3 mt-0.5 shrink-0 text-emerald-400" />
                            : <XCircle className="w-3 h-3 mt-0.5 shrink-0 text-red-400" />
                          }
                          <span>{l.step}</span>
                        </div>
                      ))}
                      <div ref={logEndRef} />
                    </div>
                  </CardSection>
                </Card>
              )}

              {log.length === 0 && (
                <Card>
                  <div className="text-center py-8">
                    <Globe className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">Task log will appear here</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}

        {tab === 'console' && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
            {/* Controls */}
            <div className="lg:col-span-3 space-y-4">
              <Card>
                <CardSection label="Navigation">
                  <div className="flex gap-2">
                    <input type="text" value={url} onChange={e => setUrl(e.target.value)}
                      placeholder="https://example.com"
                      className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                      onKeyDown={e => e.key === 'Enter' && navigate()}
                    />
                    <button onClick={navigate} disabled={loading === 'navigate'}
                      className="flex items-center gap-2 px-4 py-2.5 bg-lumina-500/20 text-lumina-300 rounded-xl text-xs font-medium hover:bg-lumina-500/30 disabled:opacity-40 transition-all"
                    >{loading === 'navigate' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Navigation className="w-3.5 h-3.5" />}Go</button>
                  </div>
                </CardSection>
              </Card>

              <Card>
                <CardSection label="Click Element">
                  <div className="flex gap-2">
                    <input type="text" value={selector} onChange={e => setSelector(e.target.value)}
                      placeholder="CSS selector (e.g. button, #id, .class)" className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                      onKeyDown={e => e.key === 'Enter' && clickElement()}
                    />
                    <button onClick={clickElement} disabled={loading === 'click'}
                      className="flex items-center gap-2 px-4 py-2.5 bg-lumina-500/20 text-lumina-300 rounded-xl text-xs font-medium hover:bg-lumina-500/30 disabled:opacity-40 transition-all"
                    >{loading === 'click' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <MousePointer className="w-3.5 h-3.5" />}Click</button>
                  </div>
                </CardSection>
              </Card>

              <Card>
                <CardSection label="Fill Form Field">
                  <div className="flex gap-2">
                    <input type="text" value={fillSelector} onChange={e => setFillSelector(e.target.value)}
                      placeholder="CSS selector" className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                    />
                    <input type="text" value={fillValue} onChange={e => setFillValue(e.target.value)}
                      placeholder="Value" className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                      onKeyDown={e => e.key === 'Enter' && fillForm()}
                    />
                    <button onClick={fillForm} disabled={loading === 'fill'}
                      className="flex items-center gap-2 px-4 py-2.5 bg-lumina-500/20 text-lumina-300 rounded-xl text-xs font-medium hover:bg-lumina-500/30 disabled:opacity-40 transition-all"
                    >{loading === 'fill' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Pen className="w-3.5 h-3.5" />}Fill</button>
                  </div>
                </CardSection>
              </Card>

              <Card>
                <CardSection label="Actions">
                  <div className="flex items-center gap-2">
                    <button onClick={takeScreenshot} disabled={loading === 'screenshot'}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-white/5 text-slate-300 hover:bg-white/10 disabled:opacity-40 transition-colors"
                    >{loading === 'screenshot' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Camera className="w-3.5 h-3.5" />}Screenshot</button>
                    <button onClick={loadContent}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-white/5 text-slate-300 hover:bg-white/10 transition-colors"
                    ><RefreshCw className="w-3.5 h-3.5" />Refresh Content</button>
                  </div>
                </CardSection>
              </Card>

              {/* Page content */}
              {content && (
                <Card>
                  <CardSection label="Page Source" action={
                    <button onClick={() => setShowFullContent(!showFullContent)}
                      className="text-xs text-lumina-400 hover:text-lumina-300"
                    >{showFullContent ? 'Collapse' : 'Show All'}</button>
                  }>
                    <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto bg-white/[0.02] rounded-lg p-3">
                      {showFullContent ? content : content.slice(0, 3000)}
                    </pre>
                  </CardSection>
                </Card>
              )}

              {/* Links */}
              {links.length > 0 && (
                <Card>
                  <CardSection label={`Links (${links.length})`}>
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {links.map((l, i) => (
                        <button key={i} onClick={() => { setUrl(l.href); }}
                          className="w-full text-left flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:bg-white/5 transition-colors"
                        ><Link className="w-3 h-3 shrink-0" /><span className="truncate">{l.text || l.href}</span></button>
                      ))}
                    </div>
                  </CardSection>
                </Card>
              )}
            </div>

            {/* Sidebar: Action log */}
            <div className="lg:col-span-2 space-y-4">
              {log.length > 0 && (
                <Card>
                  <CardSection label="Action Log">
                    <div className="space-y-1 max-h-96 overflow-y-auto">
                      {log.map((l, i) => (
                        <div key={i} className={`flex items-start gap-2 px-3 py-1.5 rounded-lg text-xs ${
                          l.status === 'ok' ? 'text-slate-300' : 'text-red-400'
                        }`}>
                          <Clock className="w-3 h-3 mt-0.5 shrink-0 text-slate-500" />
                          <span>{l.step}</span>
                        </div>
                      ))}
                    </div>
                  </CardSection>
                </Card>
              )}
              {log.length === 0 && (
                <Card>
                  <div className="text-center py-8">
                    <Terminal className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">Console actions log here</p>
                    <p className="text-xs text-slate-600 mt-1">Navigate, click, fill, and screenshot</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}

        {tab === 'history' && (
          <CardSection label="Recent Tasks">
            {taskHistory.length === 0 ? (
              <div className="text-center py-12">
                <History className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No task history yet</p>
                <p className="text-xs text-slate-600 mt-1">AI Agent tasks will appear here</p>
              </div>
            ) : (
              <div className="space-y-2">
                {taskHistory.map((t, i) => (
                  <button key={i} onClick={() => { setTaskInput(t); setTab('agent'); }}
                    className="w-full flex items-center gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all text-left group"
                  >
                    <div className="w-9 h-9 rounded-lg bg-lumina-500/10 flex items-center justify-center shrink-0">
                      <Globe className="w-4 h-4 text-lumina-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{t}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 mt-1 shrink-0" />
                  </button>
                ))}
              </div>
            )}
          </CardSection>
        )}
      </div>
    </div>
  );
}
