import { useState, useEffect } from 'react';
import {
  Brain, Activity, Database, Save, Play, TrendingUp,
  Search, Clock, Star, BarChart3, Layers, Zap,
  ChevronRight, Loader2, RefreshCw, Trash2, CheckCircle,
  XCircle, AlertCircle, BookOpen, Target, Eye,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/learning';

interface Stats {
  total_actions: number; patterns_learned: number;
  fields_remembered: number; workflows_saved: number;
}

interface Pattern {
  action: string; frequency: number; last_seen?: string;
}

interface Workflow {
  name: string; steps: number; created?: string;
}

interface MemoryField {
  form_id: string; field: string; value: string;
}

export default function LearningAgent() {
  const [tab, setTab] = useState('overview');
  const [stats, setStats] = useState<Stats | null>(null);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [patternSearch, setPatternSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [runningWorkflow, setRunningWorkflow] = useState<string | null>(null);
  const [rememberForm, setRememberForm] = useState('');
  const [rememberField, setRememberField] = useState('');
  const [rememberValue, setRememberValue] = useState('');
  const [showForm, setShowForm] = useState(false);
  const { addToast } = useToast();

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [sRes, pRes, wRes] = await Promise.all([
        fetch(`${BASE}/stats`).then(r => r.json()),
        fetch(`${BASE}/patterns`).then(r => r.json()),
        fetch(`${BASE}/workflows`).then(r => r.json()),
      ]);
      setStats(sRes.stats || sRes);
      setPatterns(pRes.patterns || []);
      setWorkflows(wRes.workflows || []);
    } catch {} finally { setLoading(false); }
  };

  const runWorkflow = async (name: string) => {
    setRunningWorkflow(name);
    try {
      const res = await fetch(`${BASE}/workflows/${encodeURIComponent(name)}/run`, { method: 'POST' });
      const data = await res.json();
      addToast(data.status === 'ok' ? `Workflow "${name}" completed` : `Workflow failed`, data.status === 'ok' ? 'success' : 'error');
    } catch (e: any) {
      addToast(`Error: ${e.message}`, 'error');
    } finally { setRunningWorkflow(null); }
  };

  const doRemember = async () => {
    if (!rememberForm.trim() || !rememberField.trim() || !rememberValue.trim()) return;
    try {
      await fetch(`${BASE}/remember`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ form_id: rememberForm, field: rememberField, value: rememberValue }),
      });
      addToast('Field remembered', 'success');
      setShowForm(false);
      setRememberForm(''); setRememberField(''); setRememberValue('');
      loadAll();
    } catch (e: any) { addToast(`Error: ${e.message}`, 'error'); }
  };

  const filteredPatterns = patterns.filter(p =>
    p.action.toLowerCase().includes(patternSearch.toLowerCase())
  );

  const statItems = [
    { label: 'Actions Tracked', value: stats?.total_actions || 0, icon: Activity, color: 'from-blue-500 to-blue-700' },
    { label: 'Patterns Learned', value: stats?.patterns_learned || 0, icon: Brain, color: 'from-lumina-500 to-lumina-700' },
    { label: 'Fields Remembered', value: stats?.fields_remembered || 0, icon: Database, color: 'from-emerald-500 to-emerald-700' },
    { label: 'Workflows Saved', value: stats?.workflows_saved || 0, icon: Save, color: 'from-amber-500 to-amber-700' },
  ];

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Brain} title="Learning Agent" description="AI that remembers patterns, fields, and workflows" />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['overview', 'patterns', 'workflows', 'teach'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'overview' ? <Activity className="w-3.5 h-3.5" /> : t === 'patterns' ? <Brain className="w-3.5 h-3.5" /> : t === 'workflows' ? <Layers className="w-3.5 h-3.5" /> : <BookOpen className="w-3.5 h-3.5" />}
            {t === 'teach' ? 'Teach' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-6 h-6 text-lumina-400 animate-spin" />
          </div>
        ) : tab === 'overview' ? (
          <div className="space-y-5">
            {/* Stats grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {statItems.map(s => (
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
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card>
                <CardSection label="Recent Patterns">
                  {patterns.slice(0, 5).map((p, i) => (
                    <div key={i} className="flex items-center justify-between py-1.5 text-xs">
                      <span className="text-slate-300">{p.action}</span>
                      <span className="text-slate-500">{p.frequency}x</span>
                    </div>
                  ))}
                  {patterns.length === 0 && <p className="text-xs text-slate-500 py-4 text-center">No patterns learned yet</p>}
                </CardSection>
              </Card>
              <Card>
                <CardSection label="Saved Workflows">
                  {workflows.slice(0, 5).map((w, i) => (
                    <div key={i} className="flex items-center justify-between py-1.5 text-xs">
                      <span className="text-slate-300">{w.name}</span>
                      <span className="text-slate-500">{w.steps} steps</span>
                    </div>
                  ))}
                  {workflows.length === 0 && <p className="text-xs text-slate-500 py-4 text-center">No workflows saved</p>}
                </CardSection>
              </Card>
            </div>
          </div>
        ) : tab === 'patterns' ? (
          <CardSection label="Learned Patterns" action={
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
              <input type="text" value={patternSearch} onChange={e => setPatternSearch(e.target.value)}
                placeholder="Search patterns..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-44"
              />
            </div>
          }>
            {filteredPatterns.length === 0 ? (
              <div className="text-center py-12">
                <Brain className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No patterns learned yet</p>
                <p className="text-xs text-slate-600 mt-1">Patterns appear as the AI learns from your actions</p>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredPatterns.map((p, i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/[0.02] transition-colors">
                    <div className="w-8 h-8 rounded-lg bg-lumina-500/10 flex items-center justify-center shrink-0">
                      <Zap className="w-4 h-4 text-lumina-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-slate-300 truncate">{p.action}</p>
                      <p className="text-[10px] text-slate-500">Last seen: {p.last_seen ? new Date(p.last_seen).toLocaleDateString() : 'N/A'}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3 text-emerald-400" />
                      <span className="text-xs font-medium text-slate-400">{p.frequency}x</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardSection>
        ) : tab === 'workflows' ? (
          <CardSection label="Saved Workflows" action={
            <button onClick={loadAll} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          }>
            {workflows.length === 0 ? (
              <div className="text-center py-12">
                <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No workflows saved</p>
                <p className="text-xs text-slate-600 mt-1">Workflows are created automatically as you perform multi-step tasks</p>
              </div>
            ) : (
              <div className="space-y-2">
                {workflows.map((w, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all group">
                    <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0">
                      <Layers className="w-4 h-4 text-amber-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white truncate">{w.name}</p>
                      <p className="text-[10px] text-slate-500">{w.steps} step(s) · {w.created ? new Date(w.created).toLocaleDateString() : 'N/A'}</p>
                    </div>
                    <button onClick={() => runWorkflow(w.name)} disabled={runningWorkflow === w.name}
                      className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 disabled:opacity-40 transition-colors"
                    >{runningWorkflow === w.name ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}Run</button>
                  </div>
                ))}
              </div>
            )}
          </CardSection>
        ) : (
          /* Teach tab */
          <div className="max-w-xl space-y-5">
            <Card>
              <CardSection label="Teach the AI">
                <p className="text-xs text-slate-400 mb-4">Manually teach the AI field values for specific forms. The AI will remember these automatically next time.</p>
                {!showForm ? (
                  <button onClick={() => setShowForm(true)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
                  ><BookOpen className="w-3.5 h-3.5" />Teach a Field</button>
                ) : (
                  <div className="space-y-3">
                    <input type="text" value={rememberForm} onChange={e => setRememberForm(e.target.value)}
                      placeholder="Form ID (e.g. login, checkout, contact)" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                    />
                    <div className="grid grid-cols-2 gap-3">
                      <input type="text" value={rememberField} onChange={e => setRememberField(e.target.value)}
                        placeholder="Field name (e.g. email)" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                      />
                      <input type="text" value={rememberValue} onChange={e => setRememberValue(e.target.value)}
                        placeholder="Value" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={doRemember}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
                      ><Save className="w-3.5 h-3.5" />Remember</button>
                      <button onClick={() => setShowForm(false)}
                        className="px-4 py-2 rounded-lg text-xs text-slate-400 hover:bg-white/5 transition-colors"
                      >Cancel</button>
                    </div>
                  </div>
                )}
              </CardSection>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
