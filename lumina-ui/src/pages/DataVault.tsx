import { useState, useEffect, useCallback } from 'react';
import {
  Shield, Plus, Trash2, Copy, CheckCircle, Search, Edit3,
  Save, User, Briefcase, Building2, Hash, Globe, Mail, Phone,
  MapPin, Link, FileText, Star, RefreshCw, AlertCircle,
  Brain, Key, Lock, Eye, EyeOff, X, ChevronRight,
  Download, Upload, Sparkles, CheckSquare, Box,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/vault';

interface VaultEntry {
  key: string; value: string; label?: string; section?: string;
}

interface ProfileData {
  name?: string; email?: string; phone?: string; company?: string;
  role?: string; website?: string; location?: string; industry?: string;
}

const SECTIONS = [
  { key: 'personal', label: 'Personal', icon: User, color: 'text-blue-400' },
  { key: 'business', label: 'Business', icon: Briefcase, color: 'text-emerald-400' },
  { key: 'brand', label: 'Brand', icon: Building2, color: 'text-amber-400' },
  { key: 'social', label: 'Social Media', icon: Globe, color: 'text-violet-400' },
];

const DEFAULT_FIELDS = [
  { key: 'full_name', label: 'Full Name', section: 'personal', icon: User },
  { key: 'email', label: 'Email', section: 'personal', icon: Mail },
  { key: 'phone', label: 'Phone', section: 'personal', icon: Phone },
  { key: 'location', label: 'Location', section: 'personal', icon: MapPin },
  { key: 'company_name', label: 'Company Name', section: 'business', icon: Briefcase },
  { key: 'role', label: 'Role/Position', section: 'business', icon: Briefcase },
  { key: 'website', label: 'Website', section: 'business', icon: Globe },
  { key: 'industry', label: 'Industry', section: 'business', icon: Building2 },
  { key: 'brand_name', label: 'Brand Name', section: 'brand', icon: Building2 },
  { key: 'brand_voice', label: 'Brand Voice', section: 'brand', icon: FileText },
  { key: 'target_audience', label: 'Target Audience', section: 'brand', icon: Star },
  { key: 'unique_value', label: 'Unique Value Proposition', section: 'brand', icon: Sparkles },
  { key: 'instagram', label: 'Instagram Handle', section: 'social', icon: Globe },
  { key: 'twitter', label: 'Twitter/X Handle', section: 'social', icon: Globe },
  { key: 'linkedin', label: 'LinkedIn URL', section: 'social', icon: Link },
  { key: 'facebook', label: 'Facebook Page', section: 'social', icon: Globe },
];

export default function DataVault() {
  const [tab, setTab] = useState('vault');
  const [entries, setEntries] = useState<VaultEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sectionFilter, setSectionFilter] = useState('all');
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [addKey, setAddKey] = useState('');
  const [addValue, setAddValue] = useState('');
  const [addSection, setAddSection] = useState('personal');
  const [showAdd, setShowAdd] = useState(false);
  const [profile, setProfile] = useState<ProfileData>({});
  const [contextPrompt, setContextPrompt] = useState('');
  const [copied, setCopied] = useState(false);
  const [showValues, setShowValues] = useState(false);
  const { addToast } = useToast();

  useEffect(() => {
    loadEntries();
    loadProfile();
  }, []);

  const loadEntries = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/`);
      const data = await res.json();
      setEntries(data.entries || data.vault || []);
    } catch {} finally { setLoading(false); }
  };

  const loadProfile = async () => {
    try {
      const res = await fetch(`${BASE}/profile`);
      const data = await res.json();
      setProfile(data.profile || data || {});
    } catch {}
  };

  const loadContext = async () => {
    try {
      const res = await fetch(`${BASE}/prompt`);
      const data = await res.json();
      setContextPrompt(data.prompt || data.context || '');
      setTab('context');
    } catch {}
  };

  const saveEntry = async (key: string, value: string) => {
    try {
      await fetch(`${BASE}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value }),
      });
      addToast('Entry saved', 'success');
      setEditingKey(null);
      loadEntries();
    } catch (e: any) {
      addToast(`Failed: ${e.message}`, 'error');
    }
  };

  const deleteEntry = async (key: string) => {
    try {
      await fetch(`${BASE}/${encodeURIComponent(key)}`, { method: 'DELETE' });
      addToast('Entry deleted', 'success');
      loadEntries();
    } catch (e: any) {
      addToast(`Failed: ${e.message}`, 'error');
    }
  };

  const saveProfile = async () => {
    try {
      await fetch(`${BASE}/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile }),
      });
      addToast('Profile saved', 'success');
    } catch (e: any) {
      addToast(`Failed: ${e.message}`, 'error');
    }
  };

  const addCustomEntry = async () => {
    if (!addKey.trim() || !addValue.trim()) return;
    await saveEntry(addKey.trim(), addValue.trim());
    setAddKey('');
    setAddValue('');
    setShowAdd(false);
  };

  const copyAll = async () => {
    const text = entries.map(e => `${e.key}: ${e.value}`).join('\n');
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    addToast('Copied to clipboard', 'success');
  };

  const filteredEntries = entries.filter(e =>
    (sectionFilter === 'all' || e.section === sectionFilter) &&
    (e.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
     (e.value || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
     (e.label || '').toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getFieldIcon = (key: string) => {
    const f = DEFAULT_FIELDS.find(df => df.key === key);
    return f?.icon || Key;
  };

  const getSectionColor = (section?: string) => {
    const s = SECTIONS.find(s => s.key === section);
    return s?.color || 'text-slate-400';
  };

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Shield} title="Data Vault" description="Store personal, business, brand & social info for AI agents" />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['vault', 'profile', 'context'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'vault' ? <Shield className="w-3.5 h-3.5" /> : t === 'profile' ? <User className="w-3.5 h-3.5" /> : <Brain className="w-3.5 h-3.5" />}
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {tab === 'vault' && (
          <CardSection label="Vault Entries" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Search..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-32"
                />
              </div>
              <select value={sectionFilter} onChange={e => setSectionFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
              >
                <option value="all">All Sections</option>
                {SECTIONS.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
              <button onClick={() => setShowValues(!showValues)}
                className={`p-1.5 rounded-lg transition-colors ${showValues ? 'bg-lumina-500/20 text-lumina-300' : 'text-slate-500 hover:text-white'}`}
              >{showValues ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}</button>
              <button onClick={copyAll}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs text-slate-300 hover:bg-white/5 transition-colors"
              >{copied ? <CheckCircle className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}{copied ? 'Copied' : 'Copy All'}</button>
              <button onClick={() => setShowAdd(!showAdd)}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
              ><Plus className="w-3.5 h-3.5" />Add</button>
            </div>
          }>
            {/* Add form */}
            {showAdd && (
              <div className="flex items-start gap-2 p-3 mb-3 rounded-xl border border-lumina-500/20 bg-lumina-500/5">
                <div className="flex-1 space-y-2">
                  <div className="flex gap-2">
                    <input type="text" value={addKey} onChange={e => setAddKey(e.target.value)}
                      placeholder="Key (e.g. tax_id)" className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                    />
                    <select value={addSection} onChange={e => setAddSection(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white focus:outline-none w-28"
                    >{SECTIONS.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}</select>
                  </div>
                  <input type="text" value={addValue} onChange={e => setAddValue(e.target.value)}
                    placeholder="Value" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                  />
                </div>
                <div className="flex gap-1">
                  <button onClick={addCustomEntry}
                    className="px-3 py-2 rounded-lg text-xs bg-lumina-500/20 text-lumina-300 hover:bg-lumina-500/30"
                  >Save</button>
                  <button onClick={() => setShowAdd(false)} className="p-2 text-slate-500 hover:text-white"><X className="w-3.5 h-3.5" /></button>
                </div>
              </div>
            )}

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-5 h-5 text-lumina-400 animate-spin" />
              </div>
            ) : filteredEntries.length === 0 ? (
              <div className="text-center py-12">
                <Shield className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-500">No vault entries found</p>
                <p className="text-xs text-slate-600 mt-1">Add your personal, business, brand, and social information</p>
              </div>
            ) : (
              <div className="space-y-1 divide-y divide-white/[0.03]">
                {filteredEntries.map(entry => {
                  const Icon = getFieldIcon(entry.key);
                  const sc = getSectionColor(entry.section);
                  const isEditing = editingKey === entry.key;
                  const fieldDef = DEFAULT_FIELDS.find(f => f.key === entry.key);
                  return (
                    <div key={entry.key}
                      className="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/[0.02] transition-colors group"
                    >
                      <Icon className={`w-4 h-4 shrink-0 ${sc}`} />
                      {isEditing ? (
                        <div className="flex-1 flex items-center gap-2">
                          <input type="text" value={editValue} onChange={e => setEditValue(e.target.value)}
                            className="flex-1 bg-white/10 border border-lumina-500/50 rounded px-2 py-1 text-xs text-white focus:outline-none"
                            onKeyDown={e => { if (e.key === 'Enter') saveEntry(entry.key, editValue); if (e.key === 'Escape') setEditingKey(null); }}
                            autoFocus
                          />
                          <button onClick={() => saveEntry(entry.key, editValue)}
                            className="p-1 text-lumina-400 hover:text-lumina-300"
                          ><Save className="w-3.5 h-3.5" /></button>
                        </div>
                      ) : (
                        <>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-slate-300">{fieldDef?.label || entry.key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                            <p className="text-[10px] text-slate-500 truncate">{showValues ? entry.value : '••••••••'}</p>
                          </div>
                          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => { setEditingKey(entry.key); setEditValue(entry.value || ''); }}
                              className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white"
                            ><Edit3 className="w-3.5 h-3.5" /></button>
                            <button onClick={() => deleteEntry(entry.key)}
                              className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400"
                            ><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardSection>
        )}

        {tab === 'profile' && (
          <div className="max-w-2xl">
            <CardSection label="Profile Information" action={
              <button onClick={saveProfile}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
              ><Save className="w-3.5 h-3.5" />Save Profile</button>
            }>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  { key: 'name', label: 'Full Name', icon: User },
                  { key: 'email', label: 'Email', icon: Mail },
                  { key: 'phone', label: 'Phone', icon: Phone },
                  { key: 'company', label: 'Company', icon: Building2 },
                  { key: 'role', label: 'Role', icon: Briefcase },
                  { key: 'website', label: 'Website', icon: Globe },
                  { key: 'location', label: 'Location', icon: MapPin },
                  { key: 'industry', label: 'Industry', icon: Hash },
                ].map(field => (
                  <div key={field.key}>
                    <label className="text-[10px] text-slate-500 uppercase tracking-wider flex items-center gap-1 mb-1">
                      <field.icon className="w-3 h-3" />{field.label}
                    </label>
                    <input type="text" value={(profile as any)[field.key] || ''}
                      onChange={e => setProfile({ ...profile, [field.key]: e.target.value })}
                      placeholder={field.label}
                      className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 transition-colors"
                    />
                  </div>
                ))}
              </div>
            </CardSection>
          </div>
        )}

        {tab === 'context' && (
          <div className="max-w-3xl">
            <CardSection label="AI Context Prompt" action={
              <div className="flex items-center gap-2">
                <button onClick={loadContext}
                  className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-slate-300 hover:bg-white/5 transition-colors"
                ><RefreshCw className="w-3.5 h-3.5" />Refresh</button>
              </div>
            }>
              {!contextPrompt ? (
                <div className="text-center py-12">
                  <Brain className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                  <p className="text-sm text-slate-500">No context prompt generated yet</p>
                  <button onClick={loadContext}
                    className="mt-3 flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 mx-auto transition-colors"
                  ><Brain className="w-3.5 h-3.5" />Generate Context</button>
                </div>
              ) : (
                <div>
                  <div className="p-4 rounded-xl bg-white/[0.03] border border-white/5 font-mono text-xs text-slate-300 whitespace-pre-wrap max-h-96 overflow-y-auto leading-relaxed">
                    {contextPrompt}
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <button onClick={async () => {
                      await navigator.clipboard.writeText(contextPrompt);
                      setCopied(true); setTimeout(() => setCopied(false), 2000);
                      addToast('Copied to clipboard', 'success');
                    }}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
                    ><Copy className="w-3.5 h-3.5" />{copied ? 'Copied!' : 'Copy to Clipboard'}</button>
                    <button onClick={() => {
                      const blob = new Blob([contextPrompt], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a'); a.href = url; a.download = 'ai-context.txt'; a.click();
                      URL.revokeObjectURL(url);
                    }}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs text-slate-300 hover:bg-white/5 transition-colors"
                    ><Download className="w-3.5 h-3.5" />Download</button>
                  </div>
                </div>
              )}
            </CardSection>
          </div>
        )}
      </div>
    </div>
  );
}
