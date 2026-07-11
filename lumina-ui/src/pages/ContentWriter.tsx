import { useState, useEffect, useCallback } from 'react';
import {
  PenTool, Sparkles, Copy, CheckCircle, Loader2,
  MessageSquare, ShoppingBag, FileText, Mail, Image, HelpCircle,
  Layout, Hash, Smartphone, DollarSign, FileSignature,
  History, BookTemplate, Download, Trash2, ChevronRight,
  Tag, Search,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/writer';

const CONTENT_ICONS: Record<string, typeof PenTool> = {
  blog: FileText, product_description: ShoppingBag, meta_title: Tag,
  meta_description: Hash, faq: HelpCircle, landing_page: Layout,
  email: Mail, social_post: Image, reply: MessageSquare,
  whatsapp: Smartphone, quote: DollarSign, invoice: FileSignature,
};

const TONES = ['professional', 'casual', 'persuasive', 'humorous', 'formal', 'friendly', 'luxury', 'urgent'];
const LANGUAGES = ['English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Dutch', 'Japanese', 'Chinese', 'Korean', 'Arabic', 'Hindi', 'Russian'];
const PLATFORMS = ['Facebook', 'Instagram', 'Twitter', 'LinkedIn', 'TikTok', 'WhatsApp', 'Telegram', 'Email'];

interface ContentType {
  key: string; label: string; icon: string;
}
interface GenerateResult {
  content?: string; error?: string; type?: string; topic?: string; tone?: string;
}

interface HistoryItem {
  content: string; type: string; topic: string; tone: string; timestamp: number;
}

const TEMPLATES = [
  { name: 'Welcome Email', type: 'email', topic: 'Welcome new users to Lumina AI OS', tone: 'friendly' },
  { name: 'Product Launch', type: 'blog', topic: 'Announcing our new AI-powered feature', tone: 'persuasive' },
  { name: 'FAQ for Support', type: 'faq', topic: 'Common questions about Lumina AI subscription plans', tone: 'helpful' },
  { name: 'Landing Page Hero', type: 'landing_page', topic: 'Lumina AI OS - Your Intelligent Operating System', tone: 'professional' },
  { name: 'Social Announcement', type: 'social_post', topic: 'We just launched a major update!', tone: 'casual' },
  { name: 'Sales Email', type: 'email', topic: 'Special offer for premium subscribers', tone: 'persuasive' },
  { name: 'Meta Description', type: 'meta_description', topic: 'Lumina AI OS - AI-powered operating system', tone: 'professional' },
  { name: 'Client Proposal', type: 'quote', topic: 'Website redesign project for Acme Corp', tone: 'professional' },
  { name: 'WhatsApp Broadcast', type: 'whatsapp', topic: 'Flash sale notification for customers', tone: 'urgent' },
  { name: 'Product Description', type: 'product_description', topic: 'Premium noise-canceling wireless headphones', tone: 'luxury' },
];

export default function ContentWriter() {
  const [tab, setTab] = useState('generate');
  const [contentTypes, setContentTypes] = useState<ContentType[]>([]);
  const [selectedType, setSelectedType] = useState('blog');
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('professional');
  const [platform, setPlatform] = useState('Facebook');
  const [language, setLanguage] = useState('English');
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historySearch, setHistorySearch] = useState('');
  const [templateSearch, setTemplateSearch] = useState('');
  const [templateFilter, setTemplateFilter] = useState('all');
  const { addToast } = useToast();

  useEffect(() => {
    fetch(`${BASE}/types`).then(r => r.json()).then(d => {
      setContentTypes(d.types || []);
    }).catch(() => {});
    const saved = localStorage.getItem('lumina_writer_history');
    if (saved) try { setHistory(JSON.parse(saved)); } catch {}
  }, []);

  const saveHistory = useCallback((item: HistoryItem) => {
    setHistory(prev => {
      const next = [item, ...prev].slice(0, 50);
      localStorage.setItem('lumina_writer_history', JSON.stringify(next));
      return next;
    });
  }, []);

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('lumina_writer_history');
  };

  const generate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content_type: selectedType, topic, tone, platform, language, use_vault: false }),
      });
      const data: GenerateResult = await res.json();
      setResult(data);
      if (data.content) {
        saveHistory({ content: data.content, type: selectedType, topic, tone, timestamp: Date.now() });
        addToast('Content generated successfully', 'success');
      }
    } catch (e: any) {
      setResult({ error: e.message });
      addToast(`Error: ${e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const copyContent = async () => {
    if (!result?.content) return;
    await navigator.clipboard.writeText(result.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadContent = () => {
    if (!result?.content) return;
    const filename = `${result.type}_${Date.now()}.md`;
    const blob = new Blob([result.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const applyTemplate = (t: typeof TEMPLATES[0]) => {
    setSelectedType(t.type);
    setTopic(t.topic);
    setTone(t.tone);
    setTab('generate');
    addToast(`Loaded template: ${t.name}`, 'info');
  };

  const restoreHistory = (item: HistoryItem) => {
    setSelectedType(item.type);
    setTopic(item.topic);
    setTone(item.tone);
    setResult({ content: item.content, type: item.type, topic: item.topic, tone: item.tone });
    setTab('generate');
  };

  const chars = result?.content?.length || 0;
  const words = result?.content?.trim().split(/\s+/).length || 0;

  const filteredTemplates = TEMPLATES.filter(t =>
    (templateFilter === 'all' || t.type === templateFilter) &&
    (t.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
     t.topic.toLowerCase().includes(templateSearch.toLowerCase()))
  );

  const filteredHistory = history.filter(h =>
    h.topic.toLowerCase().includes(historySearch.toLowerCase()) ||
    h.type.toLowerCase().includes(historySearch.toLowerCase())
  );

  const uniqueTypes = [...new Set(TEMPLATES.map(t => t.type))];

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        icon={PenTool}
        title="Content Writer"
        description="AI-powered content generation for any format"
      />

      {/* Tab navigation */}
      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['generate', 'templates', 'history'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'generate' ? <Sparkles className="w-3.5 h-3.5" /> : t === 'templates' ? <BookTemplate className="w-3.5 h-3.5" /> : <History className="w-3.5 h-3.5" />}
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto space-y-5">
        {tab === 'generate' && (
          <>
            {/* Content type grid */}
            <CardSection label="Content Type">
              <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
                {contentTypes.map(ct => {
                  const Icon = CONTENT_ICONS[ct.key] || FileText;
                  const isSelected = selectedType === ct.key;
                  return (
                    <button key={ct.key} onClick={() => setSelectedType(ct.key)}
                      className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-xs transition-all ${
                        isSelected
                          ? 'border-lumina-500/40 bg-lumina-500/10 text-lumina-300 shadow-sm'
                          : 'border-white/5 bg-white/[0.03] text-slate-400 hover:border-white/10 hover:text-slate-200'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-center leading-tight">{ct.label}</span>
                    </button>
                  );
                })}
              </div>
            </CardSection>

            {/* Topic */}
            <CardSection label="Topic">
              <input type="text" value={topic} onChange={e => setTopic(e.target.value)}
                placeholder="What do you want to write about?"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 transition-colors"
                onKeyDown={e => e.key === 'Enter' && generate()}
              />
            </CardSection>

            {/* Advanced options */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <CardSection label="Tone">
                <select value={tone} onChange={e => setTone(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-lumina-500/50"
                >
                  {TONES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
                </select>
              </CardSection>
              <CardSection label="Language">
                <select value={language} onChange={e => setLanguage(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-lumina-500/50"
                >
                  {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
                </select>
              </CardSection>
              <CardSection label="Platform">
                <select value={platform} onChange={e => setPlatform(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-lumina-500/50"
                >
                  {PLATFORMS.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </CardSection>
            </div>

            {/* Generate button */}
            <button onClick={generate} disabled={loading || !topic.trim()}
              className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-lumina-500 to-lumina-600 rounded-xl text-sm font-medium text-white disabled:opacity-40 hover:from-lumina-400 hover:to-lumina-500 transition-all shadow-lg shadow-lumina-500/20"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              {loading ? 'Generating...' : 'Generate Content'}
            </button>

            {/* Result */}
            {result && (
              <Card className="!p-0 overflow-hidden">
                {result.error ? (
                  <div className="p-5 text-red-400 text-sm">{result.error}</div>
                ) : result.content ? (
                  <>
                    {/* Result toolbar */}
                    <div className="flex items-center gap-3 px-5 py-3 border-b border-white/5 bg-white/[0.02]">
                      <div className="flex items-center gap-1.5 text-xs text-slate-400">
                        <FileText className="w-3.5 h-3.5" />
                        <span className="font-medium text-slate-300">{contentTypes.find(c => c.key === result.type)?.label || result.type}</span>
                      </div>
                      <div className="flex-1" />
                      <span className="text-[10px] text-slate-500">{chars} chars · {words} words</span>
                      <button onClick={copyContent}
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                      >{copied ? <CheckCircle className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}{copied ? 'Copied' : 'Copy'}</button>
                      <button onClick={downloadContent}
                        className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                      ><Download className="w-3.5 h-3.5" />Download</button>
                    </div>
                    {/* Content */}
                    <div className="p-5">
                      <div className="prose prose-invert prose-sm max-w-none text-slate-300 whitespace-pre-wrap font-mono text-xs leading-relaxed">
                        {result.content}
                      </div>
                    </div>
                  </>
                ) : null}
              </Card>
            )}
          </>
        )}

        {tab === 'templates' && (
          <CardSection label="Quick Templates" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={templateSearch} onChange={e => setTemplateSearch(e.target.value)}
                  placeholder="Search templates..." className="bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-44"
                />
              </div>
              <select value={templateFilter} onChange={e => setTemplateFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="all">All Types</option>
                {uniqueTypes.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
          }>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredTemplates.map((t, i) => {
                const Icon = CONTENT_ICONS[t.type] || FileText;
                return (
                  <button key={i} onClick={() => applyTemplate(t)}
                    className="flex items-start gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10 transition-all text-left group"
                  >
                    <div className="w-9 h-9 rounded-lg bg-lumina-500/10 flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4 text-lumina-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{t.name}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5 truncate">{t.type.replace(/_/g, ' ')} · {t.tone}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-colors mt-1 shrink-0" />
                  </button>
                );
              })}
            </div>
            {filteredTemplates.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-8">No templates matching your search</p>
            )}
          </CardSection>
        )}

        {tab === 'history' && (
          <CardSection label="Generation History" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={historySearch} onChange={e => setHistorySearch(e.target.value)}
                  placeholder="Search history..." className="bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-44"
                />
              </div>
              {history.length > 0 && (
                <button onClick={clearHistory}
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 transition-colors"
                ><Trash2 className="w-3.5 h-3.5" />Clear</button>
              )}
            </div>
          }>
            {history.length === 0 ? (
              <div className="text-center py-12">
                <History className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No generation history yet</p>
                <p className="text-xs text-slate-600 mt-1">Content you generate will appear here</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredHistory.map((item, i) => {
                  const Icon = CONTENT_ICONS[item.type] || FileText;
                  return (
                    <button key={i} onClick={() => restoreHistory(item)}
                      className="w-full flex items-start gap-3 p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10 transition-all text-left group"
                    >
                      <div className="w-9 h-9 rounded-lg bg-lumina-500/10 flex items-center justify-center shrink-0">
                        <Icon className="w-4 h-4 text-lumina-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-white truncate">{item.topic}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-slate-400">{item.type.replace(/_/g, ' ')}</span>
                          <span className="text-[10px] text-slate-600">{new Date(item.timestamp).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-colors mt-1 shrink-0" />
                    </button>
                  );
                })}
              </div>
            )}
          </CardSection>
        )}
      </div>
    </div>
  );
}
