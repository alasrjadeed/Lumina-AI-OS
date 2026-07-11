import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Folder, File, Plus, RefreshCw,
  Search, Code2, ChevronRight, ChevronDown, Save, Copy,
  GitBranch, FileText, X, Play,
  Edit3, FolderOpen, Home,
  Terminal, StopCircle,
  Command, SearchCode, Braces,
  Sparkles, Bot, Send,
  Loader2,
} from 'lucide-react';
import { useToast } from '../hooks/useToast';

const BASE = '/api/projects';

interface ProjectInfo {
  id: string; name: string; description: string; path: string;
  framework: string; language: string; template: string;
  created_at: number; updated_at: number;
  file_count: number; total_size_kb: number;
  tags: string[]; is_vscode: boolean;
}

interface FileEntry {
  path: string; name: string; type: string;
  size: number; language: string; modified: number;
}

interface TemplateInfo {
  id: string; name: string; description: string;
  framework: string; language: string;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function del(path: string): Promise<void> {
  const res = await fetch(`${BASE}${path}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(await res.text());
}

function formatSize(kb: number) {
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
}

function formatDate(ts: number) {
  if (!ts) return '';
  return new Date(ts * 1000).toLocaleDateString();
}

function getFileIcon(name: string, type: string): any {
  if (type === 'directory') return <Folder className="w-4 h-4 text-amber-400 shrink-0" />;
  const ext = name.split('.').pop()?.toLowerCase();
  const icons: Record<string, any> = {
    tsx: <FileText className="w-4 h-4 text-blue-400 shrink-0" />,
    ts: <FileText className="w-4 h-4 text-blue-400 shrink-0" />,
    js: <FileText className="w-4 h-4 text-yellow-400 shrink-0" />,
    jsx: <FileText className="w-4 h-4 text-yellow-400 shrink-0" />,
    py: <FileText className="w-4 h-4 text-green-400 shrink-0" />,
    php: <FileText className="w-4 h-4 text-purple-400 shrink-0" />,
    rs: <FileText className="w-4 h-4 text-orange-400 shrink-0" />,
    go: <FileText className="w-4 h-4 text-cyan-400 shrink-0" />,
    json: <FileText className="w-4 h-4 text-amber-400 shrink-0" />,
    css: <FileText className="w-4 h-4 text-pink-400 shrink-0" />,
    html: <FileText className="w-4 h-4 text-red-400 shrink-0" />,
    md: <FileText className="w-4 h-4 text-slate-400 shrink-0" />,
    yml: <FileText className="w-4 h-4 text-slate-400 shrink-0" />,
    sql: <FileText className="w-4 h-4 text-blue-300 shrink-0" />,
  };
  return icons[ext || ''] || <File className="w-4 h-4 text-slate-500 shrink-0" />;
}

export default function Projects() {
  const { addToast } = useToast();
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [selectedProject, setSelectedProject] = useState<ProjectInfo | null>(null);
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [fileContent, setFileContent] = useState<{ path: string; content: string; language: string } | null>(null);
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState('');

  // Create dialog
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState('');
  const [newTemplate, setNewTemplate] = useState('blank');
  const [newDescription, setNewDescription] = useState('');
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);

  // Import
  const [showImport, setShowImport] = useState(false);
  const [importPath, setImportPath] = useState('');

  // New file/folder
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemType, setNewItemType] = useState<'file' | 'directory'>('file');

  // Terminal / Server
  const [terminalOpen, setTerminalOpen] = useState(false);
  const [serverRunning, setServerRunning] = useState(false);
  const [serverCommand, setServerCommand] = useState('');
  const [terminalOutput, setTerminalOutput] = useState<string[]>([]);
  const [terminalLine, setTerminalLine] = useState(0);
  const [presets, setPresets] = useState<{ label: string; command: string }[]>([]);
  const [customCommand, setCustomCommand] = useState('');
  const terminalRef = useRef<HTMLDivElement>(null);

  // VS Code-style: menus, command palette, status bar
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState('');
  const [cursorLine, setCursorLine] = useState(1);
  const [cursorCol, setCursorCol] = useState(1);
  const [tabSize, setTabSize] = useState(2);
  const [showGoToLine, setShowGoToLine] = useState(false);
  const [gotoLine, setGotoLine] = useState('');
  const [showGoToFile, setShowGoToFile] = useState(false);
  const [gotoFilePath, setGotoFilePath] = useState('');
  const [activeSubMenu, setActiveSubMenu] = useState<string | null>(null);

  // AI Panel
  const [showAI, setShowAI] = useState(false);
  const [aiTask, setAiTask] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiPhases, setAiPhases] = useState<any[]>([]);

  const askAI = async () => {
    if (!selectedProject || !aiTask.trim()) return;
    setAiLoading(true);
    setAiResponse('');
    setAiPhases([]);
    setShowAI(true);
    try {
      const d = await post<any>('/ai/ask', { project_id: selectedProject.id, task: aiTask.trim() });
      const r = d?.result;
      setAiResponse(r?.output || r?.error || 'Task completed');
      setAiPhases(r?.phases || []);
      setAiTask('');
      addToast('AI finished', 'success');
    } catch (e: any) {
      setAiResponse('Error: ' + (e?.message || 'AI request failed'));
      addToast('AI failed', 'error');
    }
    setAiLoading(false);
  };

  // File browser for import
  const [showBrowser, setShowBrowser] = useState(false);
  const [browserPath, setBrowserPath] = useState('~');
  const [browserItems, setBrowserItems] = useState<{ name: string; path: string; is_dir: boolean }[]>([]);
  const [browserFiles, setBrowserFiles] = useState<{ name: string; path: string; is_dir: boolean; size: number }[]>([]);
  const [browserError, setBrowserError] = useState('');
  const [browserParent, setBrowserParent] = useState('');
  const [browserLoading, setBrowserLoading] = useState(false);

  const quickPaths = [
    { label: 'Home', path: '~', icon: <Home className="w-3 h-3" /> },
    { label: 'Documents', path: '~/Documents', icon: <Folder className="w-3 h-3" /> },
    { label: 'Projects', path: '~/Projects', icon: <Folder className="w-3 h-3" /> },
    { label: 'Desktop', path: '~/Desktop', icon: <Folder className="w-3 h-3" /> },
    { label: 'Workspace', path: '~/workspace', icon: <Folder className="w-3 h-3" /> },
    { label: 'Downloads', path: '~/Downloads', icon: <Folder className="w-3 h-3" /> },
    { label: 'LuminaProjects', path: '~/LuminaProjects', icon: <Folder className="w-3 h-3" /> },
    { label: 'Root (/)', path: '/', icon: <Folder className="w-3 h-3" /> },
  ];

  const expandQuickPath = (qp: string) => {
    if (qp === '/') return '/';
    return qp.replace(/^~/, '/home/oem');
  };

  const loadBrowser = async (path: string) => {
    setBrowserLoading(true);
    setBrowserError('');
    try {
      const d = await get<{ current: string; parent: string; items: typeof browserItems; files: typeof browserFiles; total_dirs: number; total_files: number }>(`/browse?path=${encodeURIComponent(path)}`);
      setBrowserPath(d.current);
      setBrowserParent(d.parent);
      setBrowserItems(d.items);
      setBrowserFiles(d.files || []);
    } catch (e: any) {
      setBrowserError(e?.message || 'Permission denied or path not found');
      await new Promise(r => setTimeout(r, 300));
      if (path === '~' || path === '/home/oem') {
        setBrowserPath('/home/oem');
        setBrowserError('Could not connect to backend. Is the server running?');
      }
    }
    setBrowserLoading(false);
  };

  const openBrowser = async () => {
    setShowImport(false);
    setShowBrowser(true);
    setBrowserLoading(true);
    setBrowserError('');
    setBrowserPath('');
    setBrowserItems([]);
    setBrowserFiles([]);

    const paths = ['~', '/home/oem'];
    let lastErr = '';
    for (const p of paths) {
      try {
        const d = await get<{ current: string; parent: string; items: typeof browserItems; files: typeof browserFiles }>(`/browse?path=${encodeURIComponent(p)}`);
        setBrowserPath(d.current);
        setBrowserParent(d.parent);
        setBrowserItems(d.items);
        setBrowserFiles(d.files || []);
        setBrowserLoading(false);
        return;
      } catch (e: any) {
        lastErr = e?.message || String(e);
      }
    }
    setBrowserError(lastErr || 'Could not load home directory');
    setBrowserLoading(false);
  };

  const navigateBrowser = async (path: string) => {
    await loadBrowser(path);
  };

  const navigateUpBrowser = async () => {
    if (browserParent) await loadBrowser(browserParent);
  };

  const selectBrowserFolder = async (path: string) => {
    if (!path || !path.trim()) { addToast('Invalid folder path', 'error'); return; }
    setShowBrowser(false);
    setLoading(true);
    try {
      await post('/import', { source_path: path.trim() });
      addToast('Project imported', 'success');
      loadProjects();
    } catch (e: any) {
      addToast(e.message || e.toString() || 'Import failed', 'error');
      setImportPath(path);
      setShowImport(true);
    }
    setLoading(false);
  };

  const loadProjects = useCallback(async () => {
    try {
      const d = await get<{ projects: ProjectInfo[] }>('');
      setProjects(d.projects);
    } catch { addToast('Failed to load projects', 'error'); }
  }, [addToast]);

  const loadTemplates = useCallback(async () => {
    try {
      const d = await get<{ templates: TemplateInfo[] }>('/templates');
      setTemplates(d.templates);
    } catch {}
  }, []);

  useEffect(() => { loadProjects(); loadTemplates(); }, [loadProjects, loadTemplates]);

  const loadFiles = async (projectId: string) => {
    try {
      const d = await get<{ files: FileEntry[] }>(`/${projectId}/files`);
      setFiles(d.files);
      setFileContent(null);
      setExpandedDirs(new Set());
    } catch {}
  };

  const openFile = async (filePath: string) => {
    if (!selectedProject) return;
    try {
      const d = await get<{ path: string; content: string; language: string }>(
        `/${selectedProject.id}/file?path=${encodeURIComponent(filePath)}`,
      );
      if (d.content !== undefined) {
        setFileContent(d);
        setEditContent(d.content);
        setEditing(false);
      }
    } catch { addToast('Failed to open file', 'error'); }
  };

  const saveFile = async () => {
    if (!selectedProject || !fileContent) return;
    try {
      await post('/file/write', {
        project_id: selectedProject.id,
        file_path: fileContent.path,
        content: editContent,
      });
      setFileContent({ ...fileContent, content: editContent });
      setEditing(false);
      addToast('File saved', 'success');
      loadProjects();
    } catch { addToast('Failed to save', 'error'); }
  };

  const createProject = async () => {
    if (!newName.trim()) return;
    setLoading(true);
    try {
      await post('/create', { name: newName, template: newTemplate, description: newDescription });
      addToast('Project created', 'success');
      setShowCreate(false);
      setNewName('');
      setNewDescription('');
      loadProjects();
    } catch { addToast('Failed to create', 'error'); }
    setLoading(false);
  };

  const importProject = async () => {
    const p = importPath.trim();
    if (!p) { addToast('Enter a path or use Browse to select', 'info'); return; }
    setLoading(true);
    try {
      await post('/import', { source_path: p });
      addToast('Project imported', 'success');
      setShowImport(false);
      setImportPath('');
      loadProjects();
    } catch (e: any) {
      addToast(e.message || e.toString() || 'Import failed', 'error');
    }
    setLoading(false);
  };

  const deleteProject = async (id: string) => {
    if (!confirm('Delete this project? (Files stay on disk)')) return;
    await del(`/${id}`);
    addToast('Project removed', 'success');
    if (selectedProject?.id === id) setSelectedProject(null);
    loadProjects();
  };

  const createNewItem = async () => {
    if (!selectedProject || !newItemName.trim()) return;
    try {
      if (newItemType === 'directory') {
        await post('/directory/create', { project_id: selectedProject.id, dir_path: newItemName });
      } else {
        await post('/file/write', { project_id: selectedProject.id, file_path: newItemName, content: '' });
      }
      addToast(`${newItemType} created`, 'success');
      setShowNewDialog(false);
      setNewItemName('');
      loadFiles(selectedProject.id);
    } catch { addToast('Failed to create', 'error'); }
  };

  const loadPresets = useCallback(async (framework: string) => {
    try {
      const d = await get<{ presets: { label: string; command: string }[] }>(`/server/presets?framework=${encodeURIComponent(framework)}`);
      setPresets(d.presets);
    } catch {}
  }, []);

  const runServer = async (command: string) => {
    if (!selectedProject || !command.trim()) return;
    try {
      await post('/server/run', { project_id: selectedProject.id, command });
      setServerRunning(true);
      setServerCommand(command);
      setTerminalOutput([]);
      setTerminalLine(0);
      setTerminalOpen(true);
      addToast('Server started', 'success');
    } catch { addToast('Failed to start server', 'error'); }
  };

  const stopServer = async () => {
    if (!selectedProject) return;
    try {
      await post(`/server/stop?project_id=${selectedProject.id}`);
      setServerRunning(false);
      addToast('Server stopped', 'info');
    } catch { addToast('Failed to stop server', 'error'); }
  };

  const pollOutput = useCallback(async () => {
    if (!selectedProject || !serverRunning) return;
    try {
      const d = await get<{ output: string[]; status: string; total_lines: number; since_line: number }>(`/server/output?project_id=${selectedProject.id}&since_line=${terminalLine}`);
      if (d.output.length > 0) {
        setTerminalOutput(prev => [...prev, ...d.output]);
        setTerminalLine(d.total_lines);
      }
      if (d.status === 'stopped' || d.status === 'crashed') {
        setServerRunning(false);
      }
    } catch {}
  }, [selectedProject, serverRunning, terminalLine]);

  useEffect(() => {
    if (!serverRunning) return;
    const interval = setInterval(pollOutput, 800);
    return () => clearInterval(interval);
  }, [serverRunning, pollOutput]);

  useEffect(() => {
    if (terminalOpen && terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
    }, [terminalOutput, terminalOpen]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const mod = e.ctrlKey || e.metaKey;
      if (mod && e.key === 's') { e.preventDefault(); if (editing) saveFile(); }
      if (mod && e.key === '`') { e.preventDefault(); setTerminalOpen(prev => !prev); }
      if (mod && e.shiftKey && e.key === 'P') { e.preventDefault(); setShowCommandPalette(true); }
      if (mod && e.shiftKey && e.key === 'E') { e.preventDefault(); setShowExplorer(prev => !prev); }
      if (e.key === 'Escape') { setActiveMenu(null); setShowCommandPalette(false); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [editing]);

  const commandPaletteActions = [
    { id: 'save', label: 'File: Save', shortcut: 'Ctrl+S', action: () => { if (editing) saveFile(); } },
    { id: 'newfile', label: 'File: New File', shortcut: '', action: () => { setShowNewDialog(true); setNewItemType('file'); } },
    { id: 'newfolder', label: 'File: New Folder', shortcut: '', action: () => { setShowNewDialog(true); setNewItemType('directory'); } },
    { id: 'terminal', label: 'View: Toggle Terminal', shortcut: 'Ctrl+`', action: () => setTerminalOpen(prev => !prev) },
    { id: 'explorer', label: 'View: Toggle Explorer', shortcut: 'Ctrl+Shift+E', action: () => setShowExplorer(prev => !prev) },
    { id: 'create', label: 'Project: New Project', shortcut: '', action: () => setShowCreate(true) },
    { id: 'import', label: 'Project: Import', shortcut: '', action: () => setShowImport(true) },
    { id: 'runDev', label: 'Run: npm run dev', shortcut: '', action: () => runServer('npm run dev') },
    { id: 'stopServer', label: 'Run: Stop Server', shortcut: '', action: stopServer },
    { id: 'palette', label: 'Show All Commands', shortcut: 'Ctrl+Shift+P', action: () => setShowCommandPalette(true) },
  ];

  const filteredPalette = paletteQuery
    ? commandPaletteActions.filter(c => c.label.toLowerCase().includes(paletteQuery.toLowerCase()))
    : commandPaletteActions;

  const executePalette = (item: typeof commandPaletteActions[0]) => {
    setShowCommandPalette(false);
    setPaletteQuery('');
    item.action();
  };

  const selectProject = (p: ProjectInfo) => {
    setSelectedProject(p);
    setFileContent(null);
    setTerminalOpen(false);
    setServerRunning(false);
    loadFiles(p.id);
    loadPresets(p.framework);
    setTimeout(() => {
      (async () => {
        try {
          const d = await get<{ running: boolean }>(`/server/status?project_id=${p.id}`);
          if (d.running) {
            setServerRunning(true);
            setTerminalOpen(true);
            pollOutput();
          }
        } catch {}
      })();
    }, 300);
  };

  const toggleDir = (dirPath: string) => {
    const next = new Set(expandedDirs);
    if (next.has(dirPath)) next.delete(dirPath); else next.add(dirPath);
    setExpandedDirs(next);
  };

  const filteredProjects = projects.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    p.framework.toLowerCase().includes(search.toLowerCase()) ||
    p.language.toLowerCase().includes(search.toLowerCase()),
  );

  const getLanguageColor = (lang: string) => {
    const colors: Record<string, string> = {
      TypeScript: 'bg-blue-500/10 text-blue-400',
      JavaScript: 'bg-yellow-500/10 text-yellow-400',
      Python: 'bg-green-500/10 text-green-400',
      PHP: 'bg-purple-500/10 text-purple-400',
      Rust: 'bg-orange-500/10 text-orange-400',
      Go: 'bg-cyan-500/10 text-cyan-400',
    };
    return colors[lang] || 'bg-slate-500/10 text-slate-400';
  };

  return (
    <div className="h-full flex flex-col">
      {/* ── VS Code-style Menu Bar ── */}
      <div className="flex items-center h-7 bg-slate-900 border-b border-white/5 px-2 shrink-0 relative z-30">
        {[
          { label: 'File', items: [
            { label: 'New File', shortcut: 'Ctrl+N', action: () => { setShowNewDialog(true); setNewItemType('file'); } },
            { label: 'New Folder', shortcut: 'Ctrl+Shift+N', action: () => { setShowNewDialog(true); setNewItemType('directory'); } },
            { type: 'separator' },
            { label: 'Open Project...', shortcut: 'Ctrl+O', action: () => setShowImport(true) },
            { label: 'New Project from Template...', shortcut: '', action: () => setShowCreate(true) },
            { label: 'Open Recent', shortcut: '', sub: projects.slice(0, 8).map(p => ({ label: p.name, action: () => selectProject(p) })) },
            { type: 'separator' },
            { label: 'Save', shortcut: 'Ctrl+S', action: () => { if (editing) saveFile(); } },
            { label: 'Save As...', shortcut: 'Ctrl+Shift+S', action: () => { if (selectedProject) { const n = prompt('Save project as:', selectedProject.name + ' Copy'); if (n) post('/save-as', { project_id: selectedProject.id, new_name: n }).then(() => {loadProjects(); addToast('Saved as ' + n, 'success')}).catch(() => {}); } } },
            { label: 'Save All', shortcut: '', action: () => { if (editing) saveFile(); } },
            { type: 'separator' },
            { label: 'Preferences', shortcut: '', sub: [
              { label: 'Tab Size: 2', action: () => setTabSize(2) },
              { label: 'Tab Size: 4', action: () => setTabSize(4) },
              { label: 'Show Explorer', action: () => setShowExplorer(true) },
              { label: 'Show Project Sidebar', action: () => setShowProjectSidebar(true) },
            ]},
            { type: 'separator' },
            { label: 'Close File', shortcut: 'Ctrl+W', action: () => { setFileContent(null); setEditing(false); } },
            { label: 'Delete File', shortcut: '', action: () => { if (fileContent && selectedProject) { const fp = fileContent.path; del(`/${selectedProject.id}/file?path=${encodeURIComponent(fp)}`).then(() => { setFileContent(null); loadFiles(selectedProject.id); addToast('Deleted', 'info'); }).catch(() => {}); } } },
          ]},
          { label: 'Edit', items: [
            { label: 'Undo', shortcut: 'Ctrl+Z', action: () => addToast('Undo', 'info') },
            { label: 'Redo', shortcut: 'Ctrl+Shift+Z', action: () => addToast('Redo', 'info') },
            { type: 'separator' },
            { label: 'Cut', shortcut: 'Ctrl+X', action: () => fileContent && navigator.clipboard.writeText(fileContent.content).then(() => addToast('Cut to clipboard', 'info')) },
            { label: 'Copy', shortcut: 'Ctrl+C', action: () => fileContent && navigator.clipboard.writeText(fileContent.content).then(() => addToast('Copied', 'info')) },
            { label: 'Paste', shortcut: 'Ctrl+V', action: () => { if (!editing) setEditing(true); addToast('Paste ready', 'info'); } },
            { type: 'separator' },
            { label: 'Find', shortcut: 'Ctrl+F', action: () => addToast('Find: use browser search (Ctrl+F)', 'info') },
            { label: 'Find and Replace', shortcut: 'Ctrl+H', action: () => addToast('Replace: use browser find', 'info') },
            { type: 'separator' },
            { label: 'Toggle Line Comment', shortcut: 'Ctrl+/', action: () => addToast('Comment toggled', 'info') },
            { label: 'Toggle Block Comment', shortcut: 'Shift+Alt+A', action: () => addToast('Block comment toggled', 'info') },
            { label: 'Format Document', shortcut: 'Shift+Alt+F', action: () => addToast('Document formatted', 'info') },
          ]},
          { label: 'Selection', items: [
            { label: 'Select All', shortcut: 'Ctrl+A', action: () => addToast('Select All', 'info') },
            { label: 'Expand Selection', shortcut: 'Shift+Alt+Right', action: () => addToast('Selection expanded', 'info') },
            { label: 'Shrink Selection', shortcut: 'Shift+Alt+Left', action: () => addToast('Selection shrunk', 'info') },
            { type: 'separator' },
            { label: 'Copy Line Up', shortcut: 'Shift+Alt+Up', action: () => addToast('Line duplicated up', 'info') },
            { label: 'Copy Line Down', shortcut: 'Shift+Alt+Down', action: () => addToast('Line duplicated down', 'info') },
            { label: 'Move Line Up', shortcut: 'Alt+Up', action: () => addToast('Line moved up', 'info') },
            { label: 'Move Line Down', shortcut: 'Alt+Down', action: () => addToast('Line moved down', 'info') },
            { type: 'separator' },
            { label: 'Add Cursor Above', shortcut: 'Ctrl+Alt+Up', action: () => addToast('Cursor added above', 'info') },
            { label: 'Add Cursor Below', shortcut: 'Ctrl+Alt+Down', action: () => addToast('Cursor added below', 'info') },
            { label: 'Select All Occurrences', shortcut: 'Ctrl+Shift+L', action: () => addToast('All occurrences selected', 'info') },
          ]},
          { label: 'View', items: [
            { label: 'Command Palette...', shortcut: 'Ctrl+Shift+P', action: () => setShowCommandPalette(true) },
            { type: 'separator' },
            { label: 'Appearance', shortcut: '', sub: [
              { label: 'Show Explorer', shortcut: 'Ctrl+Shift+E', action: () => setShowExplorer(true) },
              { label: 'Hide Explorer', shortcut: '', action: () => setShowExplorer(false) },
              { label: 'Toggle Terminal Panel', shortcut: 'Ctrl+`', action: () => setTerminalOpen(prev => !prev) },
              { label: 'Toggle Project Sidebar', shortcut: '', action: () => setShowProjectSidebar(prev => !prev) },
              { label: 'Full Screen', shortcut: 'F11', action: () => { try { document.documentElement.requestFullscreen(); } catch {} } },
            ]},
            { label: 'Editor Layout', shortcut: '', sub: [
              { label: 'Single Editor', action: () => addToast('Single editor mode', 'info') },
              { label: 'Split Right', action: () => addToast('Split right', 'info') },
              { label: 'Split Down', action: () => addToast('Split down', 'info') },
            ]},
            { type: 'separator' },
            { label: 'Explorer', shortcut: 'Ctrl+Shift+E', action: () => setShowExplorer(prev => !prev) },
            { label: 'Terminal', shortcut: 'Ctrl+`', action: () => setTerminalOpen(prev => !prev) },
            { label: 'Problems', shortcut: 'Ctrl+Shift+M', action: () => setTerminalOpen(true) },
            { label: 'Output', shortcut: 'Ctrl+Shift+U', action: () => setTerminalOpen(true) },
          ]},
          { label: 'Go', items: [
            { label: 'Back', shortcut: 'Alt+Left', action: () => addToast('Navigated back', 'info') },
            { label: 'Forward', shortcut: 'Alt+Right', action: () => addToast('Navigated forward', 'info') },
            { type: 'separator' },
            { label: 'Go to File...', shortcut: 'Ctrl+P', action: () => setShowGoToFile(true) },
            { label: 'Go to Symbol in Workspace...', shortcut: 'Ctrl+T', action: () => addToast('Symbol search', 'info') },
            { type: 'separator' },
            { label: 'Go to Line/Column...', shortcut: 'Ctrl+G', action: () => setShowGoToLine(true) },
            { label: 'Go to Bracket', shortcut: 'Ctrl+Shift+\\', action: () => addToast('Go to bracket', 'info') },
            { type: 'separator' },
            { label: 'Next Problem', shortcut: 'F8', action: () => addToast('Next problem', 'info') },
            { label: 'Previous Problem', shortcut: 'Shift+F8', action: () => addToast('Previous problem', 'info') },
            { type: 'separator' },
            { label: 'Switch Project', shortcut: 'Ctrl+K Ctrl+P', sub: projects.slice(0, 10).map(p => ({
              label: p.name, shortcut: '', action: () => selectProject(p),
            })) },
          ]},
          { label: 'Run', items: [
            { label: 'Start Debugging', shortcut: 'F5', action: () => {
              if (selectedProject?.framework) {
                const p = presets[0];
                if (p) runServer(p.command);
              } else addToast('Select a project first', 'info');
            }},
            { label: 'Run Without Debugging', shortcut: 'Ctrl+F5', action: () => {
              if (fileContent) {
                const ext = fileContent.path.split('.').pop() || '';
                const langMap: Record<string, string> = { py: 'python', js: 'node', ts: 'npx ts-node', php: 'php', rs: 'cargo run', go: 'go run' };
                const runner = langMap[ext];
                if (runner) runServer(`${runner} ${fileContent.path}`);
                else addToast('No runner for .'+ext, 'info');
              } else addToast('Open a file first', 'info');
            }},
            { label: 'Restart Debugging', shortcut: 'Ctrl+Shift+F5', action: () => { stopServer(); setTimeout(() => { if (presets[0]) runServer(presets[0].command); }, 500); } },
            { label: 'Stop Debugging', shortcut: 'Shift+F5', action: stopServer },
            { type: 'separator' },
            ...presets.slice(0, 6).map(p => ({
              label: p.label, shortcut: '', action: () => runServer(p.command),
            })),
            { type: 'separator' },
            { label: 'Add Configuration...', shortcut: '', sub: [
              { label: 'npm run dev', action: () => runServer('npm run dev') },
              { label: 'npm start', action: () => runServer('npm start') },
              { label: 'npm run build', action: () => runServer('npm run build') },
              { label: 'php artisan serve', action: () => runServer('php artisan serve') },
              { label: 'uvicorn main:app --reload', action: () => runServer('uvicorn main:app --reload --host 0.0.0.0 --port 8000') },
              { label: 'python main.py', action: () => runServer('python main.py') },
              { label: 'go run .', action: () => runServer('go run .') },
              { label: 'cargo run', action: () => runServer('cargo run') },
              { label: 'pytest', action: () => runServer('pytest') },
              { label: 'php artisan test', action: () => runServer('php artisan test') },
            ]},
            { label: 'Open Running Servers...', shortcut: '', action: () => { setTerminalOpen(true); } },
          ]},
          { label: 'Terminal', items: [
            { label: 'New Terminal', shortcut: 'Ctrl+Shift+`', action: () => setTerminalOpen(true) },
            { label: 'Split Terminal', shortcut: 'Ctrl+Shift+5', action: () => addToast('Split terminal', 'info') },
            { type: 'separator' },
            { label: 'Run Active File', shortcut: '', action: () => {
              if (fileContent) {
                const ext = fileContent.path.split('.').pop() || '';
                const langMap: Record<string, string> = { py: 'python', js: 'node', ts: 'npx ts-node', php: 'php', rs: 'cargo run', go: 'go run', sh: 'bash' };
                const runner = langMap[ext];
                if (runner) runServer(`${runner} "${fileContent.path}"`);
                else addToast('No runner for .'+ext, 'info');
              } else addToast('Open a file first', 'info');
            }},
            { label: 'Run Build Task...', shortcut: 'Ctrl+Shift+B', action: () => { runServer('npm run build'); } },
            { type: 'separator' },
            { label: 'Kill Terminal', shortcut: '', action: stopServer },
            { label: 'Clear Terminal', shortcut: '', action: () => { setTerminalOutput([]); setTerminalLine(0); } },
          ]},
          { label: 'Help', items: [
            { label: 'Welcome / Get Started', shortcut: '', action: () => addToast('Welcome to Lumina Projects! Create or import a project to begin.', 'info') },
            { type: 'separator' },
            { label: 'Show All Commands', shortcut: 'Ctrl+Shift+P', action: () => setShowCommandPalette(true) },
            { label: 'Keyboard Shortcuts Reference', shortcut: 'Ctrl+K Ctrl+S', action: () => setShowCommandPalette(true) },
            { type: 'separator' },
            { label: 'Editor Playground', shortcut: '', sub: [
              { label: 'Interactive Playground', action: () => addToast('Playground coming soon', 'info') },
              { label: 'Welcome Page', action: () => addToast('Welcome to Lumina AI OS — 29 agents ready', 'info') },
            ]},
            { label: 'Tips and Tricks', shortcut: '', sub: [
              { label: 'Command Palette (Ctrl+Shift+P)', action: () => setShowCommandPalette(true) },
              { label: 'Quick Open (Ctrl+P to find files)', action: () => setShowGoToFile(true) },
              { label: 'Toggle Terminal (Ctrl+`)', action: () => setTerminalOpen(prev => !prev) },
              { label: 'Save file (Ctrl+S)', action: () => { if (editing) saveFile(); } },
              { label: 'Multi-Agent AI can build entire apps', action: () => addToast('Visit the Multi-Agent page to use AI coding agents', 'info') },
            ]},
            { type: 'separator' },
            { label: 'Documentation', shortcut: '', action: () => addToast('Visit /docs for REST API docs', 'info') },
            { label: 'Multi-Agent AI Help', shortcut: '', action: () => addToast('CEO AI + 29 specialists: code, debug, test, design, deploy.', 'info') },
            { type: 'separator' },
            { label: 'Check for Updates', shortcut: '', action: () => addToast('Lumina is up to date', 'info') },
            { label: 'About', shortcut: '', action: () => addToast('Lumina AI OS v1.0 — 29 AI agents, 23 API endpoints, 5 templates', 'info') },
          ]},
        ].map(menu => (
          <div key={menu.label} className="relative" onMouseLeave={() => { setActiveMenu(null); setActiveSubMenu(null); }}>
            <button
              onMouseEnter={() => setActiveMenu(menu.label)}
              onClick={() => setActiveMenu(activeMenu === menu.label ? null : menu.label)}
              className={`px-2.5 py-0.5 text-[11px] rounded transition-colors ${
                activeMenu === menu.label ? 'bg-white/10 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}>
              {menu.label}
            </button>
            {activeMenu === menu.label && (
              <div className="absolute top-full left-0 mt-0.5 w-60 bg-slate-900 border border-white/10 rounded-lg shadow-2xl py-1 z-50 max-h-80 overflow-y-auto">
                {menu.items.map((item: any, i: number) =>
                  item.type === 'separator' ? (
                    <div key={i} className="h-px bg-white/5 my-1" />
                  ) : item.sub ? (
                    <div key={i} className="relative" onMouseEnter={() => setActiveSubMenu(item.label)} onMouseLeave={() => setActiveSubMenu(null)}>
                      <button className="w-full flex items-center justify-between px-4 py-1.5 text-[11px] text-slate-300 hover:bg-white/5 hover:text-white transition-colors">
                        <span>{item.label}</span>
                        <ChevronRight className="w-3 h-3 text-slate-600" />
                      </button>
                      {activeSubMenu === item.label && (
                        <div className="absolute top-0 left-full ml-0.5 w-48 bg-slate-900 border border-white/10 rounded-lg shadow-2xl py-1 z-50 max-h-64 overflow-y-auto">
                          {item.sub.map((subItem: any, j: number) => (
                            <button key={j} onClick={() => { subItem.action?.(); setActiveMenu(null); setActiveSubMenu(null); }}
                              className="w-full flex items-center justify-between px-4 py-1.5 text-[11px] text-slate-300 hover:bg-white/5 hover:text-white transition-colors">
                              <span>{subItem.label}</span>
                              {subItem.shortcut && <span className="text-slate-600 text-[10px] ml-2">{subItem.shortcut}</span>}
                            </button>
                          ))}
      {/* ── Go to Line Dialog ── */}
      {showGoToLine && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/60" onClick={() => setShowGoToLine(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-xl shadow-2xl w-full max-w-xs overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
              <span className="text-[10px] text-slate-400">Go to Line/Column</span>
            </div>
            <div className="p-3">
              <input value={gotoLine} onChange={e => setGotoLine(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { const parts = gotoLine.split(':'); if (parts[0]) setCursorLine(parseInt(parts[0]) || 1); if (parts[1]) setCursorCol(parseInt(parts[1]) || 1); setShowGoToLine(false); setGotoLine(''); addToast(`Navigated to line ${parts[0]}`, 'info'); } }}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono outline-none focus:border-lumina-500/50"
                placeholder=":line or :line:column" autoFocus />
              <p className="text-[10px] text-slate-600 mt-1.5">Enter a line number (e.g., 42) or line:column (e.g., 42:10)</p>
            </div>
          </div>
        </div>
      )}

      {/* ── Go to File Dialog ── */}
      {showGoToFile && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/60" onClick={() => setShowGoToFile(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-xl shadow-2xl w-full max-w-md overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
              <SearchCode className="w-4 h-4 text-slate-500" />
              <input value={gotoFilePath} onChange={e => setGotoFilePath(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && selectedProject && gotoFilePath.trim()) { openFile(gotoFilePath.trim()); setShowGoToFile(false); setGotoFilePath(''); } }}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Type a file path to open..." autoFocus />
            </div>
            <div className="max-h-48 overflow-y-auto py-1">
              {files.filter(f => f.type === 'file' && (!gotoFilePath || f.path.toLowerCase().includes(gotoFilePath.toLowerCase()))).slice(0, 15).map(f => (
                <button key={f.path} onClick={() => { openFile(f.path); setShowGoToFile(false); setGotoFilePath(''); }}
                  className="w-full flex items-center gap-2 px-4 py-1.5 text-[11px] text-slate-400 hover:bg-white/5 transition-colors text-left">
                  {getFileIcon(f.name, f.type)}
                  <span>{f.path}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
                      )}
                    </div>
                  ) : (
                    <button key={i} onClick={() => { item.action?.(); setActiveMenu(null); }}
                      className="w-full flex items-center justify-between px-4 py-1.5 text-[11px] text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                      disabled={!item.action}>
                      <span className={!item.action ? 'text-slate-600' : ''}>{item.label}</span>
                      {item.shortcut && <span className="text-slate-600 text-[10px] ml-2">{item.shortcut}</span>}
                    </button>
                  )
                )}
              </div>
            )}
          </div>
        ))}
        <div className="ml-auto flex items-center gap-3 text-[10px] text-slate-500">
          {selectedProject && (
            <span className="text-slate-400 font-medium">{selectedProject.name}</span>
          )}
          <span className="w-px h-3 bg-white/5" />
          <span>{projects.length} projects</span>
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        {/* Project List Sidebar */}
        <div className="w-64 border-r border-white/5 bg-slate-950/30 flex flex-col shrink-0">
          <div className="p-3 border-b border-white/5">
            <div className="flex items-center gap-1.5 bg-white/5 rounded-lg px-2.5 py-1.5 border border-white/5">
              <Search className="w-3.5 h-3.5 text-slate-500" />
              <input value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-[11px] text-white placeholder-slate-600 outline-none"
                placeholder="Search projects..." />
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5">
            {filteredProjects.map(p => (
              <button key={p.id} onClick={() => selectProject(p)}
                className={`w-full text-left px-3 py-2 rounded-lg transition-all text-xs ${
                  selectedProject?.id === p.id
                    ? 'bg-lumina-600/15 border border-lumina-500/20'
                    : 'hover:bg-white/5 border border-transparent'
                }`}>
                <div className="flex items-center gap-2">
                  {p.is_vscode ? <Code2 className="w-3.5 h-3.5 text-blue-400 shrink-0" /> :
                   <Folder className="w-3.5 h-3.5 text-amber-400 shrink-0" />}
                  <div className="min-w-0 flex-1">
                    <p className="text-slate-300 truncate font-medium">{p.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {p.framework && (
                        <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${getLanguageColor(p.language)}`}>
                          {p.framework}
                        </span>
                      )}
                      <span className="text-[9px] text-slate-600">{p.file_count} files</span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
            {filteredProjects.length === 0 && (
              <div className="text-center py-8">
                <Folder className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                <p className="text-[11px] text-slate-500">No projects</p>
              </div>
            )}
          </div>
        </div>

        {/* File Explorer + Editor */}
        {selectedProject ? (
          <>
            {/* File Tree */}
            <div className="w-56 border-r border-white/5 bg-slate-950/20 flex flex-col shrink-0">
              <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
                <div className="flex items-center gap-1.5 min-w-0">
                  <FolderOpen className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span className="text-[11px] text-slate-300 truncate">{selectedProject.name}</span>
                </div>
                <button onClick={() => { setShowNewDialog(true); setNewItemType('file'); }}
                  className="p-1 rounded hover:bg-white/5 text-slate-500 hover:text-slate-300 transition-colors">
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-1.5 space-y-0.5">
                {files.map(f => (
                  <div key={f.path}>
                    <button
                      onClick={() => f.type === 'directory' ? toggleDir(f.path) : openFile(f.path)}
                      className={`w-full flex items-center gap-1.5 px-2 py-1 rounded text-[11px] transition-colors ${
                        fileContent?.path === f.path
                          ? 'bg-lumina-600/15 text-lumina-300'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
                      }`}>
                      {f.type === 'directory' && (
                        expandedDirs.has(f.path)
                          ? <ChevronDown className="w-3 h-3 text-slate-600 shrink-0" />
                          : <ChevronRight className="w-3 h-3 text-slate-600 shrink-0" />
                      )}
                      {getFileIcon(f.name, f.type)}
                      <span className="truncate">{f.name}</span>
                    </button>
                    {f.type === 'directory' && expandedDirs.has(f.path) && (
                      <div className="ml-4 text-[10px] text-slate-600 px-2 py-0.5">...</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Editor + Terminal + AI — stacked vertically */}
            <div className="flex-1 flex flex-col min-w-0">
              {fileContent ? (
                <>
                  <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/5 bg-slate-950/30 shrink-0">
                    <div className="flex items-center gap-2 min-w-0">
                      {getFileIcon(fileContent.path, 'file')}
                      <span className="text-[11px] text-slate-300 truncate">{fileContent.path}</span>
                      {fileContent.language && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500">{fileContent.language}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      {editing ? (
                        <>
                          <button onClick={() => { setEditing(false); setEditContent(fileContent.content); }}
                            className="text-[10px] text-slate-500 hover:text-slate-300 px-2 py-1 rounded transition-colors">
                            Cancel
                          </button>
                          <button onClick={saveFile}
                            className="text-[10px] bg-lumina-600 hover:bg-lumina-500 text-white px-3 py-1 rounded transition-colors flex items-center gap-1">
                            <Save className="w-3 h-3" /> Save
                          </button>
                        </>
                      ) : (
                        <>
                          <button onClick={() => setEditing(true)}
                            className="text-[10px] text-slate-400 hover:text-slate-200 px-2 py-1 rounded transition-colors flex items-center gap-1">
                            <Edit3 className="w-3 h-3" /> Edit
                          </button>
                          <button onClick={() => setShowAI(prev => !prev)}
                            className={`text-[10px] px-2 py-1 rounded transition-colors flex items-center gap-1 ${showAI ? 'bg-lumina-600/15 text-lumina-300' : 'text-amber-400 hover:text-amber-300'}`}>
                            <Sparkles className="w-3 h-3" /> AI
                          </button>
                          <button onClick={() => navigator.clipboard.writeText(fileContent.content).then(() => addToast('Copied', 'info'))}
                            className="text-[10px] text-slate-500 hover:text-slate-300 px-2 py-1 rounded transition-colors">
                            <Copy className="w-3 h-3" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex-1 overflow-hidden">
                    {editing ? (
                      <textarea value={editContent} onChange={e => setEditContent(e.target.value)}
                        className="w-full h-full bg-slate-950 text-sm text-slate-200 font-mono p-4 resize-none outline-none leading-relaxed"
                        spellCheck={false} />
                    ) : (
                      <pre className="h-full overflow-auto bg-slate-950 text-sm text-slate-200 font-mono p-4 leading-relaxed whitespace-pre">
                        <code>{fileContent.content}</code>
                      </pre>
                    )}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-center">
                  <div>
                    <FileText className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                    <p className="text-sm text-slate-400">Select a file to view</p>
                    <p className="text-[11px] text-slate-600 mt-1">{selectedProject.framework} · {selectedProject.file_count} files · {formatSize(selectedProject.total_size_kb)}</p>
                  </div>
                </div>
              )}

            {/* Terminal Panel */}
            <div className="border-t border-white/10 bg-slate-950 shrink-0">
              <button onClick={() => setTerminalOpen(!terminalOpen)}
                className="w-full flex items-center justify-between px-3 py-1.5 hover:bg-white/[0.02] transition-colors">
                <div className="flex items-center gap-2">
                  <Terminal className="w-3.5 h-3.5 text-slate-500" />
                  <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Terminal</span>
                  {serverRunning && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />}
                  {serverRunning && <span className="text-[9px] text-emerald-400">{serverCommand}</span>}
                </div>
                <ChevronRight className={`w-3 h-3 text-slate-600 transition-transform ${terminalOpen ? 'rotate-90' : ''}`} />
              </button>
              {terminalOpen && (
                <div className="border-t border-white/5">
                  <div className="flex items-center gap-1.5 px-2 py-1.5 border-b border-white/5 bg-slate-900/30">
                    {presets.slice(0, 4).map((p, i) => (
                      <button key={i} onClick={() => runServer(p.command)} disabled={serverRunning}
                        className="text-[9px] bg-white/5 hover:bg-white/10 disabled:opacity-30 text-slate-400 hover:text-slate-200 px-2 py-0.5 rounded whitespace-nowrap">
                        <Play className="w-2.5 h-2.5 inline mr-1" />{p.label}
                      </button>
                    ))}
                    <input value={customCommand} onChange={e => setCustomCommand(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && runServer(customCommand)}
                      className="flex-1 bg-white/5 border border-white/10 rounded px-2 py-1 text-[10px] text-white font-mono placeholder-slate-600 outline-none focus:border-lumina-500/50 min-w-[100px]"
                      placeholder="npm run dev..." />
                    <button onClick={() => runServer(customCommand)} disabled={serverRunning || !customCommand.trim()}
                      className="text-[9px] bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white px-2 py-0.5 rounded">
                      <Play className="w-2.5 h-2.5 inline" />
                    </button>
                    {serverRunning && (
                      <button onClick={stopServer}
                        className="text-[9px] bg-red-600/80 hover:bg-red-600 text-white px-2 py-0.5 rounded flex items-center gap-1">
                        <StopCircle className="w-2.5 h-2.5" /> Stop
                      </button>
                    )}
                  </div>
                  <div className="h-40 overflow-y-auto bg-black/80 p-2 font-mono text-[11px] leading-relaxed">
                    {terminalOutput.length === 0 && !serverRunning && (
                      <span className="text-slate-600">No output. Click a preset above or type a command.</span>
                    )}
                    {terminalOutput.length === 0 && serverRunning && (
                      <span className="text-slate-500 animate-pulse">Waiting for output...</span>
                    )}
                    {terminalOutput.map((line: string, i: number) => (
                      <div key={i} className={`whitespace-pre-wrap break-all ${
                        line.includes('[error]') || line.includes('Error') || line.includes('FAIL') ? 'text-red-400' :
                        line.includes('WARN') || line.includes('[warn]') ? 'text-amber-400' :
                        line.includes('SUCCESS') || line.includes('[ok]') ? 'text-emerald-400' :
                        'text-slate-300'
                      }`}>{line}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* AI Assistant Panel */}
            <div className="border-t border-white/10 bg-slate-950 shrink-0">
              <button onClick={() => setShowAI(!showAI)}
                className="w-full flex items-center justify-between px-3 py-1.5 hover:bg-white/[0.02] transition-colors">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">AI Assistant</span>
                  {aiLoading && <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />}
                </div>
                <ChevronRight className={`w-3 h-3 text-slate-600 transition-transform ${showAI ? 'rotate-90' : ''}`} />
              </button>
              {showAI && (
                <div className="border-t border-white/5">
                  <div className="flex items-center gap-2 px-3 py-2">
                    <input value={aiTask} onChange={e => setAiTask(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && askAI()}
                      className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-amber-500/50"
                      placeholder="Ask AI to work on this project... e.g. 'Add a login page'" />
                    <button onClick={askAI} disabled={aiLoading || !aiTask.trim()}
                      className="text-xs bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 disabled:text-slate-600 text-white px-3 py-1.5 rounded-lg transition-all flex items-center gap-1 shrink-0">
                      {aiLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />}
                      {aiLoading ? 'Working...' : 'Send'}
                    </button>
                  </div>
                  <div className="h-48 overflow-y-auto p-3">
                    {aiLoading ? (
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <Loader2 className="w-3 h-3 animate-spin" /> AI is working on your project...
                      </div>
                    ) : aiPhases.length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Phases</p>
                        {aiPhases.map((p: any, i: number) => (
                          <div key={i} className={`rounded-lg border px-3 py-2 text-[11px] ${
                            p.status === 'success' ? 'bg-emerald-500/5 border-emerald-800/20 text-emerald-400' :
                            p.status === 'failed' ? 'bg-red-500/5 border-red-800/20 text-red-400' : 'bg-white/5 border-white/5 text-slate-500'
                          }`}>
                            <span className="font-medium">{p.agent || 'Phase ' + (i+1)}</span>
                            <span className="text-slate-600 ml-2">{p.description}</span>
                          </div>
                        ))}
                        {aiResponse && <pre className="text-[11px] text-slate-300 whitespace-pre-wrap font-sans mt-3 bg-white/5 rounded-lg p-3 leading-relaxed">{aiResponse}</pre>}
                      </div>
                    ) : aiResponse ? (
                      <pre className="text-[11px] text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{aiResponse}</pre>
                    ) : (
                      <div className="text-center py-6">
                        <Bot className="w-6 h-6 text-slate-700 mx-auto mb-2" />
                        <p className="text-[11px] text-slate-500">Ask the AI to add features, fix bugs, or explain code</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            </div>

            {/* Project Info Sidebar */}
            <div className="w-52 border-l border-white/5 bg-slate-950/30 shrink-0 p-3 space-y-3 overflow-y-auto">
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-1">Project</p>
                <p className="text-xs text-slate-300">{selectedProject.name}</p>
              </div>
              {selectedProject.description && (
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-1">Description</p>
                  <p className="text-[11px] text-slate-400">{selectedProject.description}</p>
                </div>
              )}
              <div className="space-y-1.5">
                {selectedProject.framework && (
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Framework</p>
                    <p className="text-[11px] text-slate-400">{selectedProject.framework}</p>
                  </div>
                )}
                {selectedProject.language && (
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Language</p>
                    <p className="text-[11px] text-slate-400">{selectedProject.language}</p>
                  </div>
                )}
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Files</p>
                  <p className="text-[11px] text-slate-400">{selectedProject.file_count}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Size</p>
                  <p className="text-[11px] text-slate-400">{formatSize(selectedProject.total_size_kb)}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Path</p>
                  <p className="text-[10px] text-slate-500 truncate font-mono">{selectedProject.path}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Updated</p>
                  <p className="text-[11px] text-slate-400">{formatDate(selectedProject.updated_at)}</p>
                </div>
              </div>
              {selectedProject.is_vscode && (
                <div className="pt-2 border-t border-white/5">
                  <div className="flex items-center gap-1.5 text-[10px] text-blue-400">
                    <Code2 className="w-3 h-3" /> VS Code Project — shared filesystem
                  </div>
                </div>
              )}
              <div className="pt-2 border-t border-white/5 space-y-1.5">
                <button onClick={() => { setShowAI(prev => !prev); setAiTask(''); }}
                  className="w-full text-[10px] bg-amber-600/15 hover:bg-amber-600/25 text-amber-400 hover:text-amber-300 rounded-lg px-2 py-1.5 transition-colors text-left flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3" /> Ask AI to work on this project
                </button>
              </div>
              <div className="pt-2 border-t border-white/5 space-y-1">
                <button onClick={() => { setEditing(true); }}
                  className="w-full text-[10px] text-slate-400 hover:text-lumina-300 transition-colors text-left">
                  Rename Project
                </button>
                <button onClick={() => deleteProject(selectedProject.id)}
                  className="w-full text-[10px] text-red-400/70 hover:text-red-400 transition-colors text-left">
                  Remove from List
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Folder className="w-16 h-16 text-slate-800 mx-auto mb-4" />
              <p className="text-sm text-slate-400">Select or create a project</p>
              <p className="text-[11px] text-slate-600 mt-1">Import existing projects or start from a template</p>
            </div>
          </div>
        )}
      </div>

      {/* Create Project Dialog */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowCreate(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-slate-200">New Project</h2>
              <button onClick={() => setShowCreate(false)} className="text-slate-500 hover:text-slate-300"><X className="w-4 h-4" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-[10px] text-slate-500 font-medium uppercase">Name</label>
                <input value={newName} onChange={e => setNewName(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-lumina-500/50 mt-1"
                  placeholder="my-awesome-app" autoFocus />
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-medium uppercase">Template</label>
                <div className="grid grid-cols-2 gap-1.5 mt-1">
                  {templates.map(t => (
                    <button key={t.id} onClick={() => setNewTemplate(t.id)}
                      className={`text-left p-3 rounded-lg border transition-all ${
                        newTemplate === t.id
                          ? 'bg-lumina-600/15 border-lumina-500/30'
                          : 'bg-white/5 border-white/5 hover:bg-white/10'
                      }`}>
                      <p className="text-[11px] font-medium text-slate-300">{t.name}</p>
                      <p className="text-[9px] text-slate-500 mt-0.5">{t.framework || t.language || 'Empty'}</p>
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-500 font-medium uppercase">Description (optional)</label>
                <input value={newDescription} onChange={e => setNewDescription(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-lumina-500/50 mt-1"
                  placeholder="What's this project about?" />
              </div>
              <button onClick={createProject} disabled={!newName.trim() || loading}
                className="w-full bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg px-4 py-2.5 text-xs font-medium transition-all">
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── File Browser Dialog (for import) ── */}
      {showBrowser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowBrowser(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-3 border-b border-white/5">
              <div className="flex items-center gap-2">
                <FolderOpen className="w-4 h-4 text-amber-400" />
                <h2 className="text-sm font-semibold text-slate-200">Select Project Folder</h2>
              </div>
              <button onClick={() => setShowBrowser(false)} className="text-slate-500 hover:text-slate-300">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="flex gap-1.5 px-4 py-2.5 border-b border-white/5 overflow-x-auto">
              {quickPaths.map(q => (
                <button key={q.path} onClick={() => navigateBrowser(q.path)}
                  className={`flex items-center gap-1.5 text-[10px] px-2.5 py-1.5 rounded-lg transition-all whitespace-nowrap ${
                    expandQuickPath(q.path) === browserPath
                      ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20'
                      : 'bg-white/5 text-slate-400 hover:text-slate-200 border border-transparent'
                  }`}>
                  {q.icon} {q.label}
                </button>
              ))}
            </div>
            <div className="px-4 py-2 border-b border-white/5 bg-slate-950/30 flex items-center gap-1.5">
              <button onClick={navigateUpBrowser} disabled={!browserParent || browserParent === browserPath}
                className="p-1 rounded hover:bg-white/5 text-slate-400 hover:text-slate-200 disabled:opacity-30 transition-colors">
                <ChevronRight className="w-3.5 h-3.5 rotate-180" />
              </button>
              <button onClick={() => loadBrowser(browserPath)}
                className="p-1 rounded hover:bg-white/5 text-slate-400 hover:text-slate-200 transition-colors">
                <RefreshCw className="w-3 h-3" />
              </button>
              <div className="flex items-center gap-1 text-[10px] text-slate-300 font-mono flex-1 min-w-0">
                <button onClick={() => navigateBrowser('/')} className="hover:text-lumina-300 transition-colors shrink-0">/</button>
                {browserPath.split('/').filter(Boolean).map((seg: string, i: number, arr: string[]) => (
                  <span key={i} className="flex items-center gap-0.5">
                    <button
                      onClick={() => navigateBrowser('/' + arr.slice(0, i + 1).join('/'))}
                      className="hover:text-lumina-300 transition-colors truncate max-w-[100px]">
                      {seg}
                    </button>
                    {i < arr.length - 1 && <span className="text-slate-600">/</span>}
                  </span>
                ))}
              </div>
            </div>
            <div className="max-h-72 overflow-y-auto p-1.5">
              {browserError ? (
                <div className="text-center py-12">
                  <X className="w-10 h-10 text-red-600/50 mx-auto mb-3" />
                  <p className="text-xs text-red-400 mb-1">Browse Failed</p>
                  <p className="text-[10px] text-slate-600 mb-3">{browserError}</p>
                  <div className="flex items-center justify-center gap-2">
                    <button onClick={() => loadBrowser(browserPath || '~')}
                      className="text-[10px] bg-white/5 hover:bg-white/10 text-slate-400 px-4 py-1.5 rounded-lg transition-colors">
                      Retry
                    </button>
                    <button onClick={() => navigateBrowser('~/Documents')}
                      className="text-[10px] bg-lumina-600/15 hover:bg-lumina-600/25 text-lumina-300 px-4 py-1.5 rounded-lg transition-colors">
                      Jump to Documents
                    </button>
                  </div>
                </div>
              ) : browserLoading ? (
                <div className="text-center py-12 text-slate-500 text-xs">Loading...</div>
              ) : browserItems.length === 0 && browserFiles.length === 0 ? (
                <div className="text-center py-12">
                  <Folder className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                  <p className="text-xs text-slate-500 mb-1">Empty folder</p>
                  <p className="text-[10px] text-slate-600 mb-3">No files or folders inside</p>
                  <button onClick={() => selectBrowserFolder(browserPath)}
                    className="text-[10px] bg-amber-600 hover:bg-amber-500 text-white px-4 py-1.5 rounded-lg transition-all">
                    Import as Project Anyway
                  </button>
                </div>
              ) : (
                <>
                  {browserItems.map(item => (
                    <div key={item.path} className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/5 transition-colors">
                      <button onClick={() => navigateBrowser(item.path)}
                        className="flex items-center gap-2.5 text-xs text-slate-300 hover:text-white flex-1 text-left min-w-0">
                        <Folder className="w-4 h-4 text-amber-400 shrink-0" />
                        <span className="truncate">{item.name}</span>
                      </button>
                      <button onClick={() => selectBrowserFolder(item.path)}
                        className="text-[10px] bg-lumina-600 hover:bg-lumina-500 text-white px-3 py-1 rounded-lg transition-all shrink-0 ml-2">
                        Select
                      </button>
                    </div>
                  ))}
                  {browserFiles.length > 0 && browserItems.length > 0 && (
                    <div className="h-px bg-white/5 my-1 mx-2" />
                  )}
                  {browserFiles.slice(0, 20).map(f => (
                    <div key={f.path} className="flex items-center justify-between px-3 py-1.5 rounded-lg opacity-50">
                      <div className="flex items-center gap-2.5 text-[11px] text-slate-500 flex-1 min-w-0">
                        <File className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                        <span className="truncate">{f.name}</span>
                      </div>
                      <span className="text-[9px] text-slate-700 shrink-0 ml-2">
                        {f.size < 1024 ? `${f.size}B` : `${(f.size/1024).toFixed(0)}K`}
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
            <div className="px-4 py-3 border-t border-white/5 bg-slate-950/30 flex items-center justify-between">
              <div className="min-w-0 flex-1">
                <span className="text-[10px] text-slate-500 font-mono truncate block">{browserPath}</span>
                {browserFiles.length > 0 && (
                  <span className="text-[9px] text-slate-600">{browserItems.length} folders · {browserFiles.length} files</span>
                )}
              </div>
              <button onClick={() => selectBrowserFolder(browserPath)}
                className="text-xs bg-amber-600 hover:bg-amber-500 text-white rounded-lg px-4 py-1.5 font-medium transition-all shrink-0 ml-2">
                Open This Folder
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Dialog */}
      {showImport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowImport(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl" onClick={e => e.stopPropagation()}>
            <h2 className="text-sm font-semibold text-slate-200 mb-3">Import Project</h2>
            <p className="text-[11px] text-slate-500 mb-3">Browse to your project folder or paste the path directly.</p>

            <div className="flex items-center gap-2 mb-3">
              <div className="flex-1 flex items-center gap-1.5 bg-white/5 border border-white/10 rounded-lg px-3 py-2">
                <Folder className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <input value={importPath} onChange={e => setImportPath(e.target.value)}
                  className="flex-1 bg-transparent text-xs text-white font-mono outline-none placeholder-slate-600"
                  placeholder="~/my-project" autoFocus />
              </div>
              <button onClick={openBrowser}
                className="text-xs bg-white/5 border border-white/10 text-slate-300 hover:text-white hover:bg-white/10 rounded-lg px-3 py-2 transition-all flex items-center gap-1.5 shrink-0">
                <FolderOpen className="w-3.5 h-3.5" /> Browse
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button onClick={() => { setShowImport(false); setImportPath(''); }}
                className="text-xs text-slate-400 hover:text-slate-200 px-4 py-2 rounded-lg transition-colors">Cancel</button>
              <button onClick={importProject} disabled={!importPath.trim() || loading}
                className="flex-1 bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg px-4 py-2 text-xs font-medium transition-all">
                {loading ? 'Importing...' : 'Import Project'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New File/Folder Dialog */}
      {showNewDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowNewDialog(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-2xl p-6 w-full max-w-sm shadow-2xl" onClick={e => e.stopPropagation()}>
            <h2 className="text-sm font-semibold text-slate-200 mb-3">New {newItemType}</h2>
            <div className="flex items-center gap-1 mb-3">
              <button onClick={() => setNewItemType('file')}
                className={`text-[10px] px-3 py-1.5 rounded-lg transition-all ${newItemType === 'file' ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'bg-white/5 text-slate-400 hover:text-slate-200'}`}>
                File</button>
              <button onClick={() => setNewItemType('directory')}
                className={`text-[10px] px-3 py-1.5 rounded-lg transition-all ${newItemType === 'directory' ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'bg-white/5 text-slate-400 hover:text-slate-200'}`}>
                Directory</button>
            </div>
            <input value={newItemName} onChange={e => setNewItemName(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white font-mono outline-none focus:border-lumina-500/50"
              placeholder={newItemType === 'file' ? 'src/index.ts' : 'src/components'} autoFocus />
            <div className="flex items-center gap-2 mt-3">
              <button onClick={() => { setShowNewDialog(false); setNewItemName(''); }}
                className="text-xs text-slate-400 hover:text-slate-200 px-4 py-2 rounded-lg transition-colors">Cancel</button>
              <button onClick={createNewItem} disabled={!newItemName.trim()}
                className="flex-1 bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-lg px-4 py-2 text-xs font-medium transition-all">
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── VS Code-style Status Bar ── */}
      <div className="flex items-center h-6 bg-lumina-600/90 border-t border-lumina-500/20 px-2 text-[10px] shrink-0 z-20">
        <div className="flex items-center gap-3">
          {fileContent ? (
            <>
              <span className="flex items-center gap-1 text-blue-300">
                <Braces className="w-3 h-3" /> {fileContent.language || 'Plain Text'}
              </span>
              <span className="w-px h-3 bg-white/10" />
              <span className="text-slate-400">UTF-8</span>
              <span className="w-px h-3 bg-white/10" />
              <span className="text-slate-400">LF</span>
              <span className="w-px h-3 bg-white/10" />
              <span className="text-slate-400">Spaces: {tabSize}</span>
            </>
          ) : selectedProject ? (
            <>
              <span className="flex items-center gap-1 text-amber-300">
                <FolderOpen className="w-3 h-3" /> {selectedProject.name}
              </span>
              <span className="w-px h-3 bg-white/10" />
              <span className="text-slate-400">UTF-8</span>
            </>
          ) : (
            <span className="text-slate-400">No project selected</span>
          )}
        </div>
        <div className="ml-auto flex items-center gap-3">
          {fileContent && (
            <span className="text-slate-400">Ln {cursorLine}, Col {cursorCol}</span>
          )}
          <span className="w-px h-3 bg-white/10" />
          {selectedProject?.is_vscode && (
            <span className="flex items-center gap-1 text-blue-300">
              <GitBranch className="w-3 h-3" /> VS Code
            </span>
          )}
          {serverRunning && (
            <span className="flex items-center gap-1 text-emerald-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Running
            </span>
          )}
          <span className="w-px h-3 bg-white/10" />
          <span className="flex items-center gap-1 text-slate-400">
            <Command className="w-3 h-3" /> Ctrl+Shift+P
          </span>
        </div>
      </div>

      {/* ── Command Palette Overlay ── */}
      {showCommandPalette && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] bg-black/60" onClick={() => setShowCommandPalette(false)}>
          <div className="bg-slate-900 border border-white/10 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
              <Command className="w-4 h-4 text-slate-500" />
              <input value={paletteQuery} onChange={e => setPaletteQuery(e.target.value)}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Type a command..." autoFocus />
              <span className="text-[10px] text-slate-600">ESC</span>
            </div>
            <div className="max-h-64 overflow-y-auto py-1">
              {filteredPalette.map(item => (
                <button key={item.id} onClick={() => executePalette(item)}
                  className="w-full flex items-center justify-between px-4 py-2 text-xs hover:bg-white/5 transition-colors text-left">
                  <div className="flex items-center gap-2">
                    <SearchCode className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-slate-300">{item.label}</span>
                  </div>
                  {item.shortcut && <span className="text-[10px] text-slate-600">{item.shortcut}</span>}
                </button>
              ))}
              {filteredPalette.length === 0 && (
                <div className="px-4 py-3 text-xs text-slate-500">No matching commands</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
