import { useState, useEffect } from 'react';
import { Video, Play, Settings, Image, Music, MessageSquare, RefreshCw, Zap, Film, Clock, CheckCircle, XCircle, Loader2, ExternalLink } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const VS_BASE = 'http://localhost:8000/api';

async function vsGet<T>(path: string): Promise<T> {
  try { const r = await fetch(`${VS_BASE}${path}`); if (!r.ok) throw new Error(); return r.json(); }
  catch { return [] as any; }
}

async function vsPost<T>(path: string, body?: any): Promise<T> {
  const r = await fetch(`${VS_BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function StatCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: any; color: string }) {
  const colors: Record<string, string> = { brand: 'var(--brand-500)', green: 'var(--color-success)', amber: 'var(--color-warning)', red: 'var(--color-error)', blue: 'var(--color-info)' };
  return <div className="bg-[var(--bg-tertiary)] rounded-xl p-4"><div className="flex items-center justify-between"><p className="text-2xs text-[var(--text-tertiary)] uppercase">{label}</p><Icon className="w-4 h-4" style={{ color: colors[color] }} /></div><p className="text-2xl font-bold mt-1" style={{ color: colors[color] }}>{value}</p></div>;
}

function Skeleton({ h = 'h-12' }: { h?: string }) { return <div className={`skeleton ${h} w-full`} />; }

export default function VideoStudio() {
  const [tab, setTab] = useState<'generate' | 'tasks' | 'resources'>('generate');
  const [tasks, setTasks] = useState<any[]>([]);
  const [workflows, setWorkflows] = useState<string[]>([]);
  const [templates, setTemplates] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);
  const [genForm, setGenForm] = useState({ prompt: '', workflow: 'standard', width: 1080, height: 1920 });
  const [generating, setGenerating] = useState(false);
  const { addToast } = useToast();

  useEffect(() => { checkConnection(); }, [tab]);

  async function checkConnection() {
    setLoading(true);
    try {
      const health: any = await vsGet('/health');
      setConnected(true);
      if (tab === 'tasks') setTasks((await vsGet('/tasks?limit=20')) || []);
      if (tab === 'resources') {
        const wf: any = await vsGet('/resources/workflows/media');
        setWorkflows(wf?.workflows || wf || []);
        const tpl: any = await vsGet('/resources/templates');
        setTemplates(tpl?.templates || tpl || []);
      }
    } catch { setConnected(false); }
    setLoading(false);
  }

  async function handleGenerate() {
    if (!genForm.prompt.trim()) { addToast('Enter a prompt', 'error'); return; }
    setGenerating(true);
    try {
      const result: any = await vsPost('/video/generate/async', { prompt: genForm.prompt, pipeline_type: genForm.workflow, width: genForm.width, height: genForm.height });
      addToast(`Video generation started: ${result.task_id}`, 'success');
      setTab('tasks'); checkConnection();
    } catch (e: any) { addToast(e.message || 'Video Studio not available', 'error'); }
    setGenerating(false);
  }

  const statusIcon = (s: string) => s === 'completed' ? <CheckCircle className="w-4 h-4 text-green-400" /> : s === 'failed' ? <XCircle className="w-4 h-4 text-red-400" /> : s === 'running' ? <Loader2 className="w-4 h-4 animate-spin text-blue-400" /> : <Clock className="w-4 h-4 text-amber-400" />;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Video Studio</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">AI video generation · ComfyUI + RunningHub · TTS · Templates</p></div>
        <div className="flex items-center gap-2">
          {connected ? <span className="badge badge-success flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Connected</span>
            : <span className="badge badge-error flex items-center gap-1"><XCircle className="w-3 h-3" /> Offline</span>}
          <button onClick={checkConnection} className="btn btn-ghost btn-sm"><RefreshCw className="w-3.5 h-3.5" /></button>
        </div>
      </div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {[{ id: 'generate' as const, l: 'Generate', i: Play }, { id: 'tasks' as const, l: 'Tasks', i: Film }, { id: 'resources' as const, l: 'Resources', i: Settings }].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.i className="w-3.5 h-3.5" /> {t.l}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {!connected && <div className="mb-6 bg-[var(--color-warning-bg)] border border-[var(--color-warning)]/20 rounded-xl p-4 text-sm text-[var(--color-warning)]">Video Studio not connected. Start the server: <code className="bg-black/20 px-1.5 py-0.5 rounded">cd "Lumina Video Studio" && bash scripts/start_servers.sh</code></div>}

        {/* GENERATE */}
        {tab === 'generate' && (
          <Card><div className="space-y-4">
            <h2 className="text-lg font-semibold">Create AI Video</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
              <div className="input-group"><label className="input-label">Workflow</label><select className="select" value={genForm.workflow} onChange={e => setGenForm(p => ({ ...p, workflow: e.target.value }))}>{['standard','linear','custom','asset_based','motion_transfer'].map(w => <option key={w} value={w}>{w}</option>)}</select></div>
              <div className="input-group"><label className="input-label">Width</label><input className="input" type="number" value={genForm.width} onChange={e => setGenForm(p => ({ ...p, width: +e.target.value }))} /></div>
              <div className="input-group"><label className="input-label">Height</label><input className="input" type="number" value={genForm.height} onChange={e => setGenForm(p => ({ ...p, height: +e.target.value }))} /></div>
            </div>
            <div className="input-group"><label className="input-label">Prompt / Topic</label><textarea className="input h-24" value={genForm.prompt} onChange={e => setGenForm(p => ({ ...p, prompt: e.target.value }))} placeholder="A tour of Bahrain's best restaurants with aerial shots..." /></div>
            <button onClick={handleGenerate} disabled={generating || !connected} className="btn btn-primary btn-lg">{generating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />} Generate Video</button>
          </div></Card>
        )}

        {/* TASKS */}
        {tab === 'tasks' && (
          <div className="space-y-3">
            {loading ? <div className="space-y-2">{Array(3).fill(0).map((_,i) => <Skeleton key={i} h="h-24" />)}</div>
            : tasks.length === 0 ? <div className="text-center py-12 text-[var(--text-tertiary)]"><Film className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No video tasks yet</p><p className="text-xs mt-1">Generate a video to see tasks here</p></div>
            : tasks.map((t: any) => (
              <div key={t.task_id || t.id} className="bg-[var(--bg-tertiary)] rounded-xl p-4 hover:bg-[var(--bg-hover)] transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {statusIcon(t.status)}
                    <span className="font-medium text-sm">{t.prompt?.substring(0, 60) || t.task_id || t.id}</span>
                  </div>
                  <span className={`badge ${t.status === 'completed' ? 'badge-success' : t.status === 'failed' ? 'badge-error' : t.status === 'running' ? 'badge-info' : 'badge-warning'}`}>{t.status}</span>
                </div>
                {t.progress && (
                  <div className="mt-2">
                    <div className="flex items-center justify-between text-2xs text-[var(--text-secondary)] mb-1"><span>{t.progress.message || t.progress.current}/{t.progress.total}</span><span>{Math.round(t.progress.percentage || 0)}%</span></div>
                    <div className="w-full h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden"><div className="h-full bg-[var(--brand-500)] rounded-full transition-all" style={{ width: `${Math.round(t.progress.percentage || 0)}%` }} /></div>
                  </div>
                )}
                {t.result?.file_path && <a href={`${VS_BASE}/files/${t.result.file_path}`} target="_blank" className="btn btn-secondary btn-sm mt-2"><ExternalLink className="w-3 h-3" /> View Output</a>}
              </div>
            ))}
          </div>
        )}

        {/* RESOURCES */}
        {tab === 'resources' && (
          <div className="space-y-6">
            <Card><div className="space-y-3">
              <h2 className="text-lg font-semibold"><Settings className="inline w-5 h-5 mr-1" /> Workflows ({workflows.length})</h2>
              <div className="flex flex-wrap gap-2">
                {workflows.map((w: any) => <span key={typeof w === 'string' ? w : w.name} className="badge badge-brand">{typeof w === 'string' ? w : w.name || w.id}</span>)}
                {workflows.length === 0 && <span className="text-sm text-[var(--text-tertiary)]">No workflows loaded</span>}
              </div>
            </div></Card>
            <Card><div className="space-y-3">
              <h2 className="text-lg font-semibold"><Image className="inline w-5 h-5 mr-1" /> Templates ({templates.length})</h2>
              <div className="flex flex-wrap gap-2">
                {templates.map((t: any) => <span key={typeof t === 'string' ? t : t.name} className="badge badge-info">{typeof t === 'string' ? t : t.name || t.path}</span>)}
                {templates.length === 0 && <span className="text-sm text-[var(--text-tertiary)]">No templates loaded</span>}
              </div>
            </div></Card>
          </div>
        )}
      </div>
    </div>
  );
}
