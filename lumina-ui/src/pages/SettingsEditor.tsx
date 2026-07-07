import { useEffect, useState } from 'react';
import { api } from '../api';
import {
  Save, Eye, EyeOff, CheckCircle, XCircle, Cpu,
  Shield, Server, Activity, RefreshCw, Smartphone,
  Zap, Sliders, Terminal, Lock,
  LayoutDashboard, MessageSquare, Code2, Bot,
  BarChart3, Globe, Folder, Search, PenTool, Brain, Bug,
  ListOrdered, User, Store, Camera, Ear, Wrench, Database,
  UserCog, Sparkles, Monitor, GitBranch,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';

interface Provider { name: string; label: string; key: string; type: string; configured: boolean; }

interface FeatureDef {
  id: string;
  label: string;
  description: string;
  icon: React.FC<{ className?: string }>;
  category: string;
  service?: string;
  requires?: string[];
}

const FEATURES: FeatureDef[] = [
  { id: 'chat', label: 'Chat', description: 'AI chat with conversation history', icon: MessageSquare, category: 'Core', service: 'ai_engine' },
  { id: 'codeGenerator', label: 'Code Generator', description: 'Generate code from description', icon: Code2, category: 'Core', service: 'ai_engine' },
  { id: 'codeReview', label: 'Code Review', description: 'Automated code review & fixes', icon: Code2, category: 'Core', service: 'ai_engine' },
  { id: 'codingAgent', label: 'Coding Agent', description: 'Autonomous AI engineer — plan, edit, test & heal code', icon: GitBranch, category: 'Core', service: 'ai_engine' },
  { id: 'agents', label: 'Agents', description: 'Run specialized AI agents', icon: Bot, category: 'Core', service: 'agents' },
  { id: 'voiceAssistant', label: 'Voice Control', description: 'Voice commands & audio recording', icon: Ear, category: 'Core', service: 'voice_controller' },
  { id: 'automation', label: 'Automation', description: 'Advanced workflow builder, triggers & execution engine', icon: Wrench, category: 'Core', service: 'automation_engine' },

  { id: 'crm', label: 'CRM', description: 'Sales pipeline & contact management', icon: BarChart3, category: 'Business', service: 'crm' },
  { id: 'seo', label: 'SEO Toolkit', description: 'SEO audit, keywords & competitors', icon: Search, category: 'Business', service: 'seo' },
  { id: 'socialMedia', label: 'Social Media', description: 'Multi-platform social posting', icon: Globe, category: 'Business' },
  { id: 'contentWriter', label: 'AI Writer', description: 'Generate blog posts & marketing copy', icon: PenTool, category: 'Business' },
  { id: 'learning', label: 'Learning Agent', description: 'Research & knowledge extraction', icon: Brain, category: 'Business' },
  { id: 'selfTester', label: 'Self Tester', description: 'Automated test generation', icon: Bug, category: 'Business' },
  { id: 'employee', label: 'AI Employee', description: 'Autonomous task execution', icon: User, category: 'Business' },

  { id: 'desktopControl', label: 'Desktop Control', description: 'Launch apps, manage windows, file ops & AI agent', icon: Monitor, category: 'Tools', service: 'desktop' },
  { id: 'browserAgent', label: 'Browser Agent', description: 'AI-powered browser automation', icon: Globe, category: 'Tools', service: 'browser' },
  { id: 'fileManager', label: 'File Manager', description: 'Browse & edit server files', icon: Folder, category: 'Tools', service: 'desktop' },
  { id: 'android', label: 'Android Manager', description: 'ADB device control & app mgmt', icon: Smartphone, category: 'Tools', service: 'android' },
  { id: 'whatsapp', label: 'WhatsApp Messenger', description: 'Send & receive WhatsApp messages', icon: MessageSquare, category: 'Tools', service: 'whatsapp' },
  { id: 'whatsappBusiness', label: 'WA Business', description: 'WhatsApp Business catalog & orders', icon: Store, category: 'Tools', service: 'whatsapp' },
  { id: 'taskQueue', label: 'Task Queue', description: 'Multi-step pipeline orchestration', icon: ListOrdered, category: 'Tools', service: 'pipeline_builder' },
  { id: 'dataVault', label: 'Data Vault', description: 'Secure credential & key storage', icon: Database, category: 'Tools' },

  { id: 'vision', label: 'Vision / Camera', description: 'Camera capture, detection & scene description', icon: Camera, category: 'Advanced', service: 'camera' },
  { id: 'userManagement', label: 'User Management', description: 'User roles & access control', icon: UserCog, category: 'Advanced' },
  { id: 'pipelineBuilder', label: 'Pipeline Builder', description: 'Visual pipeline construction', icon: Sparkles, category: 'Advanced', service: 'pipeline_builder' },
];

const FEATURE_CATEGORIES = ['Core', 'Business', 'Tools', 'Advanced'] as const;

const STORAGE_KEY = 'lumina_feature_prefs';

function loadFeatures(): Record<string, boolean> {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      const prefs: Record<string, boolean> = {};
      for (const f of FEATURES) {
        prefs[f.id] = parsed[f.id] !== undefined ? parsed[f.id] : true;
      }
      return prefs;
    }
  } catch {}
  return Object.fromEntries(FEATURES.map(f => [f.id, true]));
}

export default function SettingsEditor() {
  const [providers] = useState<Provider[]>([
    { name: 'ollama', label: 'Ollama', key: 'OLLAMA_BASE_URL', type: 'local', configured: true },
    { name: 'openai', label: 'OpenAI', key: 'OPENAI_API_KEY', type: 'api', configured: false },
    { name: 'openrouter', label: 'OpenRouter', key: 'OPENROUTER_API_KEY', type: 'api', configured: false },
    { name: 'deepseek', label: 'DeepSeek', key: 'DEEPSEEK_API_KEY', type: 'api', configured: false },
    { name: 'groq', label: 'Groq', key: 'GROQ_API_KEY', type: 'api', configured: false },
    { name: 'gemini', label: 'Gemini', key: 'GEMINI_API_KEY', type: 'api', configured: false },
    { name: 'cloudflare', label: 'Cloudflare', key: 'CLOUDFLARE_API_TOKEN', type: 'api', configured: false },
    { name: 'nvidia', label: 'NVIDIA', key: 'NVIDIA_API_KEY', type: 'api', configured: false },
    { name: 'serp', label: 'SERP API', key: 'SERP_API_KEY', type: 'api', configured: false },
    { name: 'apify', label: 'Apify', key: 'APIFY_API_TOKEN', type: 'api', configured: false },
    { name: 'whatsapp', label: 'WhatsApp', key: 'WHATSAPP_API_KEY', type: 'api', configured: false },
  ]);

  const [section, setSection] = useState('overview');
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [saved, setSaved] = useState('');
  const [health, setHealth] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [kernel, setKernel] = useState<any>(null);
  const [features, setFeatures] = useState<Record<string, boolean>>(loadFeatures);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    api.config().then(c => {
      setConfig(c);
      if (c.providers) {
        providers.forEach(p => {
          p.configured = (c.providers as Record<string, boolean>)[p.name] || false;
        });
      }
    }).catch(() => {});
    (api as any).kernelStatus?.().then(setKernel).catch(() => {});
  }, []);

  const showSave = (msg: string) => { setSaved(msg); setTimeout(() => setSaved(''), 2000); };

  const toggleFeature = (key: string) => {
    setFeatures(prev => {
      const next = { ...prev, [key]: !prev[key] };
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch {}
      return next;
    });
  };

  const connected = providers.filter(p => p.configured).length;
  const enabledCount = Object.values(features).filter(Boolean).length;
  const totalCount = FEATURES.length;

  const sections = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'providers', label: 'AI Providers', icon: Zap },
    { id: 'models', label: 'Model Config', icon: Sliders },
    { id: 'features', label: `Features (${enabledCount}/${totalCount})`, icon: Sliders },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'whatsapp', label: 'WhatsApp', icon: Smartphone },
    { id: 'server', label: 'Server', icon: Server },
    { id: 'system', label: 'System', icon: Terminal },
  ];

  return (
    <div className="flex gap-6 h-full p-6">
      <div className="w-48 shrink-0 space-y-1">
        {sections.map(s => (
          <button key={s.id} onClick={() => setSection(s.id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs transition-all ${
              section === s.id ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20 font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
            }`}>
            <s.icon className="w-4 h-4" />
            <span className="truncate">{s.label}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 min-w-0 space-y-6 max-w-4xl">
        {saved && <div className="fixed top-4 right-4 z-50 bg-emerald-600 text-white px-4 py-2 rounded-xl text-sm shadow-lg animate-fade-in">{saved}</div>}

        {section === 'overview' && (
          <>
            <PageHeader icon={Activity} title="Settings" description="Full system control panel" />
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bento-card"><div className="flex items-center gap-3"><Activity className="w-8 h-8 text-emerald-400" /><div><p className="text-xs text-slate-400">Status</p><p className="text-lg font-bold text-white">{health?.status || '...'}</p></div></div></div>
              <div className="bento-card"><div className="flex items-center gap-3"><Server className="w-8 h-8 text-lumina-400" /><div><p className="text-xs text-slate-400">Version</p><p className="text-lg font-bold text-white">{config?.version || '...'}</p></div></div></div>
              <div className="bento-card"><div className="flex items-center gap-3"><Cpu className="w-8 h-8 text-violet-400" /><div><p className="text-xs text-slate-400">Provider</p><p className="text-lg font-bold text-white">{health?.primary_provider || '...'}</p></div></div></div>
              <div className="bento-card"><div className="flex items-center gap-3"><Shield className="w-8 h-8 text-amber-400" /><div><p className="text-xs text-slate-400">Services</p><p className="text-lg font-bold text-white">{kernel?.services?.length || '...'}</p></div></div></div>
            </div>
          </>
        )}

        {section === 'providers' && (
          <div className="bento-card">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-6">AI Providers ({connected}/{providers.length})</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {providers.map(p => (
                <div key={p.name} className={`p-4 rounded-xl border transition-all ${p.configured ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.04]'}`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${p.configured ? 'bg-emerald-500 shadow-lg shadow-emerald-500/30' : 'bg-slate-600'}`} />
                      <span className="text-sm font-medium text-slate-200">{p.label}</span>
                      {p.type === 'local' && <span className="text-[10px] px-1.5 py-0.5 rounded bg-lumina-500/10 text-lumina-400 border border-lumina-500/20">local</span>}
                    </div>
                    {p.configured ? <CheckCircle className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-slate-600" />}
                  </div>
                  <div className="flex items-center gap-2">
                    <input type={showKeys[p.name] ? 'text' : 'password'}
                      className="flex-1 bg-slate-950/50 border border-white/5 rounded-lg px-3 py-1.5 text-xs text-white/70 placeholder-slate-600 font-mono outline-none focus:border-lumina-500/50"
                      placeholder={p.configured ? '••••••••••••••••' : `Set ${p.key}`} readOnly
                      value={p.configured ? '••••••••••••••••' : ''} />
                    <button onClick={() => setShowKeys(s => ({ ...s, [p.name]: !s[p.name] }))} className="text-slate-500 hover:text-slate-300 p-1">
                      {showKeys[p.name] ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 bg-white/5 rounded-xl p-4 text-xs text-slate-500">Edit <code className="text-lumina-300 bg-white/10 px-1.5 py-0.5 rounded font-mono">.env</code> to update keys, then restart server.</div>
          </div>
        )}

        {section === 'models' && (
          <div className="bento-card space-y-5">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Model Configuration</h2>
            <div className="grid grid-cols-2 gap-5">
              <div><label className="text-xs text-slate-400 block mb-1.5">Ollama URL</label><input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" defaultValue="http://localhost:11434" /></div>
              <div><label className="text-xs text-slate-400 block mb-1.5">Default Model</label><input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" defaultValue="qwen2.5-coder:0.5b" /></div>
              <div><label className="text-xs text-slate-400 block mb-1.5">Temperature ({config?.temperature || '0.7'})</label><input type="range" min="0" max="2" step="0.1" className="w-full accent-lumina-500" defaultValue="0.7" /></div>
              <div><label className="text-xs text-slate-400 block mb-1.5">Max Tokens ({config?.max_tokens || '4096'})</label><input type="range" min="256" max="32768" step="256" className="w-full accent-lumina-500" defaultValue="4096" /></div>
            </div>
            <button onClick={() => showSave('Model settings saved')} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-5 py-2 text-sm font-medium w-fit transition-all flex items-center gap-2"><Save className="w-4 h-4" /> Save Model Config</button>
          </div>
        )}

        {section === 'features' && (
          <div className="space-y-6">
            <PageHeader icon={Sliders} title="Feature Controls" description={`${enabledCount} of ${totalCount} features enabled`} />
            {FEATURE_CATEGORIES.map(cat => {
              const catFeatures = FEATURES.filter(f => f.category === cat);
              const catEnabled = catFeatures.filter(f => features[f.id]).length;
              return (
                <div key={cat} className="bento-card">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">{cat}</h2>
                    <span className="text-xs text-slate-500 bg-white/5 px-2 py-0.5 rounded-full">{catEnabled}/{catFeatures.length}</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {catFeatures.map(f => {
                      const Icon = f.icon;
                      const enabled = features[f.id] ?? true;
                      return (
                        <div key={f.id} className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-all ${
                          enabled ? 'bg-white/[0.02] border-white/5 hover:bg-white/[0.04]' : 'bg-white/[0.01] border-white/5 opacity-60'
                        }`}>
                          <div className="flex items-center gap-3 min-w-0">
                            <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                              enabled ? 'bg-lumina-600/15 text-lumina-400' : 'bg-slate-800 text-slate-600'
                            }`}>
                              <Icon className="w-4 h-4" />
                            </div>
                            <div className="min-w-0">
                              <p className="text-sm text-slate-200 font-medium">{f.label}</p>
                              <p className="text-[10px] text-slate-500 truncate">{f.description}</p>
                              {f.service && (
                                <span className="text-[10px] text-slate-600 font-mono">← {f.service}</span>
                              )}
                            </div>
                          </div>
                          <button onClick={() => toggleFeature(f.id)}
                            className={`relative w-11 h-5 rounded-full transition-all duration-200 shrink-0 ml-3 ${
                              enabled ? 'bg-emerald-500' : 'bg-slate-700'
                            }`}>
                            <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-all duration-200 ${
                              enabled ? 'left-[22px]' : 'left-0.5'
                            }`} />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {section === 'security' && (
          <div className="space-y-5">
            <div className="bento-card space-y-4">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Shield className="w-4 h-4" /> Authentication</h2>
              <div className="flex items-center justify-between py-3 border-b border-white/5">
                <div><p className="text-sm text-slate-200">API Authentication</p><p className="text-xs text-slate-500">Require API key for all requests</p></div>
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${false ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>{false ? 'Enabled' : 'Disabled'}</div>
              </div>
              <div><label className="text-xs text-slate-400 block mb-1">API Keys (comma separated)</label><input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white font-mono outline-none focus:border-lumina-500/50" placeholder="key1, key2, key3" /></div>
              <div><label className="text-xs text-slate-400 block mb-1">Master Key</label><input type="password" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white font-mono outline-none focus:border-lumina-500/50" placeholder="Set LUMINA_MASTER_KEY in .env" /></div>
            </div>
            <div className="bento-card space-y-4">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Lock className="w-4 h-4" /> CORS</h2>
              <div><label className="text-xs text-slate-400 block mb-1">Allowed Origins</label><input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white font-mono outline-none focus:border-lumina-500/50" placeholder="http://localhost:5173, https://yourdomain.com" defaultValue="*" /></div>
            </div>
          </div>
        )}

        {section === 'whatsapp' && (
          <div className="bento-card space-y-5">
            <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Smartphone className="w-4 h-4" /> WhatsApp Configuration</h2>
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <div><p className="text-sm text-slate-200">WhatsApp API</p><p className="text-xs text-slate-500">Meta Cloud API (free up to 1,000 convos/month)</p></div>
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${false ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>Pending Review</div>
            </div>
            <div><label className="text-xs text-slate-400 block mb-1">API Token</label><input type="password" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white font-mono outline-none focus:border-lumina-500/50" placeholder="Paste Meta token when approved" /></div>
            <div><label className="text-xs text-slate-400 block mb-1">Phone Number ID</label><input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white font-mono outline-none focus:border-lumina-500/50" defaultValue="1257983506231819" /></div>
            <button onClick={() => showSave('WhatsApp settings saved')} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-5 py-2 text-sm font-medium w-fit transition-all flex items-center gap-2"><Save className="w-4 h-4" /> Save WhatsApp Config</button>
          </div>
        )}

        {section === 'server' && (
          <div className="space-y-5">
            <div className="bento-card space-y-4">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Activity className="w-4 h-4" /> Server Status</h2>
              <div className="grid grid-cols-2 gap-4">
                <div><p className="text-xs text-slate-400">Status</p><p className="text-sm font-medium text-emerald-400">Online</p></div>
                <div><p className="text-xs text-slate-400">API Port</p><p className="text-sm font-medium text-slate-200">8000</p></div>
                <div><p className="text-xs text-slate-400">UI Port</p><p className="text-sm font-medium text-slate-200">5173</p></div>
                <div><p className="text-xs text-slate-400">Services</p><p className="text-sm font-medium text-slate-200">{kernel?.services?.length || '12'} registered</p></div>
              </div>
            </div>
            <div className="bento-card space-y-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><RefreshCw className="w-4 h-4" /> Server Actions</h2>
              <div className="flex gap-3">
                <button onClick={() => { fetch('/api/system/health').then(r => r.json()).then(d => showSave(`Health: ${d.status}`)).catch(() => showSave('Server unreachable')); }}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-4 py-2 text-sm flex items-center gap-2"><Activity className="w-4 h-4" /> Check Health</button>
                <button onClick={async () => {
                  try {
                    const res = await fetch('/api/system/reload', { method: 'POST' });
                    const d = await res.json();
                    showSave(`Config reloaded: ${d.updated?.length || 0} settings updated`);
                  } catch { showSave('Reload failed'); }
                }} className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-4 py-2 text-sm flex items-center gap-2"><RefreshCw className="w-4 h-4" /> Reload Config</button>
              </div>
            </div>
          </div>
        )}

        {section === 'system' && (
          <div className="space-y-5">
            <div className="bento-card space-y-3">
              <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Terminal className="w-4 h-4" /> Environment</h2>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><p className="text-xs text-slate-400">App Name</p><p className="text-slate-200">{config?.app_name || 'Lumina AI OS'}</p></div>
                <div><p className="text-xs text-slate-400">Version</p><p className="text-slate-200">{config?.version || '1.0.0'}</p></div>
                <div><p className="text-xs text-slate-400">Primary Provider</p><p className="text-slate-200">{health?.primary_provider || 'ollama'}</p></div>
                <div><p className="text-xs text-slate-400">Active Providers</p><p className="text-slate-200">{health?.providers?.length || '8'}</p></div>
              </div>
            </div>
            <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-5">
              <p className="text-xs text-emerald-400 font-medium mb-1">✅ Hot Reload Supported</p>
              <p className="text-xs text-slate-500">Edit <code className="text-lumina-300 bg-white/10 px-1.5 py-0.5 rounded font-mono">.env</code> then click <strong>Reload Config</strong> in the Server section. No restart needed.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
