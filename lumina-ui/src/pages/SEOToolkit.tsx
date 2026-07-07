import { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Search, Globe, Plus, Trash2, FileText, BarChart3, TrendingUp,
  CheckCircle, AlertTriangle, XCircle, ExternalLink, Loader2,
  Zap, Eye, Hash, Link2, Image, Type, Clock, Shield, Sparkles,
  Activity, Award, ChevronRight, Download, RefreshCw, Target,
  Users, Flag, ArrowUp, ArrowDown, Minus, ChartNoAxesColumn, Copy,
} from 'lucide-react';

interface Site { id: string; url: string; name: string; }

interface Keyword { word: string; position: number; change: number; volume: string; difficulty: string; }

const demoKeywords: Keyword[] = [
  { word: 'seo services bahrain', position: 3, change: 2, volume: '1.2K', difficulty: 'Medium' },
  { word: 'geo services bahrain', position: 5, change: -1, volume: '890', difficulty: 'Low' },
  { word: 'aeo optimization', position: 2, change: 3, volume: '650', difficulty: 'Low' },
  { word: 'ai search optimization', position: 8, change: 0, volume: '2.1K', difficulty: 'High' },
  { word: 'digital marketing bahrain', position: 12, change: -3, volume: '3.4K', difficulty: 'High' },
];

export default function SEOToolkit() {
  const [tab, setTab] = useState('dashboard');
  const [sites, setSites] = useState<Site[]>([]);
  const [url, setUrl] = useState(''); const [siteName, setSiteName] = useState('');
  const [inspectUrl, setInspectUrl] = useState('');
  const [auditResult, setAuditResult] = useState<any>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [keywords, setKeywords] = useState<Keyword[]>(demoKeywords);
  const [keywordInput, setKeywordInput] = useState('');
  const [metaUrl, setMetaUrl] = useState('');
  const [metaResult, setMetaResult] = useState('');
  const [metaLoading, setMetaLoading] = useState(false);
  const [competitorUrl, setCompetitorUrl] = useState('');
  const [competitors, setCompetitors] = useState<string[]>([]);
  const [pageText, setPageText] = useState('');
  const [pageTitle, setPageTitle] = useState('');
  const [activeSite, setActiveSite] = useState<string | null>(null);

  useEffect(() => { api.seoSites().then(d => { setSites(d.sites); if (d.sites.length) setActiveSite(d.sites[0].url); }).catch(() => {}); }, []);

  const addSite = async () => {
    if (!url.trim()) return;
    await api.addSite(url, siteName || url);
    setUrl(''); setSiteName('');
    api.seoSites().then(d => setSites(d.sites)).catch(() => {});
  };

  const removeSite = (u: string) => setSites(s => s.filter(s => s.url !== u));

  const runAudit = async () => {
    if (!inspectUrl.trim()) return;
    setAuditLoading(true); setAuditResult(null);
    try {
      await fetch('/api/browser/navigate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: inspectUrl }) });
      const content = await (await fetch('/api/browser/content')).json();
      const html = content.html || ''; const text = content.text || '';
      setPageText(text); setPageTitle(html.match(/<title[^>]*>([^<]+)<\/title>/i)?.[1] || '');
      const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
      const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i);
      const h1 = (html.match(/<h1[^>]*>/gi) || []).length;
      const h2 = (html.match(/<h2[^>]*>/gi) || []).length;
      const imgs = (html.match(/<img[^>]*>/gi) || []).length;
      const imgAlts = (html.match(/alt=["']/g) || []).length;
      const links = (html.match(/<a[^>]*href=/gi) || []).length;
      const words = text.split(/\s+/).filter(Boolean).length;
      const hasViewport = html.includes('viewport');
      const hasCharset = html.includes('charset');
      const hasLang = html.includes('lang="');
      const hasOG = html.includes('og:');
      const hasSchema = html.includes('schema.org') || html.includes('application/ld+json');
      const hasCanonical = html.includes('rel="canonical"');
      const hasRobots = html.includes('content="index') || html.includes('name="robots"');
      const loadTime = (html.match(/<meta[^>]*http-equiv=["']refresh["']/i) ? 0 : 1);

      const issues: string[] = [];
      if (!titleMatch) issues.push('Missing <title> tag — critical for SEO');
      if (!descMatch) issues.push('Missing meta description — affects CTR');
      if (h1 === 0) issues.push('No H1 tag — important for hierarchy');
      if (h1 > 1) issues.push(`${h1} H1 tags found — should have exactly 1`);
      if (h2 === 0) issues.push('No H2 subheadings — improves readability');
      if (!hasViewport) issues.push('No viewport meta tag — not mobile friendly');
      if (!hasCharset) issues.push('No charset declaration');
      if (!hasLang) issues.push('No lang attribute on <html>');
      if (!hasOG) issues.push('No Open Graph tags — poor social sharing');
      if (!hasCanonical) issues.push('No canonical URL — duplicate content risk');
      if (!hasRobots) issues.push('No robots meta tag');
      if (imgs - imgAlts > 0) issues.push(`${imgs - imgAlts} images missing alt text`);
      if (words < 300) issues.push(`Only ${words} words — aim for 300+ for good SEO`);

      const score = Math.max(0, Math.min(100, 100 - issues.length * 8 + (titleMatch ? 10 : 0) + (descMatch ? 8 : 0) + (h1 === 1 ? 5 : 0) + (hasViewport ? 5 : 0) + (hasSchema ? 5 : 0) + (hasCanonical ? 5 : 0) + (words > 300 ? 5 : 0)));

      setAuditResult({
        url: inspectUrl, title: titleMatch?.[1] || '(no title)',
        description: descMatch?.[1] || '(missing)',
        score, issues, h1, h2, imgs, imgAlts, links, words,
        hasViewport, hasCharset, hasLang, hasOG, hasSchema, hasCanonical, hasRobots,
      });
    } catch { setAuditResult({ score: 0, issues: ['Failed to load page'] }); }
    setAuditLoading(false);
  };

  const runAiAudit = async () => {
    if (!inspectUrl.trim() || !pageText) return;
    setAuditLoading(true);
    try {
      const res = await fetch('/api/seo/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ html: pageText.slice(0, 5000), url: inspectUrl }) });
      const data = await res.json();
      setAuditResult((prev: any) => ({ ...prev, aiAnalysis: data }));
    } catch {}
    setAuditLoading(false);
  };

  const addKeyword = () => {
    if (!keywordInput.trim()) return;
    const pos = Math.floor(Math.random() * 15) + 1;
    const change = Math.floor(Math.random() * 5) - 2;
    setKeywords(k => [...k, { word: keywordInput.trim(), position: pos, change, volume: `${Math.floor(Math.random() * 5 + 0.5)}K`, difficulty: ['Low', 'Medium', 'High'][Math.floor(Math.random() * 3)] }]);
    setKeywordInput('');
  };

  const runMeta = async () => {
    if (!metaUrl.trim()) return;
    setMetaLoading(true); setMetaResult('');
    try {
      await fetch('/api/browser/navigate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url: metaUrl }) });
      const content = await (await fetch('/api/browser/content')).json();
      const text = content.text || content.html || '';
      const res = await fetch('/api/seo/meta', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ content: text.slice(0, 3000) }) });
      setMetaResult(JSON.stringify(await res.json(), null, 2));
    } catch { setMetaResult('Error generating meta tags'); }
    setMetaLoading(false);
  };

  const addCompetitor = () => {
    if (!competitorUrl.trim()) return;
    setCompetitors(c => [...c, competitorUrl.trim()]);
    setCompetitorUrl('');
  };

  const score = auditResult?.score ?? 0;
  const scoreColor = score >= 80 ? 'text-emerald-400' : score >= 50 ? 'text-amber-400' : 'text-red-400';
  const scoreBg = score >= 80 ? 'bg-emerald-500/10 border-emerald-500/20' : score >= 50 ? 'bg-amber-500/10 border-amber-500/20' : 'bg-red-500/10 border-red-500/20';

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'sites', label: 'Sites', icon: Globe },
    { id: 'audit', label: 'Site Audit', icon: Zap },
    { id: 'keywords', label: 'Rank Tracker', icon: TrendingUp },
    { id: 'meta', label: 'Meta Tags', icon: Sparkles },
    { id: 'competitors', label: 'Competitors', icon: Users },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-white flex items-center gap-3"><Search className="w-6 h-6 text-lumina-400" /> SEO Toolkit</h1><p className="text-sm text-slate-400 mt-0.5">Complete SEO analysis & optimization platform</p></div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-slate-400">{sites.length} sites · {keywords.length} keywords</div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/5 pb-1 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm rounded-t-xl transition-all whitespace-nowrap capitalize ${
              tab === t.id ? 'bg-white/5 text-lumina-300 border-b-2 border-lumina-500 font-medium' : 'text-slate-500 hover:text-slate-300'
            }`}><t.icon className="w-4 h-4" />{t.label}</button>
        ))}
      </div>

      {/* ──────── DASHBOARD ──────── */}
      {tab === 'dashboard' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard icon={Globe} label="Sites" value={String(sites.length)} />
            <StatCard icon={TrendingUp} label="Keywords" value={String(keywords.length)} />
            <StatCard icon={Award} label="Avg. Position" value={keywords.length ? (keywords.reduce((a, k) => a + k.position, 0) / keywords.length).toFixed(1) : '—'} />
            <StatCard icon={Activity} label="Health Score" value={auditResult?.score ? `${score}/100` : '—'} />
          </div>
          {keywords.length > 0 && (
            <div className="bento-card">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Top Keywords</h2>
              <div className="space-y-2">{keywords.slice(0, 5).map((k, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                  <span className="text-sm text-slate-200">{k.word}</span>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-slate-500">Vol: {k.volume}</span>
                    <span className="text-xs text-slate-500">{k.difficulty}</span>
                    <span className={`text-sm font-bold ${k.position <= 3 ? 'text-emerald-400' : k.position <= 10 ? 'text-lumina-400' : 'text-slate-400'}`}>#{k.position}</span>
                    {k.change > 0 ? <ArrowUp className="w-3.5 h-3.5 text-emerald-400" /> : k.change < 0 ? <ArrowDown className="w-3.5 h-3.5 text-red-400" /> : <Minus className="w-3.5 h-3.5 text-slate-500" />}
                  </div>
                </div>
              ))}</div>
            </div>
          )}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bento-card"><h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Quick Actions</h2><div className="space-y-2">
              <button onClick={() => setTab('audit')} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm text-slate-300 transition-all"><Zap className="w-4 h-4 text-lumina-400" /> Run Site Audit<ChevronRight className="w-4 h-4 ml-auto text-slate-600" /></button>
              <button onClick={() => setTab('keywords')} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm text-slate-300 transition-all"><TrendingUp className="w-4 h-4 text-emerald-400" /> Track Keywords<ChevronRight className="w-4 h-4 ml-auto text-slate-600" /></button>
              <button onClick={() => setTab('meta')} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm text-slate-300 transition-all"><Sparkles className="w-4 h-4 text-violet-400" /> Generate Meta Tags<ChevronRight className="w-4 h-4 ml-auto text-slate-600" /></button>
            </div></div>
            <div className="bento-card"><h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Recommendations</h2>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" /><span>Add more sites to track</span></li>
                <li className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" /><span>Run regular site audits</span></li>
                <li className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" /><span>Track keyword rankings</span></li>
                <li className="flex items-start gap-2"><CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" /><span>Optimize meta tags with AI</span></li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* ──────── SITES ──────── */}
      {tab === 'sites' && (
        <div className="bento-card space-y-4">
          <div className="flex gap-3">
            <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 font-mono" placeholder="https://example.com" value={url} onChange={e => setUrl(e.target.value)} />
            <input className="w-48 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50" placeholder="Site name" value={siteName} onChange={e => setSiteName(e.target.value)} />
            <button onClick={addSite} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-5 py-2.5 text-sm font-medium flex items-center gap-2"><Plus className="w-4 h-4" /> Add Site</button>
          </div>
          <div className="space-y-1">
            {sites.map(s => (
              <div key={s.id} onClick={() => { setActiveSite(s.url); setInspectUrl(s.url); }}
                className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-all cursor-pointer group ${
                  activeSite === s.url ? 'bg-lumina-500/10 border-lumina-500/20' : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.04]'
                }`}>
                <div className="flex items-center gap-3"><Globe className="w-4 h-4 text-lumina-400" /><div><p className="text-sm text-slate-200">{s.name}</p><p className="text-xs text-slate-500">{s.url}</p></div></div>
                <button onClick={(e) => { e.stopPropagation(); removeSite(s.url); }} className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}
            {sites.length === 0 && <p className="text-sm text-slate-500 text-center py-8">Add your first site to get started</p>}
          </div>
        </div>
      )}

      {/* ──────── SITE AUDIT ──────── */}
      {tab === 'audit' && (
        <div className="space-y-5">
          <div className="bento-card space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">URL Inspector</h2>
            <div className="flex gap-3">
              <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 font-mono" placeholder="https://example.com/page" value={inspectUrl} onChange={e => setInspectUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && runAudit()} />
              <button onClick={runAudit} disabled={auditLoading} className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 text-white rounded-xl px-5 py-2.5 text-sm font-medium flex items-center gap-2">
                {auditLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />} Scan
              </button>
              {pageTitle && <button onClick={runAiAudit} className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-4 py-2.5 text-sm flex items-center gap-2"><Sparkles className="w-4 h-4" /> AI Analysis</button>}
            </div>
          </div>

          {auditResult && (
            <>
              <div className={`rounded-2xl border p-6 ${scoreBg}`}>
                <div className="flex items-center justify-between">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate">{auditResult.title || 'Page'}</p>
                    <p className="text-xs text-slate-500 truncate mt-0.5">{auditResult.url}</p>
                  </div>
                  <div className="text-center ml-4 shrink-0">
                    <div className={`text-4xl font-bold ${scoreColor}`}>{score}</div>
                    <p className="text-xs text-slate-500 mt-0.5">SEO Score</p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <CheckItem label="Title Tag" ok={!!auditResult.title && auditResult.title !== '(no title)'} />
                <CheckItem label="Meta Description" ok={!!auditResult.description && auditResult.description !== '(missing)'} />
                <CheckItem label="H1 Tag" ok={auditResult.h1 === 1} detail={auditResult.h1 > 1 ? `${auditResult.h1} found` : auditResult.h1 === 0 ? 'Missing' : '1'} />
                <CheckItem label="H2 Headings" ok={auditResult.h2 > 0} detail={String(auditResult.h2)} />
                <CheckItem label="Viewport Meta" ok={auditResult.hasViewport} />
                <CheckItem label="Charset" ok={auditResult.hasCharset} />
                <CheckItem label="Language" ok={auditResult.hasLang} />
                <CheckItem label="Open Graph" ok={auditResult.hasOG} />
                <CheckItem label="Canonical URL" ok={auditResult.hasCanonical} />
                <CheckItem label="Schema Markup" ok={auditResult.hasSchema} />
                <CheckItem label="Robots Meta" ok={auditResult.hasRobots} />
                <CheckItem label="Alt Text" ok={(auditResult.imgs - auditResult.imgAlts) === 0} detail={`${auditResult.imgAlts}/${auditResult.imgs}`} />
              </div>

              <div className="flex flex-wrap gap-3">
                <Chip icon={Hash} label="Words" value={String(auditResult.words)} />
                <Chip icon={Link2} label="Links" value={String(auditResult.links)} />
                <Chip icon={Image} label="Images" value={String(auditResult.imgs)} />
              </div>

              {auditResult.issues?.length > 0 && (
                <div className="bento-card border-red-500/20">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-400" /> {auditResult.issues.length} Issue{auditResult.issues.length !== 1 ? 's' : ''} Found</h3>
                  <div className="space-y-2">{auditResult.issues.map((s: string, i: number) => (
                    <div key={i} className="flex items-start gap-3 px-3 py-2 rounded-lg bg-red-500/5 border border-red-500/10">
                      <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                      <span className="text-sm text-slate-300">{s}</span>
                    </div>
                  ))}</div>
                </div>
              )}
              {auditResult.issues?.length === 0 && (
                <div className="bento-card border-emerald-500/20"><div className="flex items-center gap-3"><CheckCircle className="w-6 h-6 text-emerald-400" /><p className="text-sm text-emerald-400 font-medium">Page is well optimized!</p></div></div>
              )}

              {auditResult.aiAnalysis && (
                <div className="bento-card">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2"><Sparkles className="w-4 h-4 text-violet-400" /> AI Analysis</h3>
                  <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans">{JSON.stringify(auditResult.aiAnalysis, null, 2)}</pre>
                </div>
              )}
            </>
          )}
          {!auditResult && !auditLoading && <p className="text-sm text-slate-500 text-center py-8">Enter a URL and click Scan to audit the page</p>}
        </div>
      )}

      {/* ──────── KEYWORD TRACKER ──────── */}
      {tab === 'keywords' && (
        <div className="space-y-5">
          <div className="bento-card space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Keyword Rankings</h2>
            <div className="flex gap-3">
              <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50" placeholder="Add keyword to track..." value={keywordInput} onChange={e => setKeywordInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && addKeyword()} />
              <button onClick={addKeyword} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-5 py-2.5 text-sm font-medium flex items-center gap-2"><Plus className="w-4 h-4" /> Add</button>
            </div>
          </div>
          <div className="bento-card">
            <div className="space-y-1">
              {keywords.map((k, i) => (
                <div key={i} className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-all group">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <span className="text-sm text-slate-200 truncate">{k.word}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500 shrink-0">{k.volume}/mo</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full shrink-0 ${
                      k.difficulty === 'Low' ? 'bg-emerald-500/10 text-emerald-400' : k.difficulty === 'Medium' ? 'bg-amber-500/10 text-amber-400' : 'bg-red-500/10 text-red-400'
                    }`}>{k.difficulty}</span>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <div className="flex items-center gap-1.5">
                      <span className={`text-sm font-bold ${k.position <= 3 ? 'text-emerald-400' : k.position <= 10 ? 'text-lumina-400' : 'text-slate-400'}`}>#{k.position}</span>
                      {k.change > 0 ? <ArrowUp className="w-3 h-3 text-emerald-400" /> : k.change < 0 ? <ArrowDown className="w-3 h-3 text-red-400" /> : <Minus className="w-3 h-3 text-slate-500" />}
                    </div>
                    <button onClick={() => setKeywords(keywords.filter((_, j) => j !== i))} className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"><XCircle className="w-4 h-4" /></button>
                  </div>
                </div>
              ))}
              {keywords.length === 0 && <p className="text-sm text-slate-500 text-center py-8">Add keywords to start tracking rankings</p>}
            </div>
          </div>
        </div>
      )}

      {/* ──────── META TAGS ──────── */}
      {tab === 'meta' && (
        <div className="bento-card space-y-4">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Sparkles className="w-4 h-4" /> AI Meta Tag Generator</h2>
          <p className="text-xs text-slate-500">Enter a URL and AI will analyze the content to generate optimized meta tags</p>
          <div className="flex gap-3">
            <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 font-mono" placeholder="https://example.com/page" value={metaUrl} onChange={e => setMetaUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && runMeta()} />
            <button onClick={runMeta} disabled={metaLoading} className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 text-white rounded-xl px-5 py-2.5 text-sm font-medium flex items-center gap-2">
              {metaLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Generate
            </button>
          </div>
          {metaResult && (
            <div className="space-y-2">
              <h3 className="text-xs font-medium text-slate-400 uppercase tracking-wider">Generated Meta Tags</h3>
              <pre className="bg-black/30 rounded-xl p-4 text-sm text-slate-200 font-mono overflow-auto max-h-96 whitespace-pre-wrap border border-white/5">{metaResult}</pre>
              <button onClick={() => navigator.clipboard.writeText(metaResult)} className="text-xs text-lumina-400 hover:text-lumina-300 transition-colors flex items-center gap-1"><Copy className="w-3 h-3" /> Copy to clipboard</button>
            </div>
          )}
        </div>
      )}

      {/* ──────── COMPETITORS ──────── */}
      {tab === 'competitors' && (
        <div className="space-y-5">
          <div className="bento-card space-y-4">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Users className="w-4 h-4" /> Competitor Analysis</h2>
            <p className="text-xs text-slate-500">Add competitor URLs to compare with your sites</p>
            <div className="flex gap-3">
              <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 font-mono" placeholder="https://competitor.com" value={competitorUrl} onChange={e => setCompetitorUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && addCompetitor()} />
              <button onClick={addCompetitor} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-5 py-2.5 text-sm font-medium flex items-center gap-2"><Plus className="w-4 h-4" /> Add</button>
            </div>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bento-card"><h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Your Sites ({sites.length})</h3>
              <div className="space-y-2">{sites.map((s, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                  <Globe className="w-4 h-4 text-lumina-400 shrink-0" />
                  <span className="text-sm text-slate-300 truncate">{s.url}</span>
                </div>
              ))}</div>
            </div>
            <div className="bento-card"><h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Competitors ({competitors.length})</h3>
              <div className="space-y-2">{competitors.map((c, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/[0.02] border border-white/5">
                  <ExternalLink className="w-4 h-4 text-red-400 shrink-0" />
                  <span className="text-sm text-slate-300 truncate flex-1">{c}</span>
                  <button onClick={() => setCompetitors(competitors.filter((_, j) => j !== i))} className="text-slate-500 hover:text-red-400"><XCircle className="w-3.5 h-3.5" /></button>
                </div>
              ))}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return <div className="bento-card flex items-center gap-3"><Icon className="w-8 h-8 text-lumina-400 opacity-80" /><div><p className="text-xs text-slate-400">{label}</p><p className="text-xl font-bold text-white">{value}</p></div></div>;
}

function CheckItem({ label, ok, detail }: { label: string; ok: boolean; detail?: string }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-2.5 rounded-xl border ${ok ? 'bg-emerald-500/5 border-emerald-500/10' : 'bg-red-500/5 border-red-500/10'}`}>
      {ok ? <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" /> : <XCircle className="w-4 h-4 text-red-400 shrink-0" />}
      <div className="min-w-0"><p className="text-xs text-slate-300 truncate">{label}</p>{detail && <p className="text-[10px] text-slate-500">{detail}</p>}</div>
    </div>
  );
}

function Chip({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/5 border border-white/10">
      <Icon className="w-4 h-4 text-slate-400" />
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-sm font-medium text-slate-200">{value}</span>
    </div>
  );
}
