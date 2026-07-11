import { useState, useEffect, useCallback } from 'react';
import {
  Code2, Loader2, Search, Shield, Bug, Zap, Palette,
  CheckCircle, FileText, AlertTriangle, AlertCircle, Info,
  ArrowRight, ChevronRight, RefreshCw, History,
  Sparkles,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/code';

interface Issue {
  id: string; severity: string; title: string; description: string;
  line: number; column: number; snippet: string; dimension: string; suggestion: string;
}

interface ReviewResult {
  review_id: string; language: string; code_preview: string; code_length: number;
  score: number; issues: Issue[]; summary: string; ai_feedback: string;
  dimensions: Record<string, { count: number; weighted: number; label: string }>;
  stats: Record<string, number>; created_at: string;
}

interface DimensionInfo { id: string; label: string; icon: string; color: string; }

const SEVERITY_ICONS: Record<string, any> = {
  critical: AlertCircle, high: AlertTriangle,
  warning: AlertTriangle, medium: Info, info: Info,
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'text-red-400 bg-red-500/10 border-red-500/20',
  high: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  warning: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
  info: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
};

const DIM_COLORS: Record<string, string> = {
  security: 'text-red-400', bugs: 'text-orange-400',
  performance: 'text-amber-400', style: 'text-blue-400',
  best_practices: 'text-emerald-400', maintainability: 'text-violet-400',
};

const DIM_ICONS: Record<string, any> = {
  security: Shield, bugs: Bug, performance: Zap,
  style: Palette, best_practices: CheckCircle, maintainability: FileText,
};

const LANGUAGES = [
  { id: 'python', label: 'Python' }, { id: 'javascript', label: 'JavaScript' },
  { id: 'typescript', label: 'TypeScript' }, { id: 'java', label: 'Java' },
  { id: 'go', label: 'Go' }, { id: 'rust', label: 'Rust' },
  { id: 'cpp', label: 'C++' }, { id: 'csharp', label: 'C#' },
  { id: 'ruby', label: 'Ruby' }, { id: 'php', label: 'PHP' },
  { id: 'kotlin', label: 'Kotlin' }, { id: 'swift', label: 'Swift' },
  { id: 'sql', label: 'SQL' }, { id: 'bash', label: 'Bash' },
];

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const SAMPLES: Record<string, string> = {
  python: `def get_user(user_id):\n    query = f"SELECT * FROM users WHERE id = {user_id}"\n    conn.execute(query)\n    return None\n\ndef process(items):\n    for i in range(len(items)):\n        print(items[i])\n\ntry:\n    result = 1 / 0\nexcept:\n    pass`,
  javascript: `function save(data) {\n  localStorage.setItem("token", "sk-abc123-secret");\n  document.getElementById("result").innerHTML = data;\n  console.log("saved:", data);\n  return eval(data.config);\n}`,
  typescript: `function process(data: any) {\n  return data.name! + 1;\n}\n\ntry {\n  risky();\n} catch { }`,
};

export default function CodeReview() {
  const [tab, setTab] = useState('review');
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [history, setHistory] = useState<ReviewResult[]>([]);
  const [selectedReview, setSelectedReview] = useState<ReviewResult | null>(null);
  const [dimensions, setDimensions] = useState<DimensionInfo[]>([]);
  const { addToast } = useToast();

  const loadAll = useCallback(async () => {
    try {
      const [dims, hist] = await Promise.all([
        get<{ dimensions: DimensionInfo[] }>('/review/dimensions'),
        get<{ reviews: ReviewResult[] }>('/review/history?limit=20'),
      ]);
      setDimensions(dims.dimensions);
      setHistory(hist.reviews);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const submitReview = async () => {
    if (!code.trim() || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await post<ReviewResult>('/review', { code, language });
      setResult(res);
      addToast(`Review complete: ${res.score}/100`, 'success');
      loadAll();
    } catch {
      addToast('Review failed', 'error');
    }
    setLoading(false);
  };

  const loadSample = (lang: string) => {
    setLanguage(lang);
    setCode(SAMPLES[lang] || '');
  };

  const tabs = [
    { id: 'review', label: 'Review', icon: Code2 },
    { id: 'history', label: `History (${history.length})`, icon: History },
  ];

  return (
    <div className="p-6 space-y-6">
      <PageHeader icon={Code2} title="Code Review" description="Static analysis + AI-powered code quality review" />

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

      {tab === 'review' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <Card hover={false} className="space-y-4">
              <div className="flex items-center justify-between">
                <CardSection label="Code Input">
                  <div className="flex items-center gap-2">
                    <select value={language} onChange={e => setLanguage(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none focus:border-lumina-500/50">
                      {LANGUAGES.map(l => <option key={l.id} value={l.id}>{l.label}</option>)}
                    </select>
                  </div>
                </CardSection>
                <div className="flex items-center gap-1">
                  {Object.keys(SAMPLES).includes(language) && (
                    <button onClick={() => loadSample(language)}
                      className="text-[10px] text-lumina-400 hover:text-lumina-300 px-2 py-1 rounded-lg hover:bg-lumina-600/10 transition-colors flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Load Sample
                    </button>
                  )}
                </div>
              </div>
              <textarea value={code} onChange={e => setCode(e.target.value)} rows={14}
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 resize-none font-mono leading-relaxed"
                placeholder={`Paste your ${language} code here for review...`} />
              <div className="flex items-center gap-3">
                <button onClick={submitReview} disabled={loading || !code.trim()}
                  className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-6 py-2.5 text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-lumina-500/20">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  {loading ? 'Reviewing...' : 'Review Code'}
                </button>
                <span className="text-[10px] text-slate-600">{code.length} chars</span>
              </div>
            </Card>

            {result && (
              <Card hover={false} className="space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`text-2xl font-bold ${
                      result.score >= 80 ? 'text-emerald-400' : result.score >= 50 ? 'text-amber-400' : 'text-red-400'
                    }`}>{result.score}/100</div>
                    <div className="w-px h-8 bg-white/10" />
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-slate-500">Quality Score</span>
                      <span className="text-xs text-slate-400">{result.issues.length} issues</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {Object.entries(result.stats).map(([sev, count]) => (
                      <span key={sev} className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                        sev === 'critical' ? 'bg-red-500/10 text-red-400' :
                        sev === 'high' ? 'bg-orange-500/10 text-orange-400' :
                        sev === 'medium' ? 'bg-amber-500/10 text-amber-400' :
                        'bg-blue-500/10 text-blue-400'
                      }`}>{count} {sev}</span>
                    ))}
                  </div>
                </div>

                <p className="text-xs text-slate-400">{result.summary}</p>

                {/* Dimension scores */}
                <div className="grid grid-cols-3 gap-2">
                  {dimensions.map(d => {
                    const dim = result.dimensions[d.id];
                    if (!dim) return null;
                    const Icon = DIM_ICONS[d.id] || Shield;
                    const color = DIM_COLORS[d.id] || 'text-slate-400';
                    const barColor = dim.count === 0 ? 'bg-emerald-500' :
                      dim.weighted <= 3 ? 'bg-amber-500' : 'bg-red-500';
                    return (
                      <div key={d.id} className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
                        <div className="flex items-center gap-2 mb-1.5">
                          <Icon className={`w-3.5 h-3.5 ${color}`} />
                          <span className="text-[10px] text-slate-500">{d.label}</span>
                        </div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-slate-300">{dim.count} issue{dim.count !== 1 ? 's' : ''}</span>
                        </div>
                        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full transition-all ${barColor}`}
                            style={{ width: `${Math.min(100, dim.weighted * 10)}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* AI Feedback */}
                {result.ai_feedback && !result.ai_feedback.startsWith('AI review error') && !result.ai_feedback.startsWith('AI review unavailable') && (
                  <div className="bg-lumina-600/5 border border-lumina-500/20 rounded-xl p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Sparkles className="w-4 h-4 text-lumina-400" />
                      <span className="text-xs font-medium text-lumina-300">AI Analysis</span>
                    </div>
                    <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{result.ai_feedback}</pre>
                  </div>
                )}

                {/* Issues list */}
                {result.issues.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Issues</p>
                    <div className="max-h-96 overflow-y-auto space-y-1.5">
                      {result.issues.map((issue, i) => {
                        const SevIcon = SEVERITY_ICONS[issue.severity] || Info;
                        const sevColor = SEVERITY_COLORS[issue.severity] || 'text-slate-400 bg-white/5';
                        const DimIcon = DIM_ICONS[issue.dimension] || FileText;
                        return (
                          <div key={`${issue.id}-${i}`}
                            className="bg-white/[0.02] border border-white/5 rounded-xl p-3 hover:bg-white/[0.04] transition-colors">
                            <div className="flex items-start gap-3">
                              <SevIcon className={`w-4 h-4 shrink-0 mt-0.5 ${sevColor.split(' ')[0]}`} />
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2">
                                  <span className="text-xs font-medium text-slate-200">{issue.title}</span>
                                  <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${sevColor}`}>{issue.severity}</span>
                                  <DimIcon className={`w-3 h-3 ${DIM_COLORS[issue.dimension] || 'text-slate-500'}`} />
                                </div>
                                {issue.snippet && (
                                  <code className="text-[10px] text-slate-500 font-mono block mt-1 bg-slate-950/50 rounded px-2 py-1 truncate">{issue.snippet}</code>
                                )}
                                {issue.line > 0 && <span className="text-[10px] text-slate-600 mt-1 block">Line {issue.line}</span>}
                                {issue.suggestion && (
                                  <div className="flex items-start gap-1.5 mt-1.5 text-[10px] text-emerald-400">
                                    <ArrowRight className="w-3 h-3 shrink-0 mt-0.5" />
                                    <span>{issue.suggestion}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </Card>
            )}
          </div>

          <div className="space-y-4">
            <Card hover={false} className="space-y-4 sticky top-4">
              <CardSection label="Quality Dimensions">
                <div className="space-y-2">
                  {dimensions.map(d => {
                    const Icon = DIM_ICONS[d.id] || Shield;
                    const color = DIM_COLORS[d.id] || 'text-slate-400';
                    return (
                      <div key={d.id} className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                        <Icon className={`w-4 h-4 ${color}`} />
                        <span className="text-xs text-slate-400">{d.label}</span>
                      </div>
                    );
                  })}
                </div>
              </CardSection>

              <CardSection label="Quick Samples">
                <div className="space-y-1.5">
                  {Object.entries(SAMPLES).map(([lang]) => (
                    <button key={lang} onClick={() => loadSample(lang)}
                      className="w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] transition-all">
                      <Code2 className="w-3.5 h-3.5 text-lumina-400" />
                      {LANGUAGES.find(l => l.id === lang)?.label || lang}
                    </button>
                  ))}
                </div>
              </CardSection>

              <CardSection label="Supported Languages">
                <div className="flex flex-wrap gap-1">
                  {LANGUAGES.map(l => (
                    <span key={l.id} className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500">{l.label}</span>
                  ))}
                </div>
              </CardSection>
            </Card>
          </div>
        </div>
      )}

      {/* History */}
      {tab === 'history' && (
        <div className="space-y-4">
          {selectedReview ? (
            <div className="space-y-4">
              <button onClick={() => setSelectedReview(null)} className="text-xs text-lumina-400 hover:text-lumina-300 flex items-center gap-1">
                <ChevronRight className="w-3 h-3 rotate-180" /> Back to history
              </button>
              <Card hover={false} className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`text-lg font-bold ${
                      selectedReview.score >= 80 ? 'text-emerald-400' : selectedReview.score >= 50 ? 'text-amber-400' : 'text-red-400'
                    }`}>{selectedReview.score}/100</div>
                    <div className="w-px h-6 bg-white/10" />
                    <div>
                      <p className="text-xs font-medium text-slate-200">{selectedReview.language}</p>
                      <p className="text-[10px] text-slate-500">{new Date(selectedReview.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-600">{selectedReview.code_length} chars</span>
                </div>
                <p className="text-xs text-slate-400">{selectedReview.summary}</p>
                <div className="bg-slate-950/50 rounded-xl p-3 border border-white/5">
                  <pre className="text-[10px] text-slate-500 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">{selectedReview.code_preview}</pre>
                </div>
                {selectedReview.issues.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-xs font-medium text-slate-500">Issues ({selectedReview.issues.length})</p>
                    {selectedReview.issues.map((issue, i) => (
                      <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                        <div className={`w-1.5 h-1.5 rounded-full mt-1 shrink-0 ${
                          issue.severity === 'critical' ? 'bg-red-500' :
                          issue.severity === 'high' ? 'bg-orange-500' :
                          issue.severity === 'warning' ? 'bg-amber-500' : 'bg-blue-500'
                        }`} />
                        <div className="min-w-0">
                          <p className="text-[10px] text-slate-300">{issue.title}</p>
                          {issue.suggestion && <p className="text-[9px] text-emerald-400 mt-0.5">{issue.suggestion}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">{history.length} reviews</span>
                <button onClick={loadAll} className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              {history.length === 0 ? (
                <Card hover={false} className="text-center py-12">
                  <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                  <p className="text-sm text-slate-400">No reviews yet</p>
                  <p className="text-xs text-slate-500 mt-1">Submit code for review to see history here</p>
                </Card>
              ) : (
                <div className="space-y-2">
                  {history.map(r => (
                    <Card key={r.review_id} onClick={() => setSelectedReview(r)} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className={`text-sm font-bold shrink-0 ${
                            r.score >= 80 ? 'text-emerald-400' : r.score >= 50 ? 'text-amber-400' : 'text-red-400'
                          }`}>{r.score}</div>
                          <div className="min-w-0">
                            <p className="text-xs font-medium text-slate-200 truncate">{r.language}</p>
                            <p className="text-[10px] text-slate-500">{r.issues.length} issues · {r.code_length} chars</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1">
                            {Object.entries(r.stats || {}).filter(([_, c]) => c > 0).map(([sev, count]) => (
                              <span key={sev} className={`text-[9px] px-1 py-0.5 rounded-full ${
                                sev === 'critical' ? 'bg-red-500/10 text-red-400' :
                                sev === 'high' ? 'bg-orange-500/10 text-orange-400' : 'bg-amber-500/10 text-amber-400'
                              }`}>{count}</span>
                            ))}
                          </div>
                          <ChevronRight className="w-3 h-3 text-slate-500" />
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
