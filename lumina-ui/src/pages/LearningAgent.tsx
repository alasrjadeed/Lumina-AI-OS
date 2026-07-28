import { useState, useEffect } from 'react';
import {
  Brain, Activity, Database, Save, Play, TrendingUp,
  Search, Layers, Zap, Loader2, RefreshCw, BookOpen,
  Plus, Lightbulb, Clock, Repeat, ArrowRight,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/learning';

interface Stats { total_actions: number; patterns_learned: number; fields_remembered: number; workflows_saved: number; }
interface Pattern { action: string; sequence: string[]; frequency: number; last_seen?: number; context?: string; }
interface Workflow { name: string; steps: number; created?: string; }

export default function LearningAgent() {
  const [tab, setTab] = useState('overview');
  const [stats, setStats] = useState<Stats | null>(null);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [fields, setFields] = useState<Record<string, string>>({});
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [runningWorkflow, setRunningWorkflow] = useState<string | null>(null);

  // Teach tab
  const [showForm, setShowForm] = useState(false);
  const [rememberForm, setRememberForm] = useState('');
  const [rememberField, setRememberField] = useState('');
  const [rememberValue, setRememberValue] = useState('');

  // Record action
  const [recordAction, setRecordAction] = useState('');
  const [recordModule, setRecordModule] = useState('');

  // Save workflow
  const [showWfForm, setShowWfForm] = useState(false);
  const [wfName, setWfName] = useState('');
  const [wfStepDesc, setWfStepDesc] = useState('');
  const [wfSteps, setWfSteps] = useState<string[]>([]);

  // Pattern search
  const [patternSearch, setPatternSearch] = useState('');

  // Field lookup
  const [lookupFormId, setLookupFormId] = useState('');

  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, []);
  useEffect(() => { loadAll(); }, [tab]);

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

  const doRecord = async () => {
    if (!recordAction.trim()) return;
    try {
      await fetch(`${BASE}/record`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: recordAction, module: recordModule }) });
      addToast('Action recorded', 'success');
      setRecordAction(''); setRecordModule('');
      loadAll();
    } catch (e: any) { addToast(`Error: ${e.message}`, 'error'); }
  };

  const doRemember = async () => {
    if (!rememberForm.trim() || !rememberField.trim() || !rememberValue.trim()) return;
    try {
      await fetch(`${BASE}/remember`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ form_id: rememberForm, field_name: rememberField, value: rememberValue }) });
      addToast('Field remembered', 'success');
      setShowForm(false); setRememberForm(''); setRememberField(''); setRememberValue('');
      loadAll();
    } catch (e: any) { addToast(`Error: ${e.message}`, 'error'); }
  };

  const runWorkflow = async (name: string) => {
    setRunningWorkflow(name);
    try {
      const res = await fetch(`${BASE}/workflows/${encodeURIComponent(name)}/run`, { method: 'POST' });
      const data = await res.json();
      addToast(data.status === 'ok' ? `"${name}" completed` : 'Workflow failed', data.status === 'ok' ? 'success' : 'error');
    } catch { addToast('Error', 'error'); }
    setRunningWorkflow(null);
  };

  const doSaveWorkflow = async () => {
    if (!wfName.trim() || wfSteps.length === 0) return;
    try {
      await fetch(`${BASE}/workflows`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: wfName, steps: wfSteps.map(s => ({ description: s })) }) });
      addToast('Workflow saved', 'success');
      setShowWfForm(false); setWfName(''); setWfSteps([]); setWfStepDesc('');
      loadAll();
    } catch (e: any) { addToast(`Error: ${e.message}`, 'error'); }
  };

  const doSuggest = async () => {
    if (!recordAction.trim()) return;
    try {
      const res = await fetch(`${BASE}/suggest/${encodeURIComponent(recordAction)}`); 
      const data = await res.json();
      setSuggestion(data.next);
    } catch { setSuggestion(null); }
  };

  const lookupFields = async () => {
    if (!lookupFormId.trim()) return;
    try {
      const res = await fetch(`${BASE}/fields/${encodeURIComponent(lookupFormId)}`);
      const data = await res.json();
      setFields(data.fields || {});
    } catch { setFields({}); }
  };

  const filteredPatterns = patterns.filter(p => p.action.toLowerCase().includes(patternSearch.toLowerCase()));

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
          <button key={t} onClick={() => setTab(t)} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}>
            {t === 'overview' ? <Activity className="w-3.5 h-3.5" /> : t === 'patterns' ? <Brain className="w-3.5 h-3.5" /> : t === 'workflows' ? <Layers className="w-3.5 h-3.5" /> : <BookOpen className="w-3.5 h-3.5" />}
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {loading ? <div className="flex items-center justify-center py-16"><Loader2 className="w-6 h-6 text-lumina-400 animate-spin" /></div>
        : tab === 'overview' ? (
          <div className="space-y-5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {statItems.map(s => (
                <div key={s.label} className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${s.color} p-[1px]`}>
                  <div className="rounded-2xl bg-slate-950/90 backdrop-blur-sm p-4">
                    <div className="flex items-start justify-between"><div><p className="text-[10px] font-medium text-white/60 uppercase tracking-wider">{s.label}</p><p className="text-lg font-bold text-white mt-1">{s.value}</p></div><s.icon className="w-5 h-5 text-white/30" /></div>
                  </div>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <Card><CardSection label="Recent Patterns">
                {patterns.slice(0, 8).map((p, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 text-xs">
                    <span className="text-slate-300 truncate flex-1 mr-2">{p.action}</span>
                    <span className="text-slate-500 shrink-0">{p.frequency}x</span>
                  </div>
                ))}
                {patterns.length === 0 && <p className="text-xs text-slate-500 py-4 text-center">No patterns learned yet</p>}
              </CardSection></Card>
              <Card><CardSection label="Saved Workflows">
                {workflows.slice(0, 8).map((w, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 text-xs">
                    <span className="text-slate-300 truncate">{w.name}</span>
                    <span className="text-slate-500 shrink-0">{w.steps} steps</span>
                  </div>
                ))}
                {workflows.length === 0 && <p className="text-xs text-slate-500 py-4 text-center">No workflows saved</p>}
              </CardSection></Card>
            </div>
          </div>

        ) : tab === 'patterns' ? (
          <div className="space-y-5 max-w-4xl">
            <Card><CardSection label="Learned Patterns" action={
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input value={patternSearch} onChange={e => setPatternSearch(e.target.value)} placeholder="Search patterns..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-44" />
              </div>}>
              {filteredPatterns.length === 0 ? <div className="text-center py-12"><Brain className="w-10 h-10 text-slate-600 mx-auto mb-3" /><p className="text-sm text-slate-500">No patterns yet</p></div>
              : <div className="space-y-1">
                {filteredPatterns.map((p, i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/[0.02] transition-colors">
                    <div className="w-8 h-8 rounded-lg bg-lumina-500/10 flex items-center justify-center shrink-0"><Zap className="w-4 h-4 text-lumina-400" /></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-slate-300 truncate">{p.action}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-slate-500 flex items-center gap-1"><Clock className="w-2.5 h-2.5" />{p.last_seen ? new Date(p.last_seen * 1000).toLocaleDateString() : 'N/A'}</span>
                        {p.context && <span className="text-[10px] text-slate-500 truncate">· {p.context}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0"><TrendingUp className="w-3 h-3 text-emerald-400" /><span className="text-xs font-medium text-slate-400">{p.frequency}x</span></div>
                  </div>
                ))}
              </div>}
            </CardSection></Card>
          </div>

        ) : tab === 'workflows' ? (
          <div className="space-y-5 max-w-4xl">
            <Card><CardSection label="Saved Workflows" action={
              <button onClick={() => setShowWfForm(!showWfForm)} className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"><Plus className="w-3.5 h-3.5" /> New</button>
            }>
              {showWfForm && <div className="mb-4 p-4 rounded-xl border border-lumina-500/20 bg-lumina-500/5 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="input-group"><label className="input-label">Workflow Name</label><input className="input" value={wfName} onChange={e => setWfName(e.target.value)} placeholder="My Workflow" /></div>
                  <div className="input-group"><label className="input-label">Add Step</label><div className="flex gap-2"><input className="input flex-1" value={wfStepDesc} onChange={e => setWfStepDesc(e.target.value)} placeholder="Step description" onKeyDown={e => { if (e.key === 'Enter' && wfStepDesc.trim()) { setWfSteps(s => [...s, wfStepDesc.trim()]); setWfStepDesc(''); } }} /><button onClick={() => { if (wfStepDesc.trim()) { setWfSteps(s => [...s, wfStepDesc.trim()]); setWfStepDesc(''); } }} className="btn btn-primary btn-sm">+</button></div></div>
                </div>
                {wfSteps.length > 0 && <div className="space-y-1">{wfSteps.map((s, i) => <div key={i} className="flex items-center gap-2 text-xs text-slate-300 bg-white/5 rounded px-3 py-1.5"><ArrowRight className="w-3 h-3 text-lumina-400 shrink-0" /><span className="flex-1">{s}</span><button onClick={() => setWfSteps(steps => steps.filter((_, j) => j !== i))} className="text-slate-500 hover:text-red-400">×</button></div>)}</div>}
                <div className="flex gap-2">
                  <button onClick={doSaveWorkflow} disabled={!wfName.trim() || wfSteps.length === 0} className="btn btn-primary btn-sm"><Save className="w-3.5 h-3.5" /> Save</button>
                  <button onClick={() => { setShowWfForm(false); setWfSteps([]); setWfName(''); }} className="btn btn-ghost btn-sm">Cancel</button>
                </div>
              </div>}
              {workflows.length === 0 ? <div className="text-center py-12"><Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" /><p className="text-sm text-slate-500">No workflows saved</p><p className="text-xs text-slate-600 mt-1">Create one above or they appear as AI learns your multi-step tasks</p></div>
              : <div className="space-y-2">
                {workflows.map((w, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] transition-all group">
                    <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center shrink-0"><Layers className="w-4 h-4 text-amber-400" /></div>
                    <div className="flex-1 min-w-0"><p className="text-xs font-medium text-white truncate">{w.name}</p><p className="text-[10px] text-slate-500">{w.steps} step(s) · {w.created ? new Date(w.created).toLocaleDateString() : 'N/A'}</p></div>
                    <button onClick={() => runWorkflow(w.name)} disabled={runningWorkflow === w.name} className="btn btn-primary btn-sm">{runningWorkflow === w.name ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}Run</button>
                  </div>
                ))}
              </div>}
            </CardSection></Card>
          </div>

        ) : (
          /* TEACH TAB */
          <div className="max-w-2xl space-y-5">
            {/* Record Action */}
            <Card><CardSection label="Record Action" action={<Repeat className="w-4 h-4 text-lumina-400" />}>
              <p className="text-xs text-slate-400 mb-3">Manually record an action so Lumina learns from it and can suggest next steps.</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
                <div className="input-group"><label className="input-label">Action</label><input className="input" value={recordAction} onChange={e => setRecordAction(e.target.value)} placeholder='e.g. "generate_report"' /></div>
                <div className="input-group"><label className="input-label">Module (optional)</label><input className="input" value={recordModule} onChange={e => setRecordModule(e.target.value)} placeholder='e.g. "crm"' /></div>
                <div className="flex gap-2">
                  <button onClick={doRecord} disabled={!recordAction.trim()} className="btn btn-primary btn-sm">Record</button>
                  <button onClick={doSuggest} disabled={!recordAction.trim()} className="btn btn-secondary btn-sm"><Lightbulb className="w-3.5 h-3.5" /> Suggest</button>
                </div>
              </div>
              {suggestion && <p className="text-xs text-lumina-300 mt-2 flex items-center gap-1"><Lightbulb className="w-3.5 h-3.5" /> Next suggested: <strong>{suggestion}</strong></p>}
            </CardSection></Card>

            {/* Remember Field */}
            <Card><CardSection label="Teach a Field" action={<Database className="w-4 h-4 text-emerald-400" />}>
              <p className="text-xs text-slate-400 mb-3">Teach Lumina field values for specific forms. AI auto-fills these next time.</p>
              {!showForm ? (
                <button onClick={() => setShowForm(true)} className="btn btn-secondary btn-sm"><BookOpen className="w-3.5 h-3.5" /> Teach a Field</button>
              ) : (
                <div className="space-y-3">
                  <input className="input" value={rememberForm} onChange={e => setRememberForm(e.target.value)} placeholder="Form ID (e.g. login, checkout, contact)" />
                  <div className="grid grid-cols-2 gap-3">
                    <input className="input" value={rememberField} onChange={e => setRememberField(e.target.value)} placeholder="Field name (e.g. email)" />
                    <input className="input" value={rememberValue} onChange={e => setRememberValue(e.target.value)} placeholder="Value" />
                  </div>
                  <div className="flex gap-2">
                    <button onClick={doRemember} className="btn btn-primary btn-sm"><Save className="w-3.5 h-3.5" /> Remember</button>
                    <button onClick={() => setShowForm(false)} className="btn btn-ghost btn-sm">Cancel</button>
                  </div>
                </div>
              )}
            </CardSection></Card>

            {/* Lookup Fields */}
            <Card><CardSection label="Lookup Stored Fields" action={<Search className="w-4 h-4 text-amber-400" />}>
              <div className="flex gap-3 items-end mb-3">
                <div className="input-group flex-1"><label className="input-label">Form ID</label><input className="input" value={lookupFormId} onChange={e => setLookupFormId(e.target.value)} placeholder="login, checkout, contact" onKeyDown={e => e.key === 'Enter' && lookupFields()} /></div>
                <button onClick={lookupFields} className="btn btn-secondary btn-sm"><Search className="w-3.5 h-3.5" /> Lookup</button>
              </div>
              {Object.keys(fields).length > 0 && (
                <div className="space-y-1">
                  {Object.entries(fields).map(([k, v]) => (
                    <div key={k} className="flex items-center justify-between py-1.5 px-3 rounded bg-white/[0.02] text-xs">
                      <span className="text-slate-300">{k}</span>
                      <span className="text-slate-500">{v}</span>
                    </div>
                  ))}
                </div>
              )}
              {lookupFormId && Object.keys(fields).length === 0 && <p className="text-xs text-slate-500">No fields found for "{lookupFormId}"</p>}
            </CardSection></Card>
          </div>
        )}
      </div>
    </div>
  );
}
