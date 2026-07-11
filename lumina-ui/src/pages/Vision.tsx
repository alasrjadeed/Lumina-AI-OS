import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Camera, Square, Eye, Scan, Brain, MessageSquare,
  Loader2, History, RefreshCw, Trash2,
  Copy, AlertCircle, Maximize2,
  Minimize2, Search, Zap,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/vision';

interface VisionResult {
  success?: boolean; data?: unknown; detections?: unknown[];
  faces?: unknown[]; description?: string; error?: string; thinking?: string;
}

interface CaptureItem {
  id: string; timestamp: number; type: string; result: VisionResult; label?: string;
}

export default function Vision() {
  const [tab, setTab] = useState('camera');
  const [status, setStatus] = useState<any>(null);
  const [result, setResult] = useState<VisionResult | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [watchMode, setWatchMode] = useState(false);
  const [thinkInput, setThinkInput] = useState('');
  const [thinkResult, setThinkResult] = useState('');
  const [thinkLoading, setThinkLoading] = useState(false);
  const [captures, setCaptures] = useState<CaptureItem[]>([]);
  const [captureSearch, setCaptureSearch] = useState('');
  const [captureFilter, setCaptureFilter] = useState('all');
  const [showFullscreen, setShowFullscreen] = useState(false);
  const { addToast } = useToast();
  const streamRef = useRef<HTMLImageElement>(null);
  const watchInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    fetch(`${BASE}/status`).then(r => r.json()).then(d => setStatus(d)).catch(() => {});
  }, []);

  useEffect(() => {
    if (watchMode) {
      fetch(`${BASE}/watch`, { method: 'POST' }).catch(() => {});
      watchInterval.current = setInterval(() => {
        fetch(`${BASE}/what-do-you-see`, { method: 'POST' })
          .then(r => r.json())
          .then(d => setResult({ description: d.response || JSON.stringify(d) }))
          .catch(() => {});
      }, 3000);
    } else {
      fetch(`${BASE}/watch/stop`, { method: 'POST' }).catch(() => {});
      if (watchInterval.current) {
        clearInterval(watchInterval.current);
        watchInterval.current = null;
      }
    }
    return () => {
      fetch(`${BASE}/watch/stop`, { method: 'POST' }).catch(() => {});
      if (watchInterval.current) clearInterval(watchInterval.current);
    };
  }, [watchMode]);

  const call = async (endpoint: string, body?: unknown) => {
    setLoading(endpoint);
    setResult(null);
    try {
      const res = await fetch(`${BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined,
      });
      const data: VisionResult = await res.json();
      setResult(data);
      if (data.success !== false) {
        addToast(`${endpoint.replace('/', '').replace('-', ' ')} completed`, 'success');
      }
      return data;
    } catch (e: any) {
      setResult({ error: e.message });
      addToast(`Error: ${e.message}`, 'error');
    } finally {
      setLoading(null);
    }
  };

  const doThink = async () => {
    if (!thinkInput.trim()) return;
    setThinkLoading(true);
    setThinkResult('');
    try {
      const res = await fetch(`${BASE}/think`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: thinkInput }),
      });
      const data = await res.json();
      setThinkResult(data.response || data.thinking || JSON.stringify(data));
    } catch (e: any) {
      setThinkResult(`Error: ${e.message}`);
    } finally {
      setThinkLoading(false);
    }
  };

  const saveCapture = useCallback((type: string, res: VisionResult, label?: string) => {
    setCaptures(prev => [{
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: Date.now(), type, result: res, label,
    }, ...prev].slice(0, 50));
  }, []);

  const captureImage = async () => {
    const res = await call('/capture/json');
    if (res) saveCapture('capture', res);
  };

  const detectObjects = async () => {
    const res = await call('/detect');
    if (res) saveCapture('detect', res);
  };

  const detectFaces = async () => {
    const res = await call('/face/detect');
    if (res) saveCapture('face', res);
  };

  const describeScene = async () => {
    const res = await call('/describe');
    if (res) saveCapture('describe', res?.description ? { description: res.description } : res);
  };

  const clearCaptures = () => setCaptures([]);

  const copyResult = (text: string) => {
    navigator.clipboard.writeText(text);
    addToast('Copied to clipboard', 'success');
  };

  const filteredCaptures = captures.filter(c =>
    (captureFilter === 'all' || c.type === captureFilter) &&
    (c.label || c.type).toLowerCase().includes(captureSearch.toLowerCase())
  );
  const captureTypes = [...new Set(captures.map(c => c.type))];

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Camera} title="Vision" description={status ? `Camera: ${status.camera || status.device || 'active'}` : 'Camera vision & AI analysis'} />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['camera', 'think', 'captures'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'camera' ? <Camera className="w-3.5 h-3.5" /> : t === 'think' ? <Brain className="w-3.5 h-3.5" /> : <History className="w-3.5 h-3.5" />}
            {t === 'captures' ? 'Captures' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {tab === 'camera' && (
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 h-full">
            {/* Stream panel */}
            <div className="lg:col-span-3 space-y-4">
              <div className="relative rounded-xl overflow-hidden border border-white/5 bg-black/60 aspect-video flex items-center justify-center">
                  <img ref={streamRef} src={`${BASE}/stream/mjpeg?t=${Date.now()}`}
                    alt="Camera stream" className="w-full h-full object-contain"
                  />
                  <button onClick={() => setShowFullscreen(!showFullscreen)}
                    className="absolute top-2 right-2 p-1.5 rounded-lg bg-black/40 text-white/60 hover:text-white hover:bg-black/60 transition-all"
                  >{showFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}</button>
                {status?.error && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/70">
                    <div className="text-center">
                      <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-2" />
                      <p className="text-sm text-red-400">Camera unavailable</p>
                      <p className="text-xs text-slate-500 mt-1">{status.error}</p>
                    </div>
                  </div>
                )}
                {/* Action buttons overlay */}
                <div className="absolute bottom-3 left-3 right-3 flex items-center gap-2">
                  <button onClick={captureImage} disabled={loading !== null}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 disabled:opacity-40 transition-all"
                  >{loading === '/capture/json' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Camera className="w-3.5 h-3.5" />}Capture</button>
                  <button onClick={detectObjects} disabled={loading !== null}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 disabled:opacity-40 transition-all"
                  >{loading === '/detect' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Scan className="w-3.5 h-3.5" />}Detect</button>
                  <button onClick={detectFaces} disabled={loading !== null}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 disabled:opacity-40 transition-all"
                  >{loading === '/face/detect' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}Faces</button>
                  <button onClick={describeScene} disabled={loading !== null}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 disabled:opacity-40 transition-all"
                  >{loading === '/describe' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <MessageSquare className="w-3.5 h-3.5" />}Describe</button>
                  <button onClick={() => setWatchMode(!watchMode)}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium backdrop-blur-sm transition-all ${
                      watchMode ? 'bg-red-500/30 text-red-300' : 'bg-white/10 text-white hover:bg-white/20'
                    }`}
                  >{watchMode ? <Square className="w-3.5 h-3.5" /> : <Zap className="w-3.5 h-3.5" />}{watchMode ? 'Stop' : 'Watch'}</button>
                </div>
              </div>
            </div>

            {/* Result panel */}
            <div className="lg:col-span-2 space-y-4">
              {loading ? (
                <Card>
                  <div className="flex items-center gap-3 py-4">
                    <Loader2 className="w-5 h-5 text-lumina-400 animate-spin" />
                    <span className="text-sm text-slate-400">Processing...</span>
                  </div>
                </Card>
              ) : result ? (
                <Card>
                  <CardSection label="Result">
                    {result.error ? (
                      <p className="text-xs text-red-400">{result.error}</p>
                    ) : result.description ? (
                      <div>
                        <p className="text-sm text-slate-200 whitespace-pre-wrap">{result.description}</p>
                        <button onClick={() => copyResult(result.description!)}
                          className="mt-2 flex items-center gap-1 text-xs text-lumina-400 hover:text-lumina-300"
                        ><Copy className="w-3 h-3" />Copy</button>
                      </div>
                    ) : result.detections ? (
                      <div className="space-y-1">
                        {result.detections.map((d: any, i: number) => (
                          <div key={i} className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-white/[0.03] text-xs">
                            <span className="text-slate-300">{d.label || d.name || `Object ${i + 1}`}</span>
                            <span className="text-lumina-400">{d.confidence ? `${(d.confidence * 100).toFixed(0)}%` : ''}</span>
                          </div>
                        ))}
                      </div>
                    ) : result.faces ? (
                      <div className="space-y-1">
                        {result.faces.map((f: any, i: number) => (
                          <div key={i} className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-white/[0.03] text-xs">
                            <span className="text-slate-300">Face #{i + 1}</span>
                            <span className="text-slate-500">{f.confidence ? `${(f.confidence * 100).toFixed(0)}%` : ''}</span>
                          </div>
                        ))}
                        <p className="text-[10px] text-slate-500 mt-1">{result.faces.length} face(s) detected</p>
                      </div>
                    ) : (
                      <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-60 overflow-y-auto">
                        {JSON.stringify(result.data || result, null, 2)}
                      </pre>
                    )}
                  </CardSection>
                </Card>
              ) : (
                <Card>
                  <div className="text-center py-8">
                    <Camera className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">Click a button to analyze</p>
                    <p className="text-xs text-slate-600 mt-1">Capture, Detect, Faces, or Describe</p>
                  </div>
                </Card>
              )}

              {/* Quick actions */}
              <Card>
                <CardSection label="Quick Actions">
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: 'Capture & Detect', icon: Scan, action: async () => { await captureImage(); await detectObjects(); } },
                      { label: 'Capture & Describe', icon: MessageSquare, action: async () => { await captureImage(); await describeScene(); } },
                      { label: 'Reset Camera', icon: RefreshCw, action: () => fetch(`${BASE}/reload`, { method: 'POST' }).then(() => addToast('Camera reset', 'success')) },
                      { label: 'Status', icon: Eye, action: () => fetch(`${BASE}/status`).then(r => r.json()).then(d => setStatus(d)) },
                    ].map(({ label: lbl, icon: Icon, action }) => (
                      <button key={lbl} onClick={action}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-300 hover:bg-white/5 border border-white/5 transition-all"
                      ><Icon className="w-3.5 h-3.5 text-slate-400" />{lbl}</button>
                    ))}
                  </div>
                </CardSection>
              </Card>
            </div>
          </div>
        )}

        {tab === 'think' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
            <Card>
              <CardSection label="Ask About the Scene">
                <textarea value={thinkInput} onChange={e => setThinkInput(e.target.value)}
                  placeholder="What do you see? What should I look for?"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 resize-none h-24 transition-colors"
                />
                <button onClick={doThink} disabled={thinkLoading || !thinkInput.trim()}
                  className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-lumina-500 to-lumina-600 rounded-xl text-xs font-medium text-white disabled:opacity-40 hover:from-lumina-400 hover:to-lumina-500 transition-all shadow-lg shadow-lumina-500/20"
                >{thinkLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Brain className="w-3.5 h-3.5" />}
                  {thinkLoading ? 'Thinking...' : 'Ask Vision'}
                </button>
              </CardSection>
            </Card>

            <Card>
              <CardSection label="Response" action={
                thinkResult && <button onClick={() => copyResult(thinkResult)}
                  className="flex items-center gap-1 text-xs text-lumina-400 hover:text-lumina-300"
                ><Copy className="w-3 h-3" />Copy</button>
              }>
                {thinkLoading ? (
                  <div className="flex items-center gap-2 py-6">
                    <Loader2 className="w-4 h-4 text-lumina-400 animate-spin" />
                    <span className="text-xs text-slate-400">Analyzing scene...</span>
                  </div>
                ) : thinkResult ? (
                  <p className="text-sm text-slate-200 whitespace-pre-wrap">{thinkResult}</p>
                ) : (
                  <div className="text-center py-10">
                    <Brain className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">Ask a question about the scene</p>
                  </div>
                )}
              </CardSection>
            </Card>
          </div>
        )}

        {tab === 'captures' && (
          <div className="space-y-4">
            <CardSection label="Capture History" action={
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input type="text" value={captureSearch} onChange={e => setCaptureSearch(e.target.value)}
                    placeholder="Search..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-32"
                  />
                </div>
                <select value={captureFilter} onChange={e => setCaptureFilter(e.target.value)}
                  className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
                >
                  <option value="all">All</option>
                  {captureTypes.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                {captures.length > 0 && (
                  <button onClick={clearCaptures}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-colors"
                  ><Trash2 className="w-3.5 h-3.5" />Clear</button>
                )}
              </div>
            }>
              {filteredCaptures.length === 0 ? (
                <div className="text-center py-12">
                  <History className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                  <p className="text-sm text-slate-500">No captures yet</p>
                  <p className="text-xs text-slate-600 mt-1">Use the Camera tab to capture and analyze</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {filteredCaptures.map(c => (
                    <div key={c.id}
                      className="flex items-start gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all"
                    >
                      <div className="w-9 h-9 rounded-lg bg-lumina-500/10 flex items-center justify-center shrink-0">
                        {c.type === 'capture' ? <Camera className="w-4 h-4 text-lumina-400" /> :
                         c.type === 'detect' ? <Scan className="w-4 h-4 text-lumina-400" /> :
                         c.type === 'face' ? <Eye className="w-4 h-4 text-lumina-400" /> :
                         <MessageSquare className="w-4 h-4 text-lumina-400" />}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium text-white capitalize">{c.type}</span>
                          <span className="text-[10px] text-slate-500">{new Date(c.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-[10px] text-slate-400 truncate mt-0.5">
                          {c.result.description || c.result.error || `Success: ${!!c.result.success}`}
                        </p>
                      </div>
                      <button onClick={() => copyResult(JSON.stringify(c.result, null, 2))}
                        className="p-1 text-slate-500 hover:text-white"
                      ><Copy className="w-3.5 h-3.5" /></button>
                    </div>
                  ))}
                </div>
              )}
            </CardSection>
          </div>
        )}
      </div>
    </div>
  );
}
