import { useState, useEffect, useCallback } from 'react';
import {
  Code2, Loader2, Copy, Check, Play, Download, Trash2,
  Globe, Monitor, Cpu, FileType, Sparkles, History, BookTemplate,
  ChevronRight, RefreshCw, Zap, Layers, Clock, Search,
  FileCode, Braces, Terminal, Database, Hash, Palette,
  ArrowRight, X, Plus,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/code';

const LANGUAGES = [
  { id: 'python', icon: FileCode, color: 'text-blue-400' },
  { id: 'javascript', icon: FileCode, color: 'text-yellow-400' },
  { id: 'typescript', icon: FileCode, color: 'text-blue-500' },
  { id: 'html', icon: Globe, color: 'text-orange-400' },
  { id: 'css', icon: Palette, color: 'text-purple-400' },
  { id: 'java', icon: Cpu, color: 'text-red-400' },
  { id: 'go', icon: Hash, color: 'text-cyan-400' },
  { id: 'rust', icon: Braces, color: 'text-orange-500' },
  { id: 'kotlin', icon: Code2, color: 'text-violet-400' },
  { id: 'sql', icon: Database, color: 'text-emerald-400' },
  { id: 'bash', icon: Terminal, color: 'text-slate-400' },
  { id: 'c', icon: Code2, color: 'text-blue-400' },
  { id: 'cpp', icon: Code2, color: 'text-blue-600' },
  { id: 'csharp', icon: FileCode, color: 'text-green-500' },
  { id: 'php', icon: FileCode, color: 'text-indigo-400' },
  { id: 'ruby', icon: Code2, color: 'text-red-500' },
  { id: 'swift', icon: Monitor, color: 'text-orange-400' },
  { id: 'dart', icon: Code2, color: 'text-teal-400' },
  { id: 'scala', icon: Braces, color: 'text-red-400' },
  { id: 'r', icon: Code2, color: 'text-blue-600' },
  { id: 'yaml', Icon: FileType, color: 'text-slate-500' },
  { id: 'json', Icon: Braces, color: 'text-green-400' },
  { id: 'xml', Icon: Code2, color: 'text-orange-400' },
  { id: 'markdown', icon: FileType, color: 'text-slate-500' },
];

const MODES = [
  { id: 'quick', label: 'Quick', desc: 'Concise, minimal code', icon: Zap },
  { id: 'production', label: 'Production', desc: 'Error handling, types, docs', icon: Layers },
  { id: 'explain', label: 'Explained', desc: 'Detailed inline comments', icon: Sparkles },
];

const WEB_LANGS = ['html', 'css', 'javascript', 'js', 'react', 'jsx', 'tsx', 'vue'];

interface Template {
  id: string; title: string; lang: string; framework: string; desc: string; code: string;
}
interface HistoryItem {
  id: string; description: string; language: string; framework: string | null;
  mode: string; code_length: number; timestamp: string;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function detectLang(label: string): string {
  const langs = ['python', 'javascript', 'typescript', 'html', 'css', 'java', 'go', 'rust', 'kotlin', 'sql', 'bash', 'c', 'cpp', 'php', 'ruby', 'swift', 'dart'];
  const lower = label.toLowerCase();
  if (lower === 'js') return 'javascript';
  if (lower === 'ts') return 'typescript';
  if (lower === 'py') return 'python';
  if (lower === 'rs') return 'rust';
  if (lower === 'kt') return 'kotlin';
  if (lower === 'rb') return 'ruby';
  if (lower === 'sh') return 'bash';
  for (const l of langs) { if (lower.includes(l)) return l; }
  return '';
}

const LANG_COLORS: Record<string, string> = {
  python: '#3572A5', javascript: '#f7df1e', typescript: '#3178c6',
  html: '#e34c26', css: '#563d7c', java: '#b07219',
  go: '#00ADD8', rust: '#dea584', kotlin: '#A97BFF',
  sql: '#e38c00', bash: '#89e051', c: '#555555',
  cpp: '#f34b7d', php: '#4F5D95', ruby: '#701516',
};

export default function CodeGenerator() {
  const [tab, setTab] = useState('generate');
  const [desc, setDesc] = useState('');
  const [lang, setLang] = useState('python');
  const [framework, setFramework] = useState('');
  const [frameworks, setFrameworks] = useState<string[]>([]);
  const [mode, setMode] = useState('quick');
  const [code, setCode] = useState('');
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [testUrl, setTestUrl] = useState('');
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templateFilter, setTemplateFilter] = useState('');
  const [selectedHistory, setSelectedHistory] = useState<HistoryItem | null>(null);
  const { addToast } = useToast();

  const loadFrameworks = useCallback(async (l: string) => {
    try {
      const res = await get<{ frameworks: string[] }>(`/frameworks?language=${l}`);
      setFrameworks(res.frameworks);
      setFramework('');
    } catch { setFrameworks([]); }
  }, []);

  const loadAll = useCallback(async () => {
    try {
      const [tRes, hRes] = await Promise.all([
        get<{ templates: Template[] }>('/templates'),
        get<{ items: HistoryItem[] }>('/generate/history'),
      ]);
      setTemplates(tRes.templates);
      setHistory(hRes.items);
    } catch { /* silent */ }
  }, []);

  useEffect(() => { loadAll(); loadFrameworks(lang); }, [loadAll, lang, loadFrameworks]);

  const generate = async () => {
    if (!desc.trim() || loading) return;
    setLoading(true);
    setCode('');
    setExplanation('');
    setTestUrl('');
    try {
      const res = await post<{ code: string; explanation: string; language: string }>('/generate', {
        description: desc,
        language: lang,
        framework: framework || null,
        mode,
      });
      setCode(res.code);
      setExplanation(res.explanation);
      addToast('Code generated successfully', 'success');
      loadAll();
    } catch {
      setCode('// Error generating code. Check server connection.');
      addToast('Generation failed', 'error');
    }
    setLoading(false);
  };

  const copyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadCode = () => {
    const ext = lang === 'python' ? 'py' : lang === 'javascript' ? 'js' : lang === 'typescript' ? 'ts' : lang;
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `code.${ext}`; a.click();
    URL.revokeObjectURL(url);
  };

  const testInBrowser = async () => {
    if (!code.trim()) return;
    try {
      const res = await fetch('/api/code/preview', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ code, language: lang }) });
      const data = await res.json();
      if (data.preview_url) { setTestUrl(data.preview_url); window.open(data.preview_url, '_blank'); }
    } catch { addToast('Failed to create preview', 'error'); }
  };

  const loadTemplate = (t: Template) => {
    setLang(t.lang);
    setFramework(t.framework || '');
    setDesc(`Generate a ${t.title.toLowerCase()} — ${t.desc}`);
    setTab('generate');
    addToast(`Loaded template: ${t.title}`, 'info');
  };

  const loadHistoryItem = (item: HistoryItem) => {
    setLang(item.language);
    setFramework(item.framework || '');
    setMode(item.mode);
    setDesc(item.description);
    setTab('generate');
  };

  const canTest = WEB_LANGS.includes(lang) && !!code;

  const langInfo = LANGUAGES.find(l => l.id === lang);
  const LangIcon = langInfo?.icon || Code2;
  const langColor = langInfo?.color || 'text-slate-400';

  const tabs = [
    { id: 'generate', label: 'Generate', icon: Sparkles },
    { id: 'templates', label: `Templates (${templates.length})`, icon: BookTemplate },
    { id: 'history', label: `History (${history.length})`, icon: History },
  ];

  return (
    <div className="p-6 space-y-6">
      <PageHeader icon={Code2} title="Code Generator" description="AI-powered code generation with framework support & templates" />

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

      {tab === 'generate' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {/* Input */}
            <Card hover={false} className="space-y-4">
              <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={4}
                className="w-full bg-slate-950 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 resize-none"
                placeholder="Describe what code you want to generate... e.g. 'A FastAPI CRUD for a todo app with SQLite'"
              />

              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">Lang</span>
                  <select value={lang} onChange={e => setLang(e.target.value)}
                    className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none focus:border-lumina-500/50">
                    {LANGUAGES.map(l => (
                      <option key={l.id} value={l.id}>{l.id}</option>
                    ))}
                  </select>
                </div>

                {frameworks.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider">FW</span>
                    <select value={framework} onChange={e => setFramework(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none focus:border-lumina-500/50">
                      <option value="">None</option>
                      {frameworks.map(f => <option key={f} value={f}>{f}</option>)}
                    </select>
                  </div>
                )}

                <div className="flex items-center gap-1">
                  {MODES.map(m => {
                    const MIcon = m.icon;
                    const active = mode === m.id;
                    return (
                      <button key={m.id} onClick={() => setMode(m.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-medium transition-all ${
                          active
                            ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20'
                            : 'text-slate-500 hover:text-slate-300 border border-transparent'
                        }`}
                        title={m.desc}>
                        <MIcon className="w-3 h-3" /> {m.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex items-center gap-3 pt-1">
                <button onClick={generate} disabled={loading || !desc.trim()}
                  className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl px-6 py-2.5 text-sm font-medium transition-all flex items-center gap-2 shadow-lg shadow-lumina-500/20">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Code2 className="w-4 h-4" />}
                  {loading ? 'Generating...' : 'Generate'}
                </button>
                {desc && <span className="text-[10px] text-slate-600">{desc.length} chars</span>}
              </div>
            </Card>

            {/* Output */}
            {code && (
              <Card hover={false} className="space-y-4 overflow-hidden">
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <div className="flex items-center gap-2">
                    <LangIcon className={`w-4 h-4 ${langColor}`} />
                    <span className="text-xs font-medium text-slate-300">{lang}</span>
                    {framework && <span className="text-[10px] px-2 py-0.5 rounded-full bg-lumina-600/10 text-lumina-400 border border-lumina-500/20">{framework}</span>}
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                      mode === 'production' ? 'bg-amber-500/10 text-amber-400' :
                      mode === 'explain' ? 'bg-lumina-500/10 text-lumina-400' :
                      'bg-emerald-500/10 text-emerald-400'
                    }`}>{mode}</span>
                    <span className="text-[10px] text-slate-600">{code.length} chars</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {canTest && (
                      <button onClick={testInBrowser}
                        className="flex items-center gap-1.5 text-[10px] text-lumina-400 hover:text-lumina-300 transition-colors bg-lumina-500/10 px-3 py-1.5 rounded-lg">
                        <Play className="w-3 h-3" /> Run
                      </button>
                    )}
                    <button onClick={downloadCode}
                      className="flex items-center gap-1.5 text-[10px] text-slate-400 hover:text-slate-200 transition-colors px-2 py-1.5 rounded-lg hover:bg-white/5">
                      <Download className="w-3 h-3" />
                    </button>
                    <button onClick={copyCode}
                      className="flex items-center gap-1.5 text-[10px] text-slate-400 hover:text-slate-200 transition-colors px-2 py-1.5 rounded-lg hover:bg-white/5">
                      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copied ? 'Copied' : 'Copy'}
                    </button>
                  </div>
                </div>
                <pre className="text-sm text-slate-200 font-mono overflow-x-auto whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">{code}</pre>
              </Card>
            )}

            {explanation && (
              <Card hover={false}>
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-lumina-400" />
                  <span className="text-xs font-medium text-lumina-300">Explanation</span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{explanation}</p>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            <Card hover={false} className="space-y-4 sticky top-4">
              <CardSection label="Generation Modes">
                <div className="space-y-2">
                  {MODES.map(m => {
                    const MIcon = m.icon;
                    return (
                      <div key={m.id} className={`flex items-start gap-2.5 px-3 py-2 rounded-lg border ${
                        mode === m.id ? 'bg-lumina-600/10 border-lumina-500/20' : 'bg-white/[0.02] border-white/5'
                      }`}>
                        <MIcon className={`w-4 h-4 shrink-0 mt-0.5 ${
                          m.id === 'production' ? 'text-amber-400' :
                          m.id === 'explain' ? 'text-lumina-400' : 'text-emerald-400'
                        }`} />
                        <div>
                          <p className="text-xs font-medium text-slate-300">{m.label}</p>
                          <p className="text-[10px] text-slate-500">{m.desc}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardSection>

              <CardSection label="Language Colors">
                <div className="flex flex-wrap gap-1.5">
                  {LANGUAGES.slice(0, 14).map(l => (
                    <span key={l.id}
                      className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500 flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: LANG_COLORS[l.id] || '#666' }} />
                      {l.id}
                    </span>
                  ))}
                </div>
              </CardSection>

              <CardSection label="Tips">
                <ul className="space-y-1.5 text-[10px] text-slate-500">
                  <li className="flex items-start gap-1.5"><ArrowRight className="w-3 h-3 shrink-0 mt-0.5 text-lumina-400" /> Be specific about inputs/outputs</li>
                  <li className="flex items-start gap-1.5"><ArrowRight className="w-3 h-3 shrink-0 mt-0.5 text-lumina-400" /> Mention error handling for production mode</li>
                  <li className="flex items-start gap-1.5"><ArrowRight className="w-3 h-3 shrink-0 mt-0.5 text-lumina-400" /> Use Templates tab for quick starts</li>
                </ul>
              </CardSection>
            </Card>
          </div>
        </div>
      )}

      {/* Templates */}
      {tab === 'templates' && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1 max-w-xs">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input value={templateFilter} onChange={e => setTemplateFilter(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-300 outline-none focus:border-lumina-500/50 placeholder-slate-500"
                placeholder="Filter templates..." />
            </div>
            <div className="flex items-center gap-1">
              {['', 'python', 'javascript', 'typescript', 'html', 'go', 'rust', 'sql'].map(l => (
                <button key={l} onClick={() => setTemplateFilter(l)}
                  className={`text-[10px] px-2 py-1 rounded-lg transition-colors ${
                    templateFilter === l ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'text-slate-500 hover:text-slate-300'
                  }`}>{l || 'All'}</button>
              ))}
            </div>
          </div>

          {templates.length === 0 ? (
            <Card hover={false} className="text-center py-12">
              <BookTemplate className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No templates available</p>
            </Card>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {templates
                .filter(t => !templateFilter || t.lang === templateFilter || t.title.toLowerCase().includes(templateFilter.toLowerCase()))
                .map(t => {
                  const tLang = LANGUAGES.find(l => l.id === t.lang);
                  const TIcon = tLang?.icon || Code2;
                  const tColor = tLang?.color || 'text-slate-400';
                  return (
                    <Card key={t.id} onClick={() => loadTemplate(t)} className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-9 h-9 rounded-lg bg-white/[0.03] border border-white/5 flex items-center justify-center">
                          <TIcon className={`w-4 h-4 ${tColor}`} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-slate-200">{t.title}</p>
                          <p className="text-[10px] text-slate-500 mt-0.5 truncate">{t.desc}</p>
                          <div className="flex items-center gap-1.5 mt-1.5">
                            <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500">{t.lang}</span>
                            {t.framework && <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-lumina-600/10 text-lumina-400">{t.framework}</span>}
                          </div>
                        </div>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0 mt-1" />
                      </div>
                    </Card>
                  );
                })}
            </div>
          )}
        </div>
      )}

      {/* History */}
      {tab === 'history' && (
        <div className="space-y-4">
          {history.length === 0 ? (
            <Card hover={false} className="text-center py-12">
              <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No generation history yet</p>
              <p className="text-xs text-slate-500 mt-1">Generate code to see history here</p>
            </Card>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">{history.length} generations</span>
                <button onClick={loadAll} className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              {history.map(item => {
                const hLang = LANGUAGES.find(l => l.id === item.language);
                const HIcon = hLang?.icon || Code2;
                const hColor = hLang?.color || 'text-slate-400';
                return (
                  <Card key={item.id} onClick={() => loadHistoryItem(item)} className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-lg bg-white/[0.03] border border-white/5 flex items-center justify-center shrink-0">
                          <HIcon className={`w-4 h-4 ${hColor}`} />
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs text-slate-300 truncate max-w-md">{item.description}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-[10px] text-slate-500">{item.language}</span>
                            {item.framework && <span className="text-[10px] text-slate-500">· {item.framework}</span>}
                            <span className="text-[10px] text-slate-500">· {item.code_length} chars</span>
                            <span className={`text-[10px] px-1 py-0.5 rounded-full ${
                              item.mode === 'production' ? 'bg-amber-500/10 text-amber-400' :
                              item.mode === 'explain' ? 'bg-lumina-500/10 text-lumina-400' :
                              'bg-emerald-500/10 text-emerald-400'
                            }`}>{item.mode}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-[10px] text-slate-600">{new Date(item.timestamp).toLocaleTimeString()}</span>
                        <ChevronRight className="w-3 h-3 text-slate-500" />
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
