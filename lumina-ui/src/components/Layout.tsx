import { useState, useCallback } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, MessageSquare, Code2,   Bot, Settings,
  BarChart3, Globe, Folder, Search, Smartphone, MessageSquare as WhatsAppIcon,
  Activity, FileText, Shield, Store, Menu, X, Home, ExternalLink, Cpu,
  User, Bell, ChevronRight, PenTool, Brain, Bug, Camera, Monitor, GitBranch, Crown,
} from 'lucide-react';
import { useToast } from '../hooks/useToast';

const navSections = [
  {
    label: 'Core',
    links: [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard },
      { to: '/assistant', label: 'Assistant', icon: Bot },
      { to: '/chat', label: 'Chat', icon: MessageSquare },
      { to: '/code', label: 'Code Gen', icon: Code2 },
      { to: '/code/review', label: 'Code Review', icon: FileText },
      { to: '/coding-agent', label: 'Coding Agent', icon: GitBranch },
      { to: '/agents', label: 'Agents', icon: Bot },
      { to: '/multi-agent', label: 'Multi-Agent', icon: Crown },
      { to: '/projects', label: 'Projects', icon: Folder },
      { to: '/visual-flows', label: 'Visual Agents', icon: GitBranch },
    ],
  },
  {
    label: 'Business',
    links: [
      { to: '/crm', label: 'CRM', icon: BarChart3 },
      { to: '/seo', label: 'SEO', icon: Search },
      { to: '/social', label: 'Social Media', icon: Globe },
      { to: '/learning', label: 'Learning', icon: Brain },
      { to: '/tester', label: 'Self Tester', icon: Bug },
      { to: '/employee', label: 'AI Employee', icon: Bot },
      { to: '/automation', label: 'Automation', icon: Activity },
    ],
  },
  {
    label: 'Tools',
    links: [
      { to: '/desktop', label: 'Desktop', icon: Monitor },
      { to: '/browser/agent', label: 'Browser Agent', icon: Bot },
      { to: '/files', label: 'Files', icon: Folder },
      { to: '/vision', label: 'Vision', icon: Camera },
      { to: '/android', label: 'Android', icon: Smartphone },
      { to: '/writer', label: 'AI Writer', icon: PenTool },
      { to: '/whatsapp', label: 'WhatsApp', icon: WhatsAppIcon },
      { to: '/whatsapp/business', label: 'WA Business', icon: Store },
    ],
  },
  {
    label: 'System',
    links: [
      { to: '/users', label: 'Users', icon: User },
      { to: '/vault', label: 'Data Vault', icon: Shield },
      { to: '/settings', label: 'Settings', icon: Settings },
    ],
  },
];

const menuItems = [
  {
    label: 'File', items: [
      { label: 'New Tab', shortcut: 'Ctrl+T' },
      { label: 'Open File...', shortcut: 'Ctrl+O' },
      { label: 'Save', shortcut: 'Ctrl+S' },
      { label: 'Export', shortcut: 'Ctrl+E' },
      { type: 'separator' },
      { label: 'Exit', shortcut: 'Alt+F4' },
    ],
  },
  {
    label: 'Edit', items: [
      { label: 'Undo', shortcut: 'Ctrl+Z' },
      { label: 'Redo', shortcut: 'Ctrl+Shift+Z' },
      { type: 'separator' },
      { label: 'Cut', shortcut: 'Ctrl+X' },
      { label: 'Copy', shortcut: 'Ctrl+C' },
      { label: 'Paste', shortcut: 'Ctrl+V' },
    ],
  },
  {
    label: 'View', items: [
      { label: 'Toggle Sidebar', shortcut: 'Ctrl+B' },
      { label: 'Full Screen', shortcut: 'F11' },
      { type: 'separator' },
      { label: 'Dark Mode' },
    ],
  },
  {
    label: 'Action', items: [
      { label: 'Run Agent', shortcut: 'Ctrl+R' },
      { label: 'Generate Code', shortcut: 'Ctrl+G' },
      { label: 'Heal Task', shortcut: 'Ctrl+H' },
      { type: 'separator' },
      { label: 'New CRM Contact', shortcut: 'Ctrl+Shift+C' },
      { label: 'New Deal', shortcut: 'Ctrl+Shift+D' },
      { type: 'separator' },
      { label: 'Analyze SEO', shortcut: 'Ctrl+Shift+S' },
      { label: 'Browser Screenshot', shortcut: 'Ctrl+Shift+B' },
    ],
  },
  {
    label: 'Tools', items: [
      { label: 'Browser Console' },
      { label: 'API Reference' },
      { label: 'Plugin Manager' },
    ],
  },
  {
    label: 'Help', items: [
      { label: 'Documentation', shortcut: 'F1' },
      { label: 'About Lumina' },
    ],
  },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [tabs, setTabs] = useState([{ id: 'home', label: 'Dashboard', path: '/' }]);
  const [activeTab, setActiveTab] = useState('home');
  const [showBrowser, setShowBrowser] = useState(false);
  const [browserUrl, setBrowserUrl] = useState('https://www.google.com');
  const [browserInput, setBrowserInput] = useState('https://www.google.com');
  const [browserLoading, setBrowserLoading] = useState(false);
  const [browserKey, setBrowserKey] = useState(0);
  const [browserHtml, setBrowserHtml] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const currentSubTabs = Object.entries({
    '/code': [
      { label: 'Generate', path: '/code' },
      { label: 'Review', path: '/code/review' },
    ],
    '/crm': [
      { label: 'Overview', path: '/crm' },
      { label: 'Contacts', path: '/crm?tab=contacts' },
      { label: 'Deals', path: '/crm?tab=deals' },
    ],
  } as Record<string, { label: string; path: string }[]>).find(([key]) =>
    location.pathname.startsWith(key)
  )?.[1];

  const navigateBrowser = useCallback(async (url: string) => {
    let finalUrl = url.trim();
    if (!finalUrl) return;
    if (!finalUrl.match(/^https?:\/\//)) finalUrl = `https://${finalUrl}`;
    setBrowserUrl(finalUrl);
    setBrowserInput(finalUrl);
    setBrowserLoading(true);
    setBrowserHtml(`<div style="padding:40px;text-align:center;color:#666">Loading ${finalUrl}...</div>`);
    try {
      await fetch('/api/browser/navigate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({url: finalUrl}) });
      const contentRes = await fetch('/api/browser/content');
      const data = await contentRes.json();
      let content = data.html || data.text || '';
      if (!content) {
        setBrowserHtml(`<div style="padding:40px;color:red">Empty response from server</div>`);
        return;
      }
      const base = finalUrl.replace(/\/$/, '');
      content = content.replace(/(src|href)="\/(?!\/)/g, `$1="${base}/`);
      content = content.replace(/(src|href)='\/(?!\/)/g, `$1='${base}/`);
      content = content.replace(/<meta[^>]*http-equiv=["']Content-Security-Policy["'][^>]*>/gi, '');
      setBrowserHtml(content);
    } catch {
      setBrowserHtml(`<div style="padding:40px;color:red">Browser error</div>`);
    }
    setBrowserLoading(false);
  }, []);

  const openBrowser = () => {
    setShowBrowser(true);
    navigateBrowser(browserUrl || 'https://www.google.com');
  };

  const pageTitle = location.pathname === '/' ? 'Dashboard'
    : location.pathname.split('/').filter(Boolean).map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' / ');

  const addTab = (label: string, path: string) => {
    const id = path;
    if (!tabs.find(t => t.id === id)) {
      setTabs([...tabs, { id, label, path }]);
    }
    setActiveTab(id);
    navigate(path);
  };

  const toggleSidebar = () => setSidebarCollapsed(prev => !prev);

  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-200 select-none">
      <div className="flex items-center h-9 bg-slate-900 border-b border-white/5 px-2 shrink-0 relative z-50">
        <div className="flex items-center gap-1 mr-4">
          <div className="w-5 h-5 rounded bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center mr-2">
            <Cpu className="w-3 h-3 text-white" />
          </div>
          <span className="text-xs font-semibold text-white/80">Lumina</span>
        </div>
        {menuItems.map(menu => (
          <div key={menu.label} className="relative" onMouseLeave={() => setActiveMenu(null)}>
            <button
              onMouseEnter={() => setActiveMenu(menu.label)}
              onClick={() => setActiveMenu(activeMenu === menu.label ? null : menu.label)}
              className={`px-3 py-1 text-xs rounded transition-colors ${
                activeMenu === menu.label ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
            >
              {menu.label}
            </button>
            {activeMenu === menu.label && (
              <div className="absolute top-full left-0 mt-0.5 w-52 bg-slate-900 border border-white/10 rounded-lg shadow-2xl py-1 z-50">
                {menu.items.map((item: any, i: number) =>
                  item.type === 'separator' ? (
                    <div key={i} className="h-px bg-white/5 my-1" />
                  ) : (
                    <button key={i} onClick={() => { setActiveMenu(null); addToast(`${item.label} action`, 'info'); }}
                      className="w-full flex items-center justify-between px-4 py-1.5 text-xs text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                    >
                      <span>{item.label}</span>
                      {item.shortcut && <span className="text-slate-600 text-[10px]">{item.shortcut}</span>}
                    </button>
                  )
                )}
              </div>
            )}
          </div>
        ))}
        <div className="ml-auto flex items-center gap-2">
          <button onClick={openBrowser}
            className="px-2 py-1 text-xs text-slate-400 hover:text-slate-200 hover:bg-white/5 rounded transition-colors flex items-center gap-1">
            <ExternalLink className="w-3 h-3" /> Browser
          </button>
          <button className="p-1 text-slate-400 hover:text-slate-200 hover:bg-white/5 rounded transition-colors relative">
            <Bell className="w-3.5 h-3.5" />
            <span className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-lumina-500 rounded-full" />
          </button>
        </div>
      </div>

      <div className="flex items-center h-8 bg-slate-900/50 border-b border-white/5 px-3 gap-2 shrink-0">
        <button onClick={toggleSidebar}
          className="p-1 rounded hover:bg-white/5 text-slate-400 hover:text-slate-200 transition-colors">
          <Menu className="w-3.5 h-3.5" />
        </button>
        <div className="w-px h-4 bg-white/5" />
        <div className="flex items-center gap-1 text-xs text-slate-500 min-w-0">
          <Home className="w-3 h-3 shrink-0" />
          <ChevronRight className="w-2.5 h-2.5 shrink-0" />
          <span className="text-slate-300 truncate">{pageTitle}</span>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <div className="flex items-center gap-1 bg-white/5 rounded-md px-2 py-0.5 focus-within:bg-white/10 transition-colors">
            <Search className="w-3 h-3 text-slate-500 shrink-0" />
            <input
              className="w-40 bg-transparent text-xs text-slate-300 placeholder-slate-600 outline-none"
              placeholder="Search..."
              onKeyDown={e => e.key === 'Enter' && addToast(`Search: ${(e.target as HTMLInputElement).value}`, 'info')}
            />
          </div>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        <aside className={`flex flex-col bg-slate-900/30 border-r border-white/5 transition-all duration-200 ease-out ${sidebarCollapsed ? 'w-12' : 'w-52'}`}>
          {!sidebarCollapsed && tabs.length > 0 && (
            <div className="flex items-center gap-0.5 px-2 py-1.5 border-b border-white/5 shrink-0 overflow-x-auto">
              {tabs.map(tab => (
                <button key={tab.id} onClick={() => { setActiveTab(tab.id); navigate(tab.path); }}
                  className={`flex items-center gap-1 px-2 py-1 text-[10px] rounded transition-colors whitespace-nowrap ${
                    activeTab === tab.id ? 'bg-lumina-600/15 text-lumina-300' : 'text-slate-500 hover:text-slate-300'
                  }`}>
                  {tab.label}
                </button>
              ))}
            </div>
          )}
          {sidebarCollapsed && tabs.length > 0 && (
            <div className="flex flex-col items-center gap-0.5 py-1.5 border-b border-white/5 shrink-0">
              {tabs.map(tab => (
                <button key={tab.id} onClick={() => { setActiveTab(tab.id); navigate(tab.path); }}
                  className={`w-6 h-6 flex items-center justify-center text-[10px] rounded transition-colors ${
                    activeTab === tab.id ? 'bg-lumina-600/15 text-lumina-300' : 'text-slate-500 hover:text-slate-300'
                  }`}
                  title={tab.label}>
                  {tab.label.charAt(0)}
                </button>
              ))}
            </div>
          )}

          <nav className="flex-1 overflow-y-auto p-1.5 space-y-2 scroll-smooth">
            {navSections.map(section => (
              <div key={section.label}>
                {!sidebarCollapsed && (
                  <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider px-2 py-1">{section.label}</p>
                )}
                {section.links.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to} to={to} end={to === '/'}
                    onClick={() => addTab(label, to)}
                    className={({ isActive }) =>
                      `flex items-center gap-2.5 px-2 py-1.5 rounded-lg text-xs transition-all duration-150 ${
                        isActive
                          ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
                      }`
                    }
                  >
                    <Icon className="w-4 h-4 shrink-0" />
                    {!sidebarCollapsed && <span className="truncate">{label}</span>}
                  </NavLink>
                ))}
              </div>
            ))}
          </nav>
        </aside>

        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center gap-0.5 px-2 py-1 bg-slate-900/40 border-b border-white/5 shrink-0 overflow-x-auto">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => { setActiveTab(tab.id); navigate(tab.path); }}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-t transition-colors whitespace-nowrap shrink-0 ${
                  activeTab === tab.id
                    ? 'bg-white/5 text-lumina-300 border-t border-lumina-500/30'
                    : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.03]'
                }`}>
                {tab.label}
                <span onClick={(e) => { e.stopPropagation(); setTabs(tabs.filter(t => t.id !== tab.id)); if (activeTab === tab.id && tabs.length > 1) { const next = tabs.find(t => t.id !== tab.id); if (next) { setActiveTab(next.id); navigate(next.path); } } else if (tabs.length === 1) { navigate('/'); setTabs([{ id: 'home', label: 'Dashboard', path: '/' }]); setActiveTab('home'); } }}
                  className="ml-1 p-0.5 rounded hover:bg-white/10 hover:text-white transition-colors cursor-pointer">
                  <X className="w-3 h-3" />
                </span>
              </button>
            ))}
          </div>

          {currentSubTabs && (
            <div className="flex items-center gap-1 px-3 py-1 bg-slate-900/20 border-b border-white/5 shrink-0">
              {currentSubTabs.map(st => (
                <button key={st.path} onClick={() => navigate(st.path)}
                  className={`px-3 py-1 text-xs rounded-md transition-colors ${
                    location.pathname + location.search === st.path || (st.path === '/crm' && location.pathname === '/crm' && !location.search)
                      ? 'bg-white/10 text-lumina-300' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                  }`}>
                  {st.label}
                </button>
              ))}
            </div>
          )}

          <div className="flex-1 overflow-auto">
            {children}
          </div>
        </div>
      </div>

      <div className="flex items-center h-7 bg-slate-900 border-t border-white/5 px-3 text-[10px] text-slate-500 shrink-0">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/30" />
            System Online
          </span>
          <span className="w-px h-3 bg-white/5" />
          <span>v1.0.0</span>
        </div>
        <div className="ml-auto flex items-center gap-3">
          <span className="flex items-center gap-1 text-slate-400"><Activity className="w-3 h-3" /> 19 services</span>
        </div>
      </div>

      {showBrowser && (
        <div className="fixed inset-0 z-50 flex flex-col bg-slate-950 animate-fade-in">
          <div className="flex items-center h-12 bg-slate-900 border-b border-white/10 px-3 gap-3 shrink-0">
            <button onClick={() => setShowBrowser(false)}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors">
              <X className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-3 flex-1 max-w-3xl mx-auto bg-white/10 rounded-xl px-4 py-2 border border-white/10 focus-within:border-lumina-500/50 transition-all">
              <Globe className="w-4 h-4 text-slate-400 shrink-0" />
              <input
                className="flex-1 bg-transparent text-sm text-white outline-none placeholder-slate-500"
                value={browserInput}
                onChange={e => setBrowserInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && navigateBrowser((e.target as HTMLInputElement).value)}
                placeholder="Search Google or enter a URL..."
              />
              {browserLoading ? (
                <div className="w-4 h-4 border-2 border-lumina-400 rounded-full animate-spin" style={{ borderTopColor: 'transparent' }} />
              ) : (
                <button onClick={() => navigateBrowser(browserInput)}
                  className="text-xs font-medium text-lumina-400 hover:text-lumina-300 shrink-0">
                  Go
                </button>
              )}
            </div>
            <button onClick={() => setBrowserKey(k => k + 1)}
              className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors" title="Reload">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
              </svg>
            </button>
          </div>
          <div className="flex-1 flex min-h-0 bg-white relative">
            {browserHtml ? (
              <iframe
                key={browserKey}
                srcDoc={browserHtml}
                className="flex-1 w-full h-full"
                title="Browser"
                sandbox="allow-scripts allow-popups"
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center bg-white text-slate-400 text-sm">
                {browserLoading ? 'Loading...' : 'Enter a URL above to start browsing'}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
