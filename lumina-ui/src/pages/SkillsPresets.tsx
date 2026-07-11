import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package, LayoutTemplate, Cable, Search,
  CheckCircle, XCircle, Play, ExternalLink, Tag,
  User, Hash, RefreshCw, FileCode, Globe, Download, Trash2, ArrowUp,
  Mail, Calendar, Folder, MessageSquare, GitBranch, FileText, Music,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

interface Skill {
  name: string;
  description: string;
  tags: string[];
  author: string;
  version: string;
  source?: string;
}

interface SkillSource {
  name: string;
  url: string;
  skill_count: number;
}

interface Preset {
  name: string;
  label: string;
  description: string;
  category: string;
  system_prompt: string;
  tools: string[];
  icon: string;
}

interface CommunitySkill {
  id: string;
  name: string;
  repo: string;
  description: string;
  installs: number;
  author: string;
  tags: string[];
  installed: boolean;
  version: string;
}

interface Connector {
  name: string;
  label: string;
  description: string;
  icon: string;
  connected: boolean;
}

const FALLBACK_SKILLS: Skill[] = [
  { name: 'code-explorer', description: 'Explore and understand code files on the local filesystem', tags: ['code', 'files', 'development'], author: 'Lumina', version: '1.0.0' },
  { name: 'code-generator', description: 'Generate production-ready code in any language with tests and docs', tags: ['code', 'generation', 'development'], author: 'Lumina', version: '1.0.0' },
  { name: 'code-reviewer', description: 'Review code for bugs, security issues, performance problems, and best practices', tags: ['code', 'review', 'quality'], author: 'Lumina', version: '1.0.0' },
  { name: 'code-optimizer', description: 'Analyze and optimize code for speed, memory usage, and readability', tags: ['code', 'optimization', 'performance'], author: 'Lumina', version: '1.0.0' },
  { name: 'code-documenter', description: 'Generate docstrings, README, and API documentation from source code', tags: ['code', 'documentation', 'docs'], author: 'Lumina', version: '1.0.0' },
  { name: 'automated-tester', description: 'Run test suites and generate detailed test reports with coverage tracking', tags: ['testing', 'qa', 'automation'], author: 'Lumina', version: '1.0.0' },
  { name: 'test-generator', description: 'Generate unit tests, integration tests, and test cases for any code', tags: ['testing', 'code', 'quality'], author: 'Lumina', version: '1.0.0' },
  { name: 'workflow-automator', description: 'Create multi-step automated workflows with conditions and branching', tags: ['automation', 'workflow', 'productivity'], author: 'Lumina', version: '1.0.0' },
  { name: 'task-scheduler', description: 'Schedule recurring tasks using cron expressions with logging', tags: ['scheduling', 'automation', 'tasks'], author: 'Lumina', version: '1.0.0' },
  { name: 'web-search', description: 'Search the web for current information and news', tags: ['web', 'search', 'research'], author: 'Lumina', version: '1.0.0' },
  { name: 'web-scraper', description: 'Fetch and extract readable content from any web page', tags: ['web', 'scraping', 'content'], author: 'Lumina', version: '1.0.0' },
  { name: 'weather', description: 'Get current weather conditions for any city worldwide', tags: ['weather', 'information', 'daily'], author: 'Lumina', version: '1.0.0' },
  { name: 'news', description: 'Fetch the latest news headlines by topic or country', tags: ['news', 'media', 'information'], author: 'Lumina', version: '1.0.0' },
  { name: 'calculator', description: 'Evaluate mathematical expressions safely', tags: ['math', 'calculation', 'utility'], author: 'Lumina', version: '1.0.0' },
  { name: 'translator', description: 'Translate text between 100+ languages', tags: ['language', 'translation', 'communication'], author: 'Lumina', version: '1.0.0' },
  { name: 'smart-translator', description: 'Detect language and translate between 100+ languages with optional voice output', tags: ['translation', 'language', 'communication', 'voice'], author: 'Lumina', version: '1.0.0' },
  { name: 'voice-tts', description: 'Convert text to natural speech in any language with TTS engine', tags: ['voice', 'speech', 'audio', 'accessibility'], author: 'Lumina', version: '1.0.0' },
  { name: 'voice-stt', description: 'Transcribe speech from audio files to text in any language', tags: ['voice', 'speech', 'transcription', 'audio'], author: 'Lumina', version: '1.0.0' },
  { name: 'reading-comprehension', description: 'Read text content and answer questions about it with detailed analysis', tags: ['reading', 'comprehension', 'analysis', 'education'], author: 'Lumina', version: '1.0.0' },
  { name: 'context-qa', description: 'Answer questions using reasoning, context understanding, and related knowledge in any language', tags: ['reasoning', 'qa', 'knowledge', 'thinking'], author: 'Lumina', version: '1.0.0' },
  { name: 'whatsapp-messenger', description: 'Send WhatsApp text messages to any phone number via configured WhatsApp API', tags: ['whatsapp', 'messaging', 'communication'], author: 'Lumina', version: '1.0.0' },
  { name: 'multi-language-chat', description: 'Chat and communicate with clients in their preferred language across any channel', tags: ['chat', 'communication', 'multi-language', 'client'], author: 'Lumina', version: '1.0.0' },
  { name: 'shell-command', description: 'Execute shell commands safely with read-only protection', tags: ['terminal', 'shell', 'development'], author: 'Lumina', version: '1.0.0' },
  { name: 'file-manager', description: 'Create, copy, move, delete, and read files and folders', tags: ['files', 'storage', 'management'], author: 'Lumina', version: '1.0.0' },
  { name: 'system-info', description: 'Get detailed system information (OS, CPU, memory, disk)', tags: ['system', 'monitoring', 'diagnostics'], author: 'Lumina', version: '1.0.0' },
  { name: 'git-ops', description: 'Run Git operations: status, log, diff, branch, remote', tags: ['git', 'version-control', 'development'], author: 'Lumina', version: '1.0.0' },
  { name: 'database-query', description: 'Execute SQL queries against SQLite databases', tags: ['database', 'sql', 'data'], author: 'Lumina', version: '1.0.0' },
  { name: 'api-integrator', description: 'Connect to any REST API with full request/response handling', tags: ['api', 'integration', 'web'], author: 'Lumina', version: '1.0.0' },
  { name: 'password-generator', description: 'Generate strong random passwords with customizable length', tags: ['security', 'passwords', 'utility'], author: 'Lumina', version: '1.0.0' },
  { name: 'unit-converter', description: 'Convert between units (length, weight, temperature, speed, volume)', tags: ['conversion', 'utility', 'math'], author: 'Lumina', version: '1.0.0' },
  { name: 'date-time', description: 'Get current time, convert timezones, calculate date differences', tags: ['time', 'date', 'utility'], author: 'Lumina', version: '1.0.0' },
  { name: 'learning-researcher', description: 'Deep research on any topic with structured summaries and learning paths', tags: ['learning', 'research', 'education'], author: 'Lumina', version: '1.0.0' },
  { name: 'notes', description: 'Save, search, and manage personal knowledge notes', tags: ['notes', 'knowledge', 'productivity'], author: 'Lumina', version: '1.0.0' },
  { name: 'memory-recall', description: 'Search past conversations and learned knowledge', tags: ['memory', 'knowledge', 'history'], author: 'Lumina', version: '1.0.0' },
  { name: 'data-analyzer', description: 'Analyze JSON, CSV, or tabular data with stats and previews', tags: ['data', 'analytics', 'csv', 'json'], author: 'Lumina', version: '1.0.0' },
  { name: 'report-generator', description: 'Generate formatted reports in PDF, HTML, Markdown, CSV, or JSON', tags: ['reports', 'data', 'analytics'], author: 'Lumina', version: '1.0.0' },
  { name: 'data-pipeline', description: 'Build ETL pipelines with extraction, transformation, and loading stages', tags: ['data', 'pipeline', 'etl', 'automation'], author: 'Lumina', version: '1.0.0' },
  { name: 'email-automation', description: 'Create automated email campaigns with templates and follow-up sequences', tags: ['email', 'automation', 'marketing'], author: 'Lumina', version: '1.0.0' },
  { name: 'social-auto-poster', description: 'Schedule and auto-post to Twitter, LinkedIn, Facebook, Instagram, TikTok', tags: ['social', 'automation', 'marketing'], author: 'Lumina', version: '1.0.0' },
  { name: 'container-manager', description: 'Manage Docker containers, images, and compose stacks', tags: ['docker', 'containers', 'devops'], author: 'Lumina', version: '1.0.0' },
  { name: 'data-backup', description: 'Backup and restore files, databases, and configurations with scheduling', tags: ['backup', 'data', 'automation'], author: 'Lumina', version: '1.0.0' },
  { name: 'dependency-checker', description: 'Check dependencies for updates, security vulnerabilities, and licenses', tags: ['dependencies', 'security', 'maintenance'], author: 'Lumina', version: '1.0.0' },
  { name: 'webhook-handler', description: 'Register and manage webhooks for real-time event-driven automation', tags: ['webhook', 'automation', 'events'], author: 'Lumina', version: '1.0.0' },
  { name: 'file-watcher', description: 'Watch files and directories for changes and trigger automated actions', tags: ['files', 'watching', 'automation'], author: 'Lumina', version: '1.0.0' },
  { name: 'crypto-price', description: 'Get current cryptocurrency prices and 24h changes', tags: ['crypto', 'finance', 'price'], author: 'Lumina', version: '1.0.0' },
  { name: 'ip-info', description: 'Get your public IP address and geolocation data', tags: ['network', 'ip', 'geolocation'], author: 'Lumina', version: '1.0.0' },
  { name: 'task-planner', description: 'Plan and organize complex tasks into actionable steps', tags: ['planning', 'productivity', 'organization'], author: 'Lumina', version: '1.0.0' },
  { name: 'idea-generator', description: 'Generate creative ideas, names, and suggestions for projects', tags: ['creative', 'ideas', 'brainstorming'], author: 'Lumina', version: '1.0.0' },
  { name: 'summarizer', description: 'Condense long text into key bullet points', tags: ['text', 'productivity', 'writing'], author: 'Lumina', version: '1.0.0' },
  { name: 'email-sender', description: 'Send emails to any address (requires SMTP config)', tags: ['email', 'communication', 'productivity'], author: 'Lumina', version: '1.0.0' },
  { name: 'qr-generator', description: 'Generate QR code images from text or URLs', tags: ['qr', 'barcode', 'utility'], author: 'Lumina', version: '1.0.0' },
  { name: 'url-shortener', description: 'Shorten URLs using TinyURL', tags: ['url', 'utility', 'web'], author: 'Lumina', version: '1.0.0' },
  { name: 'color-helper', description: 'Convert colors between hex, RGB, and HSL formats', tags: ['color', 'design', 'utility'], author: 'Lumina', version: '1.0.0' },
  { name: 'lorem-ipsum', description: 'Generate placeholder text for designs and mockups', tags: ['design', 'text', 'utility'], author: 'Lumina', version: '1.0.0' },
  { name: 'random-generator', description: 'Generate random numbers, UUIDs, dice rolls, and coin flips', tags: ['random', 'utility', 'fun'], author: 'Lumina', version: '1.0.0' },
  { name: 'skill-optimizer', description: 'Analyze and optimize skill performance from usage data', tags: ['optimization', 'skills', 'performance'], author: 'Lumina', version: '1.0.0' },
  { name: 'pdf-reader', description: 'Extract text content from PDF files', tags: ['pdf', 'documents', 'files'], author: 'Lumina', version: '1.0.0' },
];

const FALLBACK_PRESETS: Preset[] = [
  { name: 'lumina-bot', label: 'Lumina Bot', description: 'Full-stack development agent — code generation, review, optimization, documentation, and testing', category: 'development', system_prompt: 'You are Lumina Bot — a full-stack AI development agent. Generate code, review, optimize, document, and test.', tools: ['code_generator', 'code_reviewer', 'code_optimizer', 'code_documenter', 'automated_tester', 'test_generator', 'git_ops'], icon: 'Cpu' },
  { name: 'automation-engineer', label: 'Automation Engineer', description: 'Design and run automated workflows, pipelines, scheduled tasks, and event-driven automations', category: 'automation', system_prompt: 'You are an Automation Engineer. Design workflows, pipelines, scheduled tasks, and event-driven automations.', tools: ['workflow_automator', 'task_scheduler', 'data_pipeline', 'file_watcher', 'webhook_handler', 'api_integrator'], icon: 'Activity' },
  { name: 'learning-specialist', label: 'Learning Specialist', description: 'Deep research, learning paths, skill optimization, and knowledge management across any domain', category: 'learning', system_prompt: 'You are a Learning Specialist. Research topics in depth, create learning paths, and manage knowledge.', tools: ['learning_researcher', 'web_searcher', 'summarizer', 'translator', 'reading_comprehension', 'context_qa', 'notes_manager'], icon: 'Brain' },
  { name: 'qa-tester', label: 'QA Tester', description: 'Automated testing, test generation, code review, quality reports, and bug tracking', category: 'testing', system_prompt: 'You are a QA Tester. Ensure quality through testing, test generation, code review, and reporting.', tools: ['automated_tester', 'test_generator', 'code_reviewer', 'report_generator', 'api_integrator', 'code_explorer'], icon: 'Bug' },
  { name: 'code-assistant', label: 'Code Assistant', description: 'Agent with code execution, file I/O, and shell access for development', category: 'development', system_prompt: 'You are a senior software engineer. Help with code writing, debugging, code review, and architecture.', tools: ['code_explorer', 'system_info', 'task_planner'], icon: 'Code2' },
  { name: 'morning-digest', label: 'Morning Digest', description: 'Daily briefing — email, calendar, tasks, news, and weather read aloud', category: 'productivity', system_prompt: 'You are a morning briefing assistant. Summarize weather, news, calendar, tasks.', tools: ['web_searcher', 'system_info'], icon: 'Sun' },
  { name: 'deep-research', label: 'Deep Research', description: 'Multi-hop research with citations across web and local docs', category: 'research', system_prompt: 'You are a research assistant. Break down questions, search, synthesize, cite sources.', tools: ['web_searcher', 'code_explorer'], icon: 'Search' },
  { name: 'orchestrator', label: 'Orchestrator', description: 'Multi-agent orchestration — delegates subtasks to specialized agents', category: 'advanced', system_prompt: 'You are an orchestrator. Break down tasks, delegate to specialized agents, synthesize results.', tools: ['web_searcher', 'task_planner', 'code_explorer'], icon: 'Crown' },
  { name: 'native-coder', label: 'Native Coder', description: 'CodeAct-style agent that generates and executes Python code', category: 'development', system_prompt: 'You are a code execution agent. Generate complete, runnable Python scripts.', tools: ['code_explorer', 'system_info'], icon: 'Terminal' },
  { name: 'social-manager', label: 'Social Media Manager', description: 'Schedule and manage social media content across platforms', category: 'business', system_prompt: 'You are a social media manager. Plan content calendars, write posts, analyze engagement.', tools: ['web_searcher', 'task_planner'], icon: 'Globe' },
  { name: 'scheduled-monitor', label: 'Scheduled Monitor', description: 'Stateful agent on a schedule with memory that watches and reports', category: 'automation', system_prompt: 'You are a monitoring agent. Watch resources, report anomalies, maintain state.', tools: ['system_info'], icon: 'Activity' },
  { name: 'chat-simple', label: 'Simple Chat', description: 'Lightweight conversation agent, no tools', category: 'general', system_prompt: 'You are a helpful AI assistant. Answer questions clearly and concisely.', tools: [], icon: 'MessageSquare' },
];

const FALLBACK_CONNECTORS: Connector[] = [
  { name: 'gmail', label: 'Gmail', description: 'Read and send emails, search inbox', icon: 'Mail', connected: false },
  { name: 'google-calendar', label: 'Google Calendar', description: 'View and manage calendar events, create reminders', icon: 'Calendar', connected: false },
  { name: 'google-tasks', label: 'Google Tasks', description: 'Manage task lists, create and complete tasks', icon: 'CheckSquare', connected: false },
  { name: 'google-drive', label: 'Google Drive', description: 'Access files, search documents, manage storage', icon: 'Folder', connected: false },
  { name: 'outlook', label: 'Outlook', description: 'Microsoft email and calendar integration', icon: 'Mail', connected: false },
  { name: 'slack', label: 'Slack', description: 'Send messages, monitor channels, search history', icon: 'MessageSquare', connected: false },
  { name: 'github', label: 'GitHub', description: 'Manage repos, issues, PRs, and code reviews', icon: 'GitBranch', connected: false },
  { name: 'notion', label: 'Notion', description: 'Access notes, databases, pages, and wikis', icon: 'FileText', connected: false },
  { name: 'linear', label: 'Linear', description: 'Project management, issue tracking, sprints', icon: 'CheckSquare', connected: false },
  { name: 'spotify', label: 'Spotify', description: 'Control playback, manage playlists, discover music', icon: 'Music', connected: false },
];

export default function SkillsPresets() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [tab, setTab] = useState('skills');
  const [search, setSearch] = useState('');

  const [skills, setSkills] = useState<Skill[]>(FALLBACK_SKILLS);
  const [sources, setSources] = useState<SkillSource[]>([]);
  const [presets, setPresets] = useState<Preset[]>(FALLBACK_PRESETS);
  const [communitySkills, setCommunitySkills] = useState<CommunitySkill[]>([]);
  const [communityLoading, setCommunityLoading] = useState(false);
  const [connectors, setConnectors] = useState<Connector[]>(FALLBACK_CONNECTORS);
  const [connectorTotal, setConnectorTotal] = useState(FALLBACK_CONNECTORS.length);
  const [toggling, setToggling] = useState<string | null>(null);
  const [actionSkill, setActionSkill] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [skillsRes, sourcesRes] = await Promise.all([
        get<{ skills: Skill[]; sources: SkillSource[] }>('/skills'),
        get<{ sources: SkillSource[] }>('/skills/sources'),
      ]);
      if (skillsRes.skills?.length) setSkills(skillsRes.skills);
      if (sourcesRes.sources?.length) setSources(sourcesRes.sources);
    } catch { /* fallback data already set */ }
  }, []);

  const loadPresets = useCallback(async () => {
    try {
      const res = await get<{ presets: Preset[]; categories: string[] }>('/presets');
      if (res.presets?.length) setPresets(res.presets);
    } catch { /* fallback data already set */ }
  }, []);

  const loadConnectors = useCallback(async () => {
    try {
      const res = await get<{ connectors: Connector[]; total: number }>('/connectors');
      if (res.connectors?.length) {
        setConnectors(res.connectors);
        setConnectorTotal(res.total || 0);
      }
    } catch { /* fallback data already set */ }
  }, []);

  const loadCommunity = useCallback(async () => {
    setCommunityLoading(true);
    try {
      const res = await get<{ skills: CommunitySkill[] }>('/community-skills?limit=100');
      setCommunitySkills(res.skills || []);
    } catch { /* fallback */ }
    setCommunityLoading(false);
  }, []);

  useEffect(() => {
    if (tab === 'skills') loadAll();
    else if (tab === 'presets') loadPresets();
    else if (tab === 'community') loadCommunity();
    else if (tab === 'connectors') loadConnectors();
  }, [tab, loadAll, loadPresets, loadCommunity, loadConnectors]);

  const launchPreset = (preset: Preset) => {
    try {
      sessionStorage.setItem('lumina_preset', JSON.stringify({ name: preset.name, tools: preset.tools, system_prompt: preset.system_prompt }));
    } catch {}
    navigate('/agents');
  };

  const importSkill = async (repo: string, name: string) => {
    setActionSkill(name);
    try {
      await post('/community-skills/import', { repo, name });
      addToast(`Imported ${name}`, 'success');
      loadCommunity();
    } catch { addToast(`Failed to import ${name}`, 'error'); }
    setActionSkill(null);
  };

  const removeSkill = async (id: string, name: string) => {
    setActionSkill(name);
    try {
      await post(`/community-skills/${encodeURIComponent(id)}/remove`);
      addToast(`Removed ${name}`, 'success');
      loadCommunity();
    } catch { addToast(`Failed to remove ${name}`, 'error'); }
    setActionSkill(null);
  };

  const upgradeSkill = async (id: string, name: string) => {
    setActionSkill(name);
    try {
      await post(`/community-skills/${encodeURIComponent(id)}/upgrade`);
      addToast(`Upgraded ${name}`, 'success');
      loadCommunity();
    } catch { addToast(`Failed to upgrade ${name}`, 'error'); }
    setActionSkill(null);
  };

  const toggleConnector = async (name: string, connected: boolean) => {
    setToggling(name);
    const action = connected ? 'disconnect' : 'connect';
    try {
      await post(`/connectors/${name}/${action}`);
      addToast(`${name} ${action === 'connect' ? 'connected' : 'disconnected'}`, 'success');
      loadConnectors();
    } catch {
      addToast(`Failed to ${action} ${name}`, 'error');
    }
    setToggling(null);
  };

  const connectedCount = connectors.filter(c => c.connected).length;

  const filteredSkills = skills.filter(s =>
    s.name.toLowerCase().includes(search.toLowerCase()) ||
    s.description.toLowerCase().includes(search.toLowerCase()) ||
    s.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))
  );

  const groupedPresets = presets.reduce<Record<string, Preset[]>>((acc, p) => {
    const cat = p.category || 'Uncategorized';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(p);
    return acc;
  }, {});

  const TABS = [
    { id: 'skills', label: 'Skills', icon: Package },
    { id: 'presets', label: 'Presets', icon: LayoutTemplate },
    { id: 'community', label: 'Community', icon: Globe },
    { id: 'connectors', label: 'Connectors', icon: Cable },
  ];

  return (
    <div className="p-6 space-y-6">
      <PageHeader
        icon={Package}
        title="Skills & Presets"
        description="Extend capabilities with skills, presets, and connectors"
        actions={
          <button onClick={() => {
            if (tab === 'skills') loadAll();
            else if (tab === 'presets') loadPresets();
            else if (tab === 'community') loadCommunity();
            else if (tab === 'connectors') loadConnectors();
          }} className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
        }
      />

      <div className="flex items-center gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/5 w-fit">
        {TABS.map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); setSearch(''); }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t.id ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'text-slate-400 hover:text-slate-200'
            }`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'skills' && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 flex-1 border border-white/10">
              <Search className="w-4 h-4 text-slate-500" />
              <input value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Search skills..." />
            </div>
            <span className="text-xs text-slate-500">{skills.length} skills</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filteredSkills.map(s => (
              <div key={s.name}
                className="bg-white/[0.02] border border-white/10 hover:border-lumina-500/30 hover:bg-white/[0.04] rounded-xl p-4 transition-all group">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-10 h-10 rounded-xl bg-lumina-600/15 text-lumina-400 flex items-center justify-center shrink-0">
                      <Package className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{s.name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                      <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-0.5">
                        <User className="w-3 h-3" /> {s.author}
                        <Hash className="w-3 h-3" /> v{s.version}
                      </div>
                    </div>
                  </div>
                  <span className="text-[9px] px-2 py-1 rounded-full bg-lumina-600/15 text-lumina-400 border border-lumina-500/20 shrink-0">
                    Install
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">{s.description}</p>
                <div className="flex items-center gap-1.5 mt-3 flex-wrap">
                  {s.tags?.map(t => (
                    <span key={t} className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500 flex items-center gap-1">
                      <Tag className="w-2.5 h-2.5" /> {t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {filteredSkills.length === 0 && (
            <div className="text-center py-12">
              <Package className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No skills found</p>
            </div>
          )}

          {sources.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-1">Skill Sources</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {sources.map(s => (
                  <div key={s.name}
                    className="bg-white/[0.02] border border-white/10 rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-200">{s.name}</p>
                      <p className="text-[10px] text-slate-500">{s.skill_count || 0} skills</p>
                    </div>
                    <ExternalLink className="w-4 h-4 text-slate-500" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'presets' && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 flex-1 border border-white/10">
              <Search className="w-4 h-4 text-slate-500" />
              <input value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Search presets..." />
            </div>
            <span className="text-xs text-slate-500">{presets.length} presets</span>
          </div>

          {Object.entries(groupedPresets).map(([cat, items]) => {
            const filtered = items.filter(p =>
              p.name.toLowerCase().includes(search.toLowerCase()) ||
              p.description.toLowerCase().includes(search.toLowerCase()) ||
              p.tools.some(t => t.toLowerCase().includes(search.toLowerCase()))
            );
            if (filtered.length === 0) return null;
            return (
              <div key={cat}>
                <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-1">{cat} ({filtered.length})</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {filtered.map(p => (
                    <div key={p.name}
                      className="bg-white/[0.02] border border-white/10 hover:border-lumina-500/30 hover:bg-white/[0.04] rounded-xl p-4 transition-all group flex flex-col">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-200 truncate">{p.label || p.name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                        <p className="text-xs text-slate-400 mt-1 leading-relaxed line-clamp-2">{p.description}</p>
                        {p.system_prompt && (
                          <div className="mt-3 bg-slate-950/50 rounded-lg p-3 border border-white/5">
                            <p className="text-[10px] text-slate-500 mb-1">System Prompt</p>
                            <p className="text-[10px] text-slate-400 font-mono leading-relaxed line-clamp-3">{p.system_prompt}</p>
                          </div>
                        )}
                        {p.tools && p.tools.length > 0 && (
                          <div className="mt-3">
                            <p className="text-[10px] text-slate-500 mb-1.5">Tools ({p.tools.length})</p>
                            <div className="flex flex-wrap gap-1">
                              {p.tools.map(t => (
                                <span key={t}
                                  className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500 flex items-center gap-1">
                                  <FileCode className="w-2.5 h-2.5" /> {t}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                      <button onClick={() => launchPreset(p)}
                        className="mt-4 w-full bg-lumina-600 hover:bg-lumina-500 text-white rounded-lg py-2 text-xs font-medium transition-all flex items-center justify-center gap-2 shadow-lg shadow-lumina-500/20">
                        <Play className="w-3.5 h-3.5" /> Launch {p.label || p.name}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
          {Object.keys(groupedPresets).length === 0 && (
            <div className="text-center py-12">
              <LayoutTemplate className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No presets available</p>
            </div>
          )}
        </div>
      )}

      {tab === 'community' && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 flex-1 border border-white/10">
              <Search className="w-4 h-4 text-slate-500" />
              <input value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Search community skills..." />
            </div>
            <button onClick={loadCommunity} className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {communitySkills.filter(s =>
              s && (!search ||
              (s.name || '').toLowerCase().includes(search.toLowerCase()) ||
              (s.description || '').toLowerCase().includes(search.toLowerCase()) ||
              (s.repo || '').toLowerCase().includes(search.toLowerCase()) ||
              (s.tags || []).some(t => (t || '').toLowerCase().includes(search.toLowerCase())))
            ).map(s => (
              <div key={s.id}
                className="bg-white/[0.02] border border-white/10 hover:border-lumina-500/30 hover:bg-white/[0.04] rounded-xl p-4 transition-all group">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                      s.installed ? 'bg-emerald-500/15 text-emerald-400' : 'bg-lumina-600/15 text-lumina-400'
                    }`}>
                      <Globe className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{s.name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                      <p className="text-[10px] text-slate-500 truncate">{s.repo}</p>
                    </div>
                  </div>
                  <span className={`text-[9px] px-2 py-1 rounded-full shrink-0 ${
                    s.installed ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800/50 text-slate-500 border border-white/5'
                  }`}>
                    {s.installed ? 'Installed' : `${s.installs.toLocaleString()} installs`}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-2 mb-3">{s.description}</p>
                <div className="flex items-center gap-1.5 flex-wrap mb-3">
                  {s.tags?.map(t => (
                    <span key={t} className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500">
                      {t}
                    </span>
                  ))}
                </div>
                <div className="flex gap-2">
                  {s.installed ? (
                    <>
                      <button onClick={() => upgradeSkill(s.id, s.name)} disabled={actionSkill === s.name}
                        className="flex-1 px-3 py-1.5 rounded-lg bg-lumina-600/10 text-lumina-400 hover:bg-lumina-600/20 border border-lumina-500/20 text-[10px] font-medium transition-all flex items-center justify-center gap-1 disabled:opacity-50">
                        <ArrowUp className="w-3 h-3" /> Upgrade
                      </button>
                      <button onClick={() => removeSkill(s.id, s.name)} disabled={actionSkill === s.name}
                        className="flex-1 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 text-[10px] font-medium transition-all flex items-center justify-center gap-1 disabled:opacity-50">
                        <Trash2 className="w-3 h-3" /> Remove
                      </button>
                    </>
                  ) : (
                    <button onClick={() => importSkill(s.repo, s.name)} disabled={actionSkill === s.name}
                      className="w-full px-3 py-1.5 rounded-lg bg-lumina-600 hover:bg-lumina-500 text-white text-[10px] font-medium transition-all flex items-center justify-center gap-1 disabled:opacity-50">
                      <Download className="w-3 h-3" /> Import
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          {communitySkills.length === 0 && !communityLoading && (
            <div className="text-center py-12">
              <Globe className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No community skills found</p>
            </div>
          )}
        </div>
      )}

      {tab === 'connectors' && (
        <div className="space-y-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 border border-white/10">
              <Search className="w-4 h-4 text-slate-500" />
              <input value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Search connectors..." />
            </div>
            <span className="text-xs text-slate-500">{connectedCount}/{connectorTotal} connected</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {connectors.filter(c =>
              c.name.toLowerCase().includes(search.toLowerCase()) ||
              c.description.toLowerCase().includes(search.toLowerCase())
            ).map(c => (
              <div key={c.name}
                className="bg-white/[0.02] border border-white/10 hover:border-lumina-500/30 hover:bg-white/[0.04] rounded-xl p-4 transition-all group">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                      c.connected ? 'bg-emerald-500/15 text-emerald-400' : 'bg-slate-800/50 text-slate-500'
                    }`}>
                      {(() => { switch(c.name) {
                        case 'gmail': return <Mail className="w-5 h-5" />;
                        case 'google-calendar': return <Calendar className="w-5 h-5" />;
                        case 'google-tasks': return <CheckCircle className="w-5 h-5" />;
                        case 'google-drive': return <Folder className="w-5 h-5" />;
                        case 'outlook': return <Mail className="w-5 h-5" />;
                        case 'slack': return <MessageSquare className="w-5 h-5" />;
                        case 'github': return <GitBranch className="w-5 h-5" />;
                        case 'notion': return <FileText className="w-5 h-5" />;
                        case 'linear': return <CheckCircle className="w-5 h-5" />;
                        case 'spotify': return <Music className="w-5 h-5" />;
                        default: return <Cable className="w-5 h-5" />;
                      } })()}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{c.label || c.name}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5 truncate">{c.description}</p>
                    </div>
                  </div>
                  <span className={`text-[9px] px-2 py-1 rounded-full flex items-center gap-1 shrink-0 ${
                    c.connected
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-slate-800/50 text-slate-500 border border-white/5'
                  }`}>
                    {c.connected ? <CheckCircle className="w-2.5 h-2.5" /> : <XCircle className="w-2.5 h-2.5" />}
                    {c.connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                <div className="flex gap-2 mt-4">
                  <button onClick={() => toggleConnector(c.name, c.connected)} disabled={toggling === c.name}
                    className={`flex-1 rounded-lg py-2 text-xs font-medium transition-all flex items-center justify-center gap-2 ${
                      c.connected
                        ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20'
                        : 'bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-500/20'
                    } disabled:opacity-50`}>
                    {c.connected ? 'Disconnect' : 'Connect'}
                  </button>
                  {c.connected && (
                    <button onClick={() => { addToast(`${c.label || c.name}: fetching data...`, 'info'); }}
                      className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-400 hover:text-slate-200 transition-all flex items-center gap-1">
                      <RefreshCw className="w-3 h-3" /> Test
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          {connectors.length === 0 && (
            <div className="text-center py-12">
              <Cable className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No connectors available</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
