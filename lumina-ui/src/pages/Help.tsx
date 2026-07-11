import { useState } from 'react';
import {
  BookOpen, Search, Monitor, Bot, MessageSquare, Code2,
  Globe, BarChart3, Smartphone, Activity, Shield, Crown, Folder,
  Terminal, Cpu, Workflow, Eye, Puzzle, Zap,
} from 'lucide-react';

interface DocSection {
  id: string;
  label: string;
  icon: any;
  content: string[];
}

const sections: DocSection[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: Cpu,
    content: [
      '# Lumina AI OS',
      '**Version:** 1.0.0  |  **Developer:** AL ASAR JADEED',
      '',
      'Lumina is the world\'s first Autonomous AI Employee Operating System. It combines a powerful AI engine with desktop automation, browser control, Android device management, CRM, marketing, and much more — all accessible through a sleek web interface.',
      '',
      '**Core Capabilities:**',
      '- AI-powered chat and code generation',
      '- Desktop automation (apps, windows, clipboard, notifications)',
      '- Browser automation with live preview',
      '- Android device remote control',
      '- CRM with pipeline management',
      '- Marketing automation & SEO tools',
      '- Multi-agent orchestration',
      '- Voice assistant with wake-word detection',
      '- Vision & object detection',
      '- Task queue & scheduling',
      '- Autonomous AI employee agents',
    ],
  },
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: BarChart3,
    content: [
      '# Dashboard',
      'The Dashboard is your home screen. It shows real-time system health, active services, provider status, agent stats, CRM summary, marketing metrics, task queue, and recent activity.',
      '',
      '**Sections:**',
      '- **Overview** — System health, uptime, active services count',
      '- **System** — CPU, memory, disk usage, kernel services',
      '- **Providers** — AI model provider status (OpenAI, Anthropic, Google, etc.)',
      '- **Agents** — Running AI agents and their status',
      '- **CRM** — Deals, contacts, pipeline value',
      '- **Marketing** — Campaign metrics, lead count',
      '- **Tasks** — Active, completed, failed task counts',
      '- **Activity** — Recent system events and logs',
      '',
      'Click the Refresh button or any section card to drill down.',
    ],
  },
  {
    id: 'chat',
    label: 'Chat',
    icon: MessageSquare,
    content: [
      '# AI Chat',
      'The Chat interface lets you converse with Lumina\'s AI engine. Ask questions, get code, generate content, or execute tasks through natural language.',
      '',
      '**Features:**',
      '- Multi-turn conversations with context memory',
      '- Code syntax highlighting in responses',
      '- Markdown rendering',
      '- Conversation history (scrollable)',
      '- Send with Enter, Shift+Enter for newline',
      '',
      'The AI uses your configured provider (OpenAI, Anthropic, Google, etc.) and can access tools like web search, file system, and desktop automation.',
    ],
  },
  {
    id: 'code',
    label: 'Code Generation',
    icon: Code2,
    content: [
      '# Code Generator & Review',
      'Generate and review code in multiple programming languages.',
      '',
      '**Code Generator:**',
      '- Describe what you want in natural language',
      '- Choose language (Python, JavaScript, TypeScript, etc.)',
      '- Get ready-to-use code with explanations',
      '',
      '**Code Review:**',
      '- Paste code for AI-powered review',
      '- Get feedback on bugs, security issues, and best practices',
      '- Suggestions for optimization',
    ],
  },
  {
    id: 'agents',
    label: 'AI Agents',
    icon: Bot,
    content: [
      '# AI Agents',
      'Lumina comes with specialized AI agents for different tasks. Access them from the Agents page or the sidebar.',
      '',
      '**Available Agents:**',
      '- **Coding Agent** — Write, debug, and refactor code',
      '- **Content Writer** — Generate articles, posts, emails',
      '- **SEO Agent** — Analyze and optimize search rankings',
      '- **Learning Agent** — Research and summarize topics',
      '- **Self Tester** — Automated testing of your code',
      '- **Browser Agent** — Navigate and interact with web pages',
      '',
      'Each agent can be run independently or orchestrated in Multi-Agent mode.',
    ],
  },
  {
    id: 'multiagent',
    label: 'Multi-Agent',
    icon: Crown,
    content: [
      '# Multi-Agent Orchestration',
      'Combine multiple AI agents to work on complex tasks. The orchestrator assigns subtasks to specialized agents and combines results.',
      '',
      '**How it works:**',
      '1. Describe your high-level task',
      '2. Lumina breaks it down into subtasks',
      '3. Specialized agents work in parallel or sequence',
      '4. Results are combined into a final response',
      '',
      'Example: "Research competitors and write a marketing email" uses the Learning Agent + Content Writer Agent.',
    ],
  },
  {
    id: 'desktop',
    label: 'Desktop Control',
    icon: Monitor,
    content: [
      '# Desktop Control',
      'Control your computer directly from the browser. Launch apps, manage windows, run shell commands, and more.',
      '',
      '**Quick Launch:**',
      '- VS Code, Chrome, Firefox, Terminal, GIMP, Spotify',
      '- Click any icon to launch instantly',
      '',
      '**AI Agent tab:**',
      '- Type natural language commands like "Open VS Code and Chrome"',
      '- Lumina executes step-by-step and shows results',
      '- Example commands are provided for reference',
      '',
      '**Apps tab:**',
      '- View all running applications',
      '- Kill apps by clicking the X button',
      '',
      '**Windows tab:**',
      '- List all desktop windows with dimensions',
      '- Focus, minimize, or close windows',
      '',
      '**System tab:**',
      '- Read clipboard content',
      '- Send desktop notifications',
      '- Open terminal, run commands, list processes',
    ],
  },
  {
    id: 'browser',
    label: 'Browser Agent',
    icon: Globe,
    content: [
      '# Browser Agent',
      'Lumina includes a built-in browser agent that can navigate websites, fill forms, take screenshots, and extract data.',
      '',
      '**Features:**',
      '- Navigate to any URL with live iframe preview',
      '- AI-powered form filling and data extraction',
      '- Screenshot capture',
      '- Download management',
      '- Session persistence across browser sessions',
      '',
      'Access via the top menu bar "Browser" button or the sidebar Browser Agent link.',
    ],
  },
  {
    id: 'crm',
    label: 'CRM',
    icon: BarChart3,
    content: [
      '# CRM (Customer Relationship Management)',
      'Manage contacts, deals, and sales pipeline.',
      '',
      '**Tabs:**',
      '- **Overview** — Summary metrics, pipeline value, conversion rate',
      '- **Contacts** — Add, search, and manage contacts',
      '- **Deals** — Track deals through pipeline stages',
      '',
      'Each deal has: title, value, contact, stage (lead → qualified → proposal → negotiation → closed won/lost).',
    ],
  },
  {
    id: 'seo',
    label: 'SEO Toolkit',
    icon: Search,
    content: [
      '# SEO Toolkit',
      'Analyze and optimize websites for search engines.',
      '',
      '**Capabilities:**',
      '- Add and manage websites for SEO tracking',
      '- Keyword analysis and ranking data',
      '- On-page SEO suggestions',
      '- Site audit and health reports',
      '- Backlink monitoring',
    ],
  },
  {
    id: 'android',
    label: 'Android Manager',
    icon: Smartphone,
    content: [
      '# Android Device Manager',
      'Connect and control Android devices via ADB (Android Debug Bridge).',
      '',
      '**Features:**',
      '- List connected devices',
      '- View device screen (screen mirroring)',
      '- Send touch events and text input',
      '- Manage notifications',
      '- Voice commands to device',
      '- Remote control interface',
      '',
      'Requires ADB to be installed and device to be in developer mode.',
    ],
  },
  {
    id: 'whatsapp',
    label: 'WhatsApp',
    icon: MessageSquare,
    content: [
      '# WhatsApp Integration',
      'Send and receive WhatsApp messages, manage business accounts.',
      '',
      '**WhatsApp Messenger:**',
      '- Send text messages to any number',
      '- View message history',
      '- Template message support',
      '',
      '**WhatsApp Business:**',
      '- Business profile management',
      '- Automated replies',
      '- Broadcast messaging',
      '- Analytics and reporting',
    ],
  },
  {
    id: 'automation',
    label: 'Automation',
    icon: Activity,
    content: [
      '# Automation Engine',
      'Create and run automated workflows. The automation engine supports multi-step tasks with error recovery (self-healing).',
      '',
      '**Features:**',
      '- Visual flow builder (see Visual Agents)',
      '- Self-healing: automatic retry with alternative strategies',
      '- Scheduled execution',
      '- Event-driven triggers',
      '- Pipeline builder for sequential tasks',
    ],
  },
  {
    id: 'voice',
    label: 'Voice Assistant',
    icon: Bot,
    content: [
      '# Voice Assistant (Jarvis)',
      'Lumina includes a hands-free voice assistant with wake-word detection.',
      '',
      '**Features:**',
      '- Wake-word activation ("Hey Lumina" / configurable)',
      '- Continuous listening mode',
      '- Text-to-speech responses',
      '- Multi-language support (Arabic, English, French, etc.)',
      '- Voice command routing to specific agents',
      '',
      'Configure in Settings → Voice section.',
    ],
  },
  {
    id: 'vision',
    label: 'Vision',
    icon: Eye,
    content: [
      '# Computer Vision',
      'Connect cameras and perform real-time object detection, face recognition, and scene description.',
      '',
      '**Capabilities:**',
      '- Live camera feed (USB/network cameras)',
      '- Object detection with bounding boxes',
      '- Face detection and recognition',
      '- Scene description using AI',
      '- Visual memory (remember what was seen)',
      '- Stream recording',
    ],
  },
  {
    id: 'projects',
    label: 'Projects',
    icon: Folder,
    content: [
      '# Projects',
      'Organize your work into projects. Each project can have its own files, agents, tasks, and context.',
      '',
      '**Features:**',
      '- Create and manage multiple projects',
      '- Assign agents to projects',
      '- Track project-specific tasks',
      '- Per-project file storage',
      '- Context-aware AI that remembers project details',
    ],
  },
  {
    id: 'visual-flows',
    label: 'Visual Flows',
    icon: Workflow,
    content: [
      '# Visual Flow Builder',
      'Create automation workflows using a visual drag-and-drop interface.',
      '',
      '**How it works:**',
      '- Connect nodes (triggers, actions, conditions)',
      '- Each node performs a specific operation',
      '- Flows can be saved and scheduled',
      '- Real-time execution monitoring',
      '',
      'Use cases: data pipelines, multi-step automations, conditional branching.',
    ],
  },
  {
    id: 'skills',
    label: 'Skills Catalog',
    icon: Puzzle,
    content: [
      '# Skills Catalog',
      'Skills teach agents how to better use tools. Every skill wraps one or more tools — agents discover them from the catalog and invoke them on demand.',
      '',
      '**57 Built-in Skills across 10 categories:**',
      '',
      '**🌐 Communication & Chat:**',
      '- **WhatsApp Messenger** — Send WhatsApp messages to clients via configured API',
      '- **Multi-Language Chat** — Communicate with clients in their language across chat/WhatsApp/email/voice',
      '- **Email Sender** — Send emails via SMTP',
      '',
      '**🗣️ Language & Voice:**',
      '- **Smart Translator** — Detect language and translate between 100+ languages with optional voice',
      '- **Voice TTS** — Convert text to natural speech in any language',
      '- **Voice STT** — Transcribe audio speech to text in any language',
      '',
      '**🧠 Thinking & Knowledge:**',
      '- **Reading Comprehension** — Read content and answer questions about it',
      '- **Context QA** — Answer questions using reasoning and context understanding in any language',
      '- **Memory Recall** — Search past conversations and learned knowledge',
      '- **Task Planner** — Plan complex tasks into actionable steps',
      '- **Learning Researcher** — Deep research with structured summaries and learning paths',
      '- **Skill Optimizer** — Analyze and optimize skill performance from usage data',
      '',
      '**💻 Development:**',
      '- **Code Generator** — Generate production-ready code in any language with tests',
      '- **Code Reviewer** — Review code for bugs, security issues, and best practices',
      '- **Code Optimizer** — Optimize code for speed, memory, and readability',
      '- **Code Documenter** — Generate docstrings, README, and API docs from code',
      '- **Code Explorer** — Explore/explain code files and directories',
      '- **Shell Command** — Execute shell commands safely',
      '- **Git Ops** — Run Git status, log, diff, branch, remote',
      '- **Database Query** — Execute SQL against SQLite databases',
      '- **PDF Reader** — Extract text from PDF files',
      '- **Dependency Checker** — Check deps for updates, vulnerabilities, and licenses',
      '- **Container Manager** — Manage Docker containers, images, and compose stacks',
      '',
      '**⚡ Automation & Pipelines:**',
      '- **Workflow Automator** — Create multi-step automated workflows with conditions',
      '- **Task Scheduler** — Schedule recurring tasks with cron expressions',
      '- **Data Pipeline** — Build ETL pipelines with extract/transform/load stages',
      '- **File Watcher** — Watch files/directories for changes and trigger actions',
      '- **Webhook Handler** — Register and manage webhooks for event-driven automation',
      '- **API Integrator** — Connect to any REST API with full request handling',
      '- **Data Backup** — Backup/restore files, databases, configs with scheduling',
      '- **Report Generator** — Generate formatted reports in PDF, HTML, Markdown, CSV',
      '',
      '**🧪 Testing & QA:**',
      '- **Automated Tester** — Run test suites and generate detailed reports',
      '- **Test Generator** — Generate unit tests, integration tests, and test cases',
      '',
      '**📢 Marketing & Comms:**',
      '- **Social Auto-Poster** — Schedule and auto-post to Twitter, LinkedIn, Facebook, etc',
      '- **Email Automation** — Create automated email campaigns with follow-ups',
      '',
      '**🔧 Utilities:**',
      '- **Web Search** — Search the web for current info',
      '- **Web Scraper** — Fetch and extract web page content',
      '- **File Manager** — Create/copy/move/delete files and folders',
      '- **Calculator** — Evaluate math expressions safely',
      '- **Unit Converter** — Convert between measurement units',
      '- **Date & Time** — Timezone conversion and date math',
      '- **Password Generator** — Generate strong random passwords',
      '- **QR Generator** — Generate QR code images',
      '- **URL Shortener** — Shorten URLs via TinyURL',
      '- **Random Generator** — Numbers, UUIDs, dice, coin flips',
      '',
      '**📊 Data & Analytics:**',
      '- **Data Analyzer** — Analyze JSON, CSV, or tabular data',
      '- **System Info** — Get OS, CPU, memory, disk details',
      '- **Summarizer** — Condense long text into bullet points',
      '- **Notes Manager** — Save/search/manage personal notes',
      '- **Idea Generator** — Creative ideas and suggestions',
      '',
      '**🌍 Information:**',
      '- **Weather** — Current conditions for any city',
      '- **News** — Latest headlines by topic or country',
      '- **Crypto Price** — Cryptocurrency prices and 24h changes',
      '- **IP Info** — Public IP and geolocation data',
      '',
      '**🎨 Design & Fun:**',
      '- **Color Helper** — Convert colors between hex/RGB/HSL',
      '- **Lorem Ipsum** — Placeholder text for designs',
      '- **Translator** — Basic text translation',
      '',
      '**🌍 Community Skills (skills.sh):**',
      '- Browse 20+ popular skill repos from the skills.sh ecosystem',
      '- **Import** — Download and install community skills with one click',
      '- **Remove** — Uninstall imported skills cleanly',
      '- **Upgrade** — Re-import skills to get the latest version',
      '- Sources include: mattpocock/skills, anthropics/skills, vercel-labs/agent-skills,',
      '  microsoft/azure-skills, obra/superpowers, firebase/agent-skills, and more',
      '- Browse available skills in the Skills & Presets → Community tab',
    ],
  },
  {
    id: 'presets',
    label: 'Agent Presets',
    icon: Zap,
    content: [
      '# Agent Presets',
      'Pre-configured agent profiles for common use cases. Launch with one click.',
      '',
      '**Available Presets:**',
      '- **Morning Digest** — Daily briefing with weather, news, calendar, tasks',
      '- **Deep Research** — Multi-hop research with citations across web and docs',
      '- **Code Assistant** — Code writing, debugging, review, and architecture',
      '- **Scheduled Monitor** — Watch system resources and report anomalies',
      '- **Simple Chat** — Lightweight conversation, no tools',
      '- **Orchestrator** — Multi-agent delegation to specialized agents',
      '- **Native Coder** — CodeAct-style Python code generation and execution',
      '- **Social Media Manager** — Plan and schedule social media content',
      '',
      'Each preset comes with a custom system prompt and tool set optimized for its purpose.',
    ],
  },
  {
    id: 'connectors',
    label: 'Connectors',
    icon: Globe,
    content: [
      '# Connectors',
      'Connect Lumina to your external services via OAuth for data access and automation.',
      '',
      '**Available Connectors:**',
      '- **Gmail** — Read and send emails',
      '- **Google Calendar** — View and manage calendar events',
      '- **Google Tasks** — Manage task lists',
      '- **Google Drive** — Access and search files',
      '- **Outlook** — Microsoft email and calendar',
      '- **Slack** — Send messages and monitor channels',
      '- **GitHub** — Manage repos, issues, and PRs',
      '- **Notion** — Access notes, databases, and pages',
      '- **Linear** — Project management and issue tracking',
      '- **Spotify** — Control playback and manage playlists',
      '',
      'Connect/disconnect from the Skills & Presets page. Data fetching uses OAuth tokens.',
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Shield,
    content: [
      '# Settings & Configuration',
      'Configure Lumina to your preferences.',
      '',
      '**Available Settings:**',
      '- AI Provider — Choose OpenAI, Anthropic, Google, Ollama, etc.',
      '- API Keys management',
      '- Voice settings (wake word, language, TTS voice)',
      '- Theme customization',
      '- User management & permissions',
      '- Data Vault encryption settings',
      '- Notification preferences',
    ],
  },
  {
    id: 'shortcuts',
    label: 'Keyboard Shortcuts',
    icon: Terminal,
    content: [
      '# Keyboard Shortcuts',
      '',
      '**Global:**',
      '- `Ctrl+T` — New Tab',
      '- `Ctrl+W` — Close Tab',
      '- `Ctrl+B` — Toggle Sidebar',
      '- `F11` — Full Screen',
      '',
      '**Code & Agents:**',
      '- `Ctrl+R` — Run Agent',
      '- `Ctrl+G` — Generate Code',
      '- `Ctrl+H` — Heal Task',
      '',
      '**CRM:**',
      '- `Ctrl+Shift+C` — New CRM Contact',
      '- `Ctrl+Shift+D` — New Deal',
      '',
      '**SEO & Browser:**',
      '- `Ctrl+Shift+S` — Analyze SEO',
      '- `Ctrl+Shift+B` — Browser Screenshot',
      '',
      '**Editing:**',
      '- `Ctrl+Z` — Undo',
      '- `Ctrl+Shift+Z` — Redo',
      '- `Ctrl+X` — Cut',
      '- `Ctrl+C` — Copy',
      '- `Ctrl+V` — Paste',
    ],
  },
];

export default function Help() {
  const [search, setSearch] = useState('');
  const [activeSection, setActiveSection] = useState('overview');

  const filtered = sections.filter(s =>
    !search || s.label.toLowerCase().includes(search.toLowerCase()) ||
    s.content.join(' ').toLowerCase().includes(search.toLowerCase())
  );

  const current = sections.find(s => s.id === activeSection) || sections[0];

  return (
    <div className="flex h-full gap-0">
      <aside className="w-56 shrink-0 border-r border-white/5 overflow-y-auto p-2 space-y-0.5 bg-slate-900/20">
        <div className="relative mb-3">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
          <input value={search} onChange={e => setSearch(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-lumina-500/50"
            placeholder="Search help..." />
        </div>
        {filtered.map(s => (
          <button key={s.id} onClick={() => setActiveSection(s.id)}
            className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-all text-left ${
              activeSection === s.id
                ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
            }`}>
            <s.icon className="w-4 h-4 shrink-0" />
            <span className="truncate">{s.label}</span>
          </button>
        ))}
      </aside>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center gap-3 mb-6">
            <BookOpen className="w-6 h-6 text-lumina-400" />
            <div>
              <h1 className="text-xl font-bold text-white">Help & Documentation</h1>
              <p className="text-xs text-slate-500">Complete guide to Lumina AI OS features</p>
            </div>
          </div>

          {filtered.length === 0 ? (
            <div className="text-center py-16">
              <Search className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-500">No results for "{search}"</p>
            </div>
          ) : (
            <div className="bento-card">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
                <current.icon className="w-5 h-5 text-lumina-400" />
                <h2 className="text-lg font-semibold text-white">{current.label}</h2>
              </div>
              <div className="prose prose-invert prose-sm max-w-none">
                {current.content.map((line, i) => {
                  if (line.startsWith('# ')) {
                    return <h1 key={i} className="text-xl font-bold text-white mt-0 mb-3">{line.slice(2)}</h1>;
                  }
                  if (line.startsWith('## ')) {
                    return <h2 key={i} className="text-base font-semibold text-lumina-300 mt-4 mb-2">{line.slice(3)}</h2>;
                  }
                  if (line.startsWith('**') && line.endsWith('**')) {
                    return <p key={i} className="text-sm font-semibold text-slate-200 mt-3 mb-1">{line.slice(2, -2)}</p>;
                  }
                  if (line.startsWith('- ')) {
                    return <li key={i} className="text-sm text-slate-400 ml-4 list-disc">{line.slice(2)}</li>;
                  }
                  if (line.startsWith('  ') && line.trim()) {
                    return <li key={i} className="text-sm text-slate-500 ml-8 list-circle">{line.trim()}</li>;
                  }
                  if (line === '') {
                    return <div key={i} className="h-2" />;
                  }
                  return <p key={i} className="text-sm text-slate-400">{line}</p>;
                })}
              </div>
            </div>
          )}

          <div className="mt-8 text-center">
            <p className="text-xs text-slate-600">
              Lumina AI OS v1.0.0 —{' '}
              <a href="https://alasarjadeed.com" target="_blank" rel="noopener noreferrer"
                className="text-lumina-400 hover:text-lumina-300 underline underline-offset-2">
                AL ASAR JADEED
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
