import { useState, useEffect, useCallback } from 'react';
import {
  Folder, File, FolderOpen, ChevronRight, Search,
  List, Grid, Trash2, Download, Copy, Edit3, X,
  FileText, Image, FileCode, FileJson, FileArchive, FileSpreadsheet,
  Music, Video, RefreshCw, ArrowUp, Home,
  CheckSquare, Square,
  FilePlus, FolderPlus, Clock,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import { useToast } from '../hooks/useToast';

const BASE = '/api/desktop';

interface FileEntry {
  name: string; path: string; type: 'file' | 'dir'; size?: number;
  modified?: number; permissions?: string; extension?: string;
}

function formatSize(bytes?: number): string {
  if (bytes === undefined || bytes < 0) return '—';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / Math.pow(1024, i)).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function formatDate(ts?: number): string {
  if (!ts) return '—';
  const d = new Date(ts * 1000);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 86400000) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  if (diff < 604800000) return d.toLocaleDateString([], { weekday: 'short' });
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

const CODE_EXTENSIONS = new Set(['js','ts','jsx','tsx','py','rs','go','java','c','cpp','h','hpp','cs','rb','php','swift','kt','scala','sh','bash','zsh','fish','yaml','yml','toml','ini','cfg','conf','env','md','txt','html','htm','xhtml','css','scss','sass','less','vue','svelte','json','xml','svg','graphql','sql','r','m','pl','lua','dart','ex','exs','clj','cljs','edn','zig','nim','crystal','haskell','hs','dockerfile','makefile','cmake','gradle']);
const IMG_EXTENSIONS = new Set(['png','jpg','jpeg','gif','bmp','webp','ico','svg','avif','heic','heif','tiff','tif']);

function getFileIcon(name: string, type: 'file' | 'dir') {
  if (type === 'dir') return Folder;
  const ext = name.split('.').pop()?.toLowerCase() || '';
  if (['js','ts','jsx','tsx','py','rs','go','java','c','cpp','rb','php','swift','kt'].includes(ext)) return FileCode;
  if (['json','xml','yaml','yml','toml'].includes(ext)) return FileJson;
  if (['zip','tar','gz','bz2','7z','rar'].includes(ext)) return FileArchive;
  if (['xls','xlsx','csv','ods'].includes(ext)) return FileSpreadsheet;
  if (['mp3','wav','flac','aac','ogg','wma'].includes(ext)) return Music;
  if (['mp4','avi','mkv','mov','wmv','webm'].includes(ext)) return Video;
  if (['png','jpg','jpeg','gif','bmp','webp','svg','ico'].includes(ext)) return Image;
  if (['pdf','doc','docx','ppt','pptx'].includes(ext)) return FileText;
  return File;
}

const EXT_COLORS: Record<string, string> = {
  js: 'text-yellow-400', ts: 'text-blue-400', py: 'text-yellow-300',
  rs: 'text-orange-400', go: 'text-cyan-400', java: 'text-red-400',
  html: 'text-orange-500', css: 'text-blue-500', json: 'text-green-400',
  md: 'text-slate-400', yaml: 'text-purple-400', xml: 'text-amber-400',
  zip: 'text-pink-400', tar: 'text-pink-400', gz: 'text-pink-400',
  png: 'text-violet-400', jpg: 'text-violet-400', jpeg: 'text-violet-400',
  pdf: 'text-red-500', csv: 'text-emerald-400',
};

const ROOT_DIR = '/';

function getDefaultHome(): string {
  try { return process?.env?.HOME || '/home/' + (process?.env?.USER || 'oem'); } catch { return '/home/oem'; }
}

const HOME_DIR = getDefaultHome();

function buildQuickLocations(home: string): { path: string; label: string; icon: any }[] {
  return [
    { path: '/', label: 'Root', icon: Folder },
    { path: '/home', label: '/home', icon: Home },
    { path: home, label: 'User Home', icon: Folder },
    { path: home + '/Desktop', label: 'Desktop', icon: Folder },
    { path: home + '/Downloads', label: 'Downloads', icon: Download },
    { path: home + '/Documents', label: 'Documents', icon: FileText },
    { path: home + '/Music', label: 'Music', icon: Music },
    { path: home + '/Pictures', label: 'Pictures', icon: Image },
    { path: home + '/Videos', label: 'Videos', icon: Video },
    { path: '/tmp', label: 'Temp', icon: Folder },
    { path: '/etc', label: 'System Config', icon: FileCode },
    { path: '/var/log', label: 'System Logs', icon: FileText },
  ];
}

export default function FileManager() {
  const [homeDir, setHomeDir] = useState(HOME_DIR);
  const [currentPath, setCurrentPath] = useState(HOME_DIR);
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'modified' | 'type'>('name');
  const [sortAsc, setSortAsc] = useState(true);
  const [selectedFile, setSelectedFile] = useState<FileEntry | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [contentLoading, setContentLoading] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [showNewInput, setShowNewInput] = useState<'file' | 'folder' | null>(null);
  const [newName, setNewName] = useState('');
  const [showRename, setShowRename] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState('');
  const [treeExpanded, setTreeExpanded] = useState<Set<string>>(new Set([HOME_DIR]));
  const [pathInput, setPathInput] = useState('');
  const [pathHistory, setPathHistory] = useState<string[]>([HOME_DIR]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const [loadError, setLoadError] = useState('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [localRoot, setLocalRoot] = useState<FileSystemDirectoryHandle | null>(null);
  const [localMode, setLocalMode] = useState(false);
  const [localPath, setLocalPath] = useState<string[]>([]);
  const { addToast } = useToast();
  const quickLocations = buildQuickLocations(homeDir);

  const openLocalFolder = async () => {
    try {
      const handle = await window.showDirectoryPicker({ mode: 'read' });
      setLocalRoot(handle);
      setLocalMode(true);
      setLocalPath([handle.name]);
      await loadLocalDir(handle);
    } catch (e: any) {
      if (e.name !== 'AbortError') addToast(`Cannot open folder: ${e.message}`, 'error');
    }
  };

  const loadLocalDir = async (dirHandle: FileSystemDirectoryHandle, pathSegments?: string[]) => {
    setLoading(true);
    setLoadError('');
    const entries: FileEntry[] = [];
    try {
      for await (const [name, handle] of (dirHandle as any).entries()) {
        const fullPath = [...(pathSegments || localPath), name].join('/');
        if (handle.kind === 'directory') {
          entries.push({ name, path: fullPath, type: 'dir', modified: Date.now() / 1000, size: 4096 });
        } else {
          try {
            const file = await (handle as FileSystemFileHandle).getFile();
            entries.push({ name, path: fullPath, type: 'file', modified: file.lastModified / 1000, size: file.size, extension: name.split('.').pop() });
          } catch { entries.push({ name, path: fullPath, type: 'file', modified: Date.now() / 1000, size: 0 }); }
        }
      }
      entries.sort((a, b) => { if (a.type !== b.type) return a.type === 'dir' ? -1 : 1; return a.name.localeCompare(b.name); });
      setFiles(entries);
    } catch (e: any) {
      setLoadError(`Error reading folder: ${e.message}`);
      setFiles([]);
    }
    setLoading(false);
  };

  const goUpLocal = async () => {
    if (localPath.length <= 1) return;
    const newPath = localPath.slice(0, -1);
    let handle = localRoot;
    for (const seg of newPath.slice(1)) {
      if (handle) handle = await (handle as any).getDirectoryHandle(seg);
    }
    if (handle) { setLocalPath(newPath); await loadLocalDir(handle, newPath); }
  };

  const previewLocalFile = async (file: FileEntry) => {
    setSelectedFile(file);
    setContentLoading(true);
    setFileContent(null);
    try {
      let handle: any = localRoot;
      const segs = file.path.split('/').slice(1);
      for (const seg of segs.slice(0, -1)) handle = await handle.getDirectoryHandle(seg);
      const fileHandle = await handle.getFileHandle(segs[segs.length - 1]);
      const f = await fileHandle.getFile();
      const text = await f.text();
      setFileContent(text);
    } catch { setFileContent(`[Cannot preview ${file.name}]\nSize: ${file.size} bytes`); }
    setContentLoading(false);
  };

  useEffect(() => {
    const controller = new AbortController();
    const tid = setTimeout(() => controller.abort(), 2000);
    fetch(BASE + '/info', { signal: controller.signal })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        clearTimeout(tid);
        if (d && d.cwd) {
          const parts = d.cwd.split('/');
          const detected = '/' + parts.slice(0, Math.min(3, parts.length)).join('/');
          setHomeDir(detected);
          if (currentPath === HOME_DIR) { setCurrentPath(d.cwd); setPathInput(d.cwd); setPathHistory([d.cwd]); }
          setBackendStatus('online');
        } else {
          setBackendStatus('offline');
        }
      })
      .catch(() => { clearTimeout(tid); setBackendStatus('offline'); });
    return () => clearTimeout(tid);
  }, []);

  const loadDir = useCallback(async (path: string) => {
    setLoading(true);
    setLoadError('');
    try {
      const res = await fetch(`${BASE}/files?path=${encodeURIComponent(path)}`);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      const items: FileEntry[] = (data.files || data.entries || []).filter((f: FileEntry) => f.name !== '.' && f.name !== '..');
      items.sort((a, b) => { if (a.type !== b.type) return a.type === 'dir' ? -1 : 1; return a.name.localeCompare(b.name); });
      setFiles(items);
      setLoadError('');
    } catch {
      if (localMode && localRoot) { return; }
      const t = Date.now() / 1000;
      const dd = (n: string, p: string): FileEntry => ({ name: n, path: p, type: 'dir', modified: t, size: 4096 });
      const ff = (n: string, p: string, s = 1024): FileEntry => ({ name: n, path: p, type: 'file', modified: t, size: s, extension: n.split('.').pop() });
      const h = homeDir;
      const demo: Record<string, FileEntry[]> = {
        '/': [dd('home', '/home'), dd('etc', '/etc'), dd('tmp', '/tmp'), dd('var', '/var'), dd('usr', '/usr'), dd('opt', '/opt'), dd('boot', '/boot')],
        '/home': [dd('oem', h)],
        '/etc': [ff('hostname', '/etc/hostname', 15), ff('hosts', '/etc/hosts', 350), ff('resolv.conf', '/etc/resolv.conf', 90), dd('nginx', '/etc/nginx'), dd('ssh', '/etc/ssh'), ff('passwd', '/etc/passwd', 2500)],
        '/tmp': [ff('temp.log', '/tmp/temp.log', 120)],
        '/var': [dd('log', '/var/log')],
        '/var/log': [ff('syslog', '/var/log/syslog', 8500), ff('auth.log', '/var/log/auth.log', 4200)],
      };
      demo[h] = [dd('Desktop', h + '/Desktop'), dd('Downloads', h + '/Downloads'), dd('Documents', h + '/Documents'), dd('Music', h + '/Music'), dd('Pictures', h + '/Pictures'), dd('Videos', h + '/Videos'), dd('Projects', h + '/Projects'), dd('.config', h + '/.config'), ff('.bashrc', h + '/.bashrc', 800), ff('README.md', h + '/README.md', 80)];
      demo[h + '/Desktop'] = [ff('notes.txt', h + '/Desktop/notes.txt', 250), ff('todo.md', h + '/Desktop/todo.md', 180)];
      demo[h + '/Downloads'] = [ff('package.tar.gz', h + '/Downloads/package.tar.gz', 85000), ff('setup.sh', h + '/Downloads/setup.sh', 1500)];
      demo[h + '/Documents'] = [ff('notes.md', h + '/Documents/notes.md', 3500)];
      demo[h + '/Projects'] = [dd('lumina', h + '/Projects/lumina'), ff('todo.md', h + '/Projects/todo.md', 150)];
      demo[h + '/Projects/lumina'] = [ff('main.py', h + '/Projects/lumina/main.py', 4500), ff('config.json', h + '/Projects/lumina/config.json', 350), ff('Dockerfile', h + '/Projects/lumina/Dockerfile', 400)];
      const items = demo[path] || demo[h] || demo['/'];
      setFiles(items || []);
    } finally {
      setLoading(false);
    }
  }, [homeDir, localMode, localRoot]);

  useEffect(() => {
    loadDir(currentPath);
    setSelectedFile(null);
    setFileContent(null);
    setSelectedItems(new Set());
  }, [currentPath, loadDir]);

  const navigateTo = async (path: string) => {
    if (localMode && localRoot) {
      const segs = path.split('/').filter(Boolean);
      let handle: any = localRoot;
      try {
        for (const seg of segs) handle = await handle.getDirectoryHandle(seg);
        setLocalPath(segs);
        await loadLocalDir(handle, segs);
        setSelectedFile(null);
        setFileContent(null);
      } catch { navigateToFallback(path); }
      return;
    }
    navigateToFallback(path);
  };

  const navigateToFallback = (path: string) => {
    const normalized = path.replace(/\/+/g, '/').replace(/\/$/, '') || '/';
    setCurrentPath(normalized);
    setPathInput(normalized);
    setPathHistory(prev => [...prev.slice(0, historyIndex + 1), normalized]);
    setHistoryIndex(prev => prev + 1);
    setTreeExpanded(prev => prev.has(normalized) ? prev : new Set([...prev, normalized]));
    setSelectedFile(null);
    setFileContent(null);
  };

  const goUp = () => {
    if (localMode && localRoot) { goUpLocal(); return; }
    if (currentPath === '/') return;
    const parent = currentPath.split('/').slice(0, -1).join('/') || '/';
    navigateToFallback(parent);
  };

  const goBack = () => {
    if (localMode) return;
    if (historyIndex > 0) {
      const idx = historyIndex - 1;
      setHistoryIndex(idx);
      setCurrentPath(pathHistory[idx]);
      setPathInput(pathHistory[idx]);
    }
  };

  const goForward = () => {
    if (localMode) return;
    if (historyIndex < pathHistory.length - 1) {
      const idx = historyIndex + 1;
      setHistoryIndex(idx);
      setCurrentPath(pathHistory[idx]);
      setPathInput(pathHistory[idx]);
    }
  };

  const goHome = () => navigateTo(HOME_DIR);

  const goRoot = () => navigateTo(ROOT_DIR);

  const toggleTree = (path: string) => {
    setTreeExpanded(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path); else next.add(path);
      return next;
    });
  };

  const [treeChildren, setTreeChildren] = useState<Record<string, FileEntry[]>>({});
  const loadTreeDir = useCallback(async (path: string) => {
    try {
      const res = await fetch(`${BASE}/files?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      const items: FileEntry[] = (data.files || data.entries || []).filter((f: FileEntry) => f.type === 'dir' && !f.name.startsWith('.'));
      setTreeChildren(prev => ({ ...prev, [path]: items }));
    } catch {}
  }, []);

  useEffect(() => {
    Array.from(treeExpanded).forEach(p => { if (!treeChildren[p]) loadTreeDir(p); });
  }, [treeExpanded, treeChildren, loadTreeDir]);

  const DEMO_CONTENT: Record<string, string> = {
    '/home/oem/README.md': '# Lumina AI OS\n\nYour autonomous AI employee operating system.\n\n## Features\n- AI Chat & Code Generation\n- Desktop Automation\n- Browser Agent\n- Skills Catalog (57 skills)\n- Agent Presets (12 profiles)\n',
    '/home/oem/.bashrc': 'export PATH=$PATH:$HOME/.local/bin\nexport EDITOR=vim\nalias ll="ls -la"\nalias gs="git status"\nalias gp="git pull"\n# Lumina AI\nsource ~/.lumina_env\n',
    '/home/oem/.profile': '# ~/.profile: executed by Bourne-compatible login shells\nif [ "$BASH" ]; then\n  if [ -f ~/.bashrc ]; then . ~/.bashrc; fi\nfi\n',
    '/home/oem/.gitconfig': '[user]\n\tname = Developer\n\temail = dev@example.com\n[core]\n\teditor = vim\n[init]\n\tdefaultBranch = main\n',
    '/home/oem/Projects/todo.md': '# TODO\n\n## This Week\n- [x] Set up project structure\n- [x] Implement core features\n- [ ] Add tests\n- [ ] Write documentation\n- [ ] Deploy to production\n\n## Next Week\n- Performance optimization\n- User feedback integration\n',
    '/home/oem/Projects/ideas.txt': '# Project Ideas\n\n1. AI-powered code review assistant\n2. Automated documentation generator\n3. Smart task scheduler with ML\n4. Cross-platform mobile app\n5. Real-time collaboration features\n',
    '/home/oem/Projects/lumina/main.py': 'from fastapi import FastAPI\nfrom api import router\nfrom core.provider import engine\n\napp = FastAPI(title="Lumina AI OS")\napp.include_router(router)\n\n@app.get("/")\nasync def root():\n    return {"status": "running", "services": len(engine.providers)}\n',
    '/home/oem/Projects/lumina/config.json': '{\n  "app_name": "Lumina AI OS",\n  "version": "1.0.0",\n  "debug": true,\n  "providers": ["openai", "anthropic", "groq"],\n  "max_tokens": 4096,\n  "temperature": 0.7\n}\n',
    '/home/oem/Projects/lumina/requirements.txt': 'fastapi>=0.110.0\nuvicorn>=0.29.0\nhttpx>=0.27.0\npydantic>=2.0.0\npytest>=8.0.0\n',
    '/home/oem/Projects/lumina/.env.example': '# Lumina Configuration\nOPENAI_API_KEY=\nANTHROPIC_API_KEY=\nGROQ_API_KEY=\nDEBUG=true\nMAX_TOKENS=4096\n',
    '/home/oem/Projects/lumina/Dockerfile': 'FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]\n',
    '/home/oem/Projects/lumina/src/app.tsx': 'import { BrowserRouter, Routes, Route } from "react-router-dom";\nimport Layout from "./components/Layout";\nimport Dashboard from "./pages/Dashboard";\n\nexport default function App() {\n  return (\n    <BrowserRouter>\n      <Layout>\n        <Routes>\n          <Route path="/" element={<Dashboard />} />\n        </Routes>\n      </Layout>\n    </BrowserRouter>\n  );\n}\n',
    '/home/oem/Projects/lumina/src/server.py': 'import asyncio\nfrom fastapi import FastAPI\nfrom core.provider import engine\n\napp = FastAPI()\n\n@app.on_event("startup")\nasync def startup():\n    await engine.init()\n\n@app.get("/health")\nasync def health():\n    return {"status": "ok"}\n',
    '/home/oem/Projects/lumina/src/utils.js': 'export function formatBytes(bytes) {\n  const units = ["B", "KB", "MB", "GB"];\n  let i = 0;\n  while (bytes >= 1024 && i < units.length - 1) {\n    bytes /= 1024;\n    i++;\n  }\n  return `${bytes.toFixed(1)} ${units[i]}`;\n}\n\nexport function debounce(fn, ms = 300) {\n  let timer;\n  return (...args) => {\n    clearTimeout(timer);\n    timer = setTimeout(() => fn(...args), ms);\n  };\n}\n',
    '/home/oem/Projects/website/index.html': '<!DOCTYPE html>\n<html lang="en">\n<head>\n  <meta charset="UTF-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n  <title>My Website</title>\n  <link rel="stylesheet" href="style.css">\n</head>\n<body>\n  <h1>Welcome</h1>\n  <p>This is my awesome website.</p>\n  <script src="script.js"></script>\n</body>\n</html>\n',
    '/home/oem/Projects/website/style.css': 'body {\n  font-family: -apple-system, sans-serif;\n  max-width: 800px;\n  margin: 0 auto;\n  padding: 2rem;\n  background: #0f172a;\n  color: #e2e8f0;\n}\nh1 { color: #818cf8; }\n',
    '/home/oem/Projects/website/script.js': 'console.log("Website loaded!");\ndocument.querySelector("h1").addEventListener("click", () => {\n  alert("Welcome to my site!");\n});\n',
    '/home/oem/Projects/website/package.json': '{\n  "name": "my-website",\n  "version": "1.0.0",\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build"\n  }\n}\n',
    '/home/oem/Desktop/notes.txt': 'Quick notes:\n- Buy groceries\n- Call mom\n- Finish project report\n- Schedule dentist appointment\n',
    '/home/oem/Desktop/todo.md': '# Today\n- [ ] Morning standup\n- [ ] Review PR #42\n- [ ] Write tests\n- [ ] Deploy to staging\n',
    '/home/oem/Documents/notes.md': '# Meeting Notes\n\n## Sprint Planning\n- Goal: Complete authentication module\n- Timeline: 2 weeks\n- Team: 3 developers\n\n## Action Items\n1. Design database schema\n2. Implement JWT auth\n3. Write API endpoints\n',
    '/home/oem/Downloads/setup.sh': '#!/bin/bash\necho "Installing dependencies..."\nsudo apt update\nsudo apt install -y python3 python3-pip nodejs\npip3 install -r requirements.txt\nnpm install\necho "Setup complete!"\n',
    '/etc/hostname': 'lumina-desktop\n',
    '/etc/hosts': '127.0.0.1\tlocalhost\n127.0.1.1\tlumina-desktop\n::1\t\tlocalhost ip6-localhost ip6-loopback\n',
    '/etc/resolv.conf': 'nameserver 8.8.8.8\nnameserver 1.1.1.1\n',
    '/etc/passwd': 'root:x:0:0:root:/root:/bin/bash\noem:x:1000:1000:User:/home/oem:/bin/bash\n',
  };

  const previewFile = async (file: FileEntry) => {
    setSelectedFile(file);
    setContentLoading(true);
    setFileContent(null);
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    try {
      if (CODE_EXTENSIONS.has(ext) || IMG_EXTENSIONS.has(ext) || ext === '') {
        const res = await fetch(`${BASE}/files/read?path=${encodeURIComponent(file.path)}`);
        if (res.ok) {
          const data = await res.json();
          setFileContent(data.content || data.text || '');
          setContentLoading(false);
          return;
        }
      }
    } catch {}
    const fallback = DEMO_CONTENT[file.path];
    if (fallback) { setFileContent(fallback); }
    else { setFileContent(`[File preview not available offline: ${file.path}]\n\nSize: ${file.size || 0} bytes\nType: ${ext || 'unknown'}`); }
    setContentLoading(false);
  };

  const deleteFile = async (path: string) => {
    try {
      const res = await fetch(`${BASE}/files/delete?path=${encodeURIComponent(path)}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
      addToast('Deleted successfully', 'success');
      loadDir(currentPath);
      if (selectedFile?.path === path) { setSelectedFile(null); setFileContent(null); }
    } catch (e: any) {
      addToast(`Delete failed: ${e.message}`, 'error');
    }
  };

  const copyFilePath = (path: string) => {
    navigator.clipboard.writeText(path);
    addToast('Path copied', 'success');
  };

  const downloadFile = async (file: FileEntry) => {
    try {
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      if (CODE_EXTENSIONS.has(ext) || IMG_EXTENSIONS.has(ext)) {
        const res = await fetch(`${BASE}/files/read?path=${encodeURIComponent(file.path)}`);
        if (res.ok) {
          const data = await res.json();
          const content = data.content || data.text || '';
          const blob = new Blob([content], { type: 'text/plain' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a'); a.href = url; a.download = file.name; a.click();
          URL.revokeObjectURL(url);
          addToast('Downloaded', 'success');
          return;
        }
      }
      // Fallback: open in new tab (triggers download if browser supports)
      window.open(`${BASE}/files/read?path=${encodeURIComponent(file.path)}&download=1`, '_blank');
    } catch {}
  };

  const createItem = async (type: 'file' | 'folder') => {
    if (!newName.trim()) return;
    const fullPath = `${currentPath}/${newName.trim()}`;
    try {
      if (type === 'folder') {
        await fetch(`${BASE}/files/mkdir?path=${encodeURIComponent(fullPath)}`, { method: 'POST' });
      } else {
        await fetch(`${BASE}/files/write`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: fullPath, content: '' }),
        });
      }
      addToast(`${type === 'folder' ? 'Folder' : 'File'} created`, 'success');
      setShowNewInput(null);
      setNewName('');
      loadDir(currentPath);
    } catch (e: any) {
      addToast(`Failed: ${e.message}`, 'error');
    }
  };

  const doRename = async (oldPath: string) => {
    if (!renameValue.trim()) return;
    try {
      await fetch(`${BASE}/files/rename?path=${encodeURIComponent(oldPath)}&new_name=${encodeURIComponent(renameValue.trim())}`, { method: 'POST' });
      addToast('Renamed', 'success');
      setShowRename(null);
      setRenameValue('');
      loadDir(currentPath);
      if (selectedFile?.path === oldPath) {
        setSelectedFile(null);
        setFileContent(null);
      }
    } catch (e: any) {
      addToast(`Rename failed: ${e.message}`, 'error');
    }
  };

  const toggleSelect = (path: string) => {
    setSelectedItems(prev => {
      const next = new Set(prev);
      if (next.has(path)) next.delete(path); else next.add(path);
      return next;
    });
  };

  const deleteSelected = () => {
    if (selectedItems.size === 0) return;
    selectedItems.forEach(path => deleteFile(path));
  };

  const sortedFiles = [...files];
  sortedFiles.sort((a, b) => {
    if (a.type !== b.type) return a.type === 'dir' ? -1 : 1;
    let cmp = 0;
    if (sortBy === 'name') cmp = a.name.localeCompare(b.name);
    else if (sortBy === 'size') cmp = (a.size || 0) - (b.size || 0);
    else if (sortBy === 'modified') cmp = (a.modified || 0) - (b.modified || 0);
    else if (sortBy === 'type') cmp = (a.extension || '').localeCompare(b.extension || '');
    return sortAsc ? cmp : -cmp;
  });

  const filteredFiles = searchQuery
    ? sortedFiles.filter(f => f.name.toLowerCase().includes(searchQuery.toLowerCase()))
    : sortedFiles;

  const isImage = selectedFile && IMG_EXTENSIONS.has(selectedFile.name.split('.').pop()?.toLowerCase() || '');
  const isCode = selectedFile && CODE_EXTENSIONS.has(selectedFile.name.split('.').pop()?.toLowerCase() || '');

  const retryBackend = () => {
    setBackendStatus('checking');
    const controller = new AbortController();
    setTimeout(() => controller.abort(), 2000);
    fetch(BASE + '/info', { signal: controller.signal })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d && d.cwd) {
          const parts = d.cwd.split('/');
          const detected = '/' + parts.slice(0, Math.min(3, parts.length)).join('/');
          setHomeDir(detected); setCurrentPath(d.cwd); setPathInput(d.cwd); setPathHistory([d.cwd]);
          setBackendStatus('online');
        } else { setBackendStatus('offline'); }
      })
      .catch(() => setBackendStatus('offline'));
  };

  return (
    <div className="flex flex-col h-full">
      {localMode ? (
        <div className="flex items-center gap-2 px-4 py-2 mb-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-300">
          <Folder className="w-3.5 h-3.5" /> Browsing: <span className="font-mono">{localPath.join('/')}</span>
          <button onClick={() => { setLocalMode(false); setLocalRoot(null); setFiles([]); }} className="ml-auto px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-300">Close</button>
        </div>
      ) : backendStatus === 'offline' && (
        <div className="flex items-center gap-3 px-4 py-2 mb-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
          <span>⚠ Backend offline — <button onClick={openLocalFolder} className="underline hover:text-amber-200 font-medium">Open Local Folder</button> or start the server on port 8000</span>
          <button onClick={retryBackend} className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 transition-all shrink-0">Retry</button>
        </div>
      )}
      {backendStatus === 'checking' && (
        <div className="flex items-center gap-2 px-4 py-2 mb-3 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-400">
          <RefreshCw className="w-3 h-3 animate-spin" /> Connecting to backend...
        </div>
      )}
      <PageHeader icon={Folder} title="File Manager" description={localMode ? localPath.join('/') : currentPath} actions={!localMode ? <button onClick={openLocalFolder} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs text-slate-300 hover:text-white transition-all"><Folder className="w-3.5 h-3.5" />Open Local Folder</button> : undefined} />

      <div className="flex-1 flex gap-3 min-h-0 mt-4">
        {/* Sidebar — Quick Access + Tree */}
        <div className="w-52 shrink-0 overflow-y-auto rounded-xl border border-white/5 bg-white/[0.02] p-2 space-y-1">
          <p className="text-[10px] text-slate-600 uppercase tracking-wider px-3 py-1.5">Quick Access</p>
          {quickLocations.map(loc => {
            const isActive = currentPath === loc.path;
            const Icon = loc.icon;
            return (
              <button key={loc.path} onClick={() => navigateTo(loc.path)}
                className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-all ${
                  isActive ? 'bg-lumina-500/15 text-lumina-300 border border-lumina-500/20' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
                }`}>
                <Icon className="w-4 h-4 shrink-0" />
                <span className="truncate">{loc.label}</span>
              </button>
            );
          })}
          <div className="h-px bg-white/5 my-2" />
          <p className="text-[10px] text-slate-600 uppercase tracking-wider px-3 py-1.5">Browse</p>
          <DirTreeItem
            name="System (/)"
            path="/"
            depth={0}
            currentPath={currentPath}
            treeExpanded={treeExpanded}
            treeChildren={treeChildren}
            onToggle={toggleTree}
            onNavigate={navigateTo}
            onLoadChildren={loadTreeDir}
          />
        </div>

        {/* Main area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Breadcrumbs + toolbar */}
          <div className="flex items-center gap-1.5 mb-2">
            <button onClick={goBack} disabled={historyIndex <= 0}
              className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
              <ChevronRight className="w-4 h-4 rotate-180" />
            </button>
            <button onClick={goForward} disabled={historyIndex >= pathHistory.length - 1}
              className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed">
              <ChevronRight className="w-4 h-4" />
            </button>
            <button onClick={goUp} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
              <ArrowUp className="w-4 h-4" />
            </button>
            <button onClick={goRoot} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors" title="Root /">
              <Folder className="w-4 h-4" />
            </button>
            <button onClick={goHome} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors" title="Home">
              <Home className="w-4 h-4" />
            </button>
            <div className="flex-1 min-w-0">
              <input type="text" value={pathInput || currentPath} onChange={e => setPathInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') navigateTo(pathInput || currentPath); }}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 font-mono"
                placeholder="Enter path..." />
            </div>
            <div className="flex items-center gap-1">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Filter..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-28"
                />
              </div>
              <button onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-lg transition-colors ${viewMode === 'list' ? 'bg-lumina-500/20 text-lumina-300' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
              ><List className="w-4 h-4" /></button>
              <button onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-lumina-500/20 text-lumina-300' : 'text-slate-500 hover:text-white hover:bg-white/5'}`}
              ><Grid className="w-4 h-4" /></button>
              <button onClick={() => loadDir(currentPath)}
                className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors"
              ><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /></button>
            </div>
          </div>

          {/* Action bar */}
          <div className="flex items-center gap-2 mb-3">
            <button onClick={() => { setShowNewInput('file'); setNewName(''); }}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-slate-300 hover:bg-white/5 border border-white/5 transition-all"
            ><FilePlus className="w-3.5 h-3.5" />New File</button>
            <button onClick={() => { setShowNewInput('folder'); setNewName(''); }}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-slate-300 hover:bg-white/5 border border-white/5 transition-all"
            ><FolderPlus className="w-3.5 h-3.5" />New Folder</button>
            {selectedItems.size > 0 && (
              <button onClick={deleteSelected}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 border border-red-500/20 transition-all"
              ><Trash2 className="w-3.5 h-3.5" />Delete ({selectedItems.size})</button>
            )}
            <div className="flex-1" />
            <span className="text-[10px] text-slate-500">{filteredFiles.length} items</span>
          </div>

          {/* New item input */}
          {showNewInput && (
            <div className="flex items-center gap-2 mb-3 p-2 rounded-xl border border-lumina-500/20 bg-lumina-500/5">
              {showNewInput === 'file' ? <FilePlus className="w-4 h-4 text-lumina-400" /> : <FolderPlus className="w-4 h-4 text-lumina-400" />}
              <input type="text" value={newName} onChange={e => setNewName(e.target.value)}
                placeholder={showNewInput === 'file' ? 'filename.ext' : 'folder-name'}
                className="flex-1 bg-transparent border-b border-white/10 px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50"
                onKeyDown={e => { if (e.key === 'Enter') createItem(showNewInput); if (e.key === 'Escape') setShowNewInput(null); }}
                autoFocus
              />
              <button onClick={() => createItem(showNewInput)}
                className="px-3 py-1 rounded-lg text-xs bg-lumina-500/20 text-lumina-300 hover:bg-lumina-500/30 transition-colors"
              >Create</button>
              <button onClick={() => setShowNewInput(null)} className="p-1 text-slate-500 hover:text-white"><X className="w-3.5 h-3.5" /></button>
            </div>
          )}

          {/* File list/grid */}
          <div className="flex-1 overflow-y-auto min-h-0">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <RefreshCw className="w-6 h-6 text-lumina-400 animate-spin" />
              </div>
            ) : filteredFiles.length === 0 ? (
              <div className="text-center py-16">
                <Folder className="w-12 h-12 text-slate-700 mx-auto mb-3" />
                {loadError ? (
                  <div>
                    <p className="text-sm text-red-400 mb-1">{loadError}</p>
                    <p className="text-xs text-slate-500">Make sure the backend server is running on port 8000</p>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">Empty directory</p>
                )}
              </div>
            ) : viewMode === 'list' ? (
              <>
                {/* Column headers */}
                <div className="flex items-center gap-2 px-3 py-2 text-[10px] text-slate-500 uppercase tracking-wider border-b border-white/5">
                  <div className="w-6 shrink-0" />
                  <button onClick={() => { setSortBy('name'); setSortAsc(sortBy !== 'name' ? true : !sortAsc); }} className="flex-1 flex items-center gap-1 hover:text-slate-300">
                    Name {sortBy === 'name' && <span className="text-lumina-400">{sortAsc ? '↑' : '↓'}</span>}
                  </button>
                  <button onClick={() => { setSortBy('size'); setSortAsc(sortBy !== 'size' ? false : !sortAsc); }} className="w-20 text-right hover:text-slate-300">
                    Size {sortBy === 'size' && <span className="text-lumina-400">{sortAsc ? '↑' : '↓'}</span>}
                  </button>
                  <button onClick={() => { setSortBy('modified'); setSortAsc(sortBy !== 'modified' ? false : !sortAsc); }} className="w-24 text-right hover:text-slate-300">
                    Modified {sortBy === 'modified' && <span className="text-lumina-400">{sortAsc ? '↑' : '↓'}</span>}
                  </button>
                  <div className="w-16" />
                </div>
                {/* Rows */}
                <div className="divide-y divide-white/[0.03]">
                  {filteredFiles.map(f => {
                    const Icon = getFileIcon(f.name, f.type);
                    const isSelected = selectedItems.has(f.path);
                    const ext = f.name.split('.').pop()?.toLowerCase() || '';
                    const iconColor = f.type === 'dir' ? 'text-amber-400' : EXT_COLORS[ext] || 'text-slate-400';
                    return (
                      <div key={f.path}
                        className={`flex items-center gap-2 px-3 py-2 text-xs transition-colors group ${
                          selectedFile?.path === f.path ? 'bg-lumina-500/10' : 'hover:bg-white/[0.03]'
                        }`}
                      >
                        <button onClick={() => toggleSelect(f.path)} className="p-0.5 text-slate-600 hover:text-white">
                          {isSelected ? <CheckSquare className="w-3.5 h-3.5 text-lumina-400" /> : <Square className="w-3.5 h-3.5" />}
                        </button>
                        <Icon className={`w-4 h-4 shrink-0 ${iconColor}`} />
                        {showRename === f.path ? (
                          <input type="text" value={renameValue} onChange={e => setRenameValue(e.target.value)}
                            className="flex-1 bg-white/10 border border-lumina-500/50 rounded px-2 py-0.5 text-xs text-white focus:outline-none"
                            onKeyDown={e => { if (e.key === 'Enter') doRename(f.path); if (e.key === 'Escape') setShowRename(null); }}
                            autoFocus onClick={e => e.stopPropagation()}
                          />
                        ) : (
                          <button onClick={() => { if (f.type === 'dir') { navigateTo(f.path); } else if (localMode) { previewLocalFile(f); } else { previewFile(f); } }}
                            className="flex-1 text-left text-slate-300 truncate hover:text-white"
                          >{f.name}</button>
                        )}
                        <span className="w-20 text-right text-slate-500">{f.type === 'file' ? formatSize(f.size) : '—'}</span>
                        <span className="w-24 text-right text-slate-500">{formatDate(f.modified)}</span>
                        <div className="w-16 flex items-center justify-end gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          {f.type === 'dir' && (
                            <button onClick={() => navigateTo(f.path)} title="Open"
                              className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white"
                            ><FolderOpen className="w-3.5 h-3.5" /></button>
                          )}
                          <button onClick={() => copyFilePath(f.path)} title="Copy path"
                            className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white"
                          ><Copy className="w-3.5 h-3.5" /></button>
                          {f.type === 'file' && (
                            <button onClick={() => downloadFile(f)} title="Download"
                              className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white"
                            ><Download className="w-3.5 h-3.5" /></button>
                          )}
                          <button onClick={() => { setShowRename(f.path); setRenameValue(f.name); }} title="Rename"
                            className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white"
                          ><Edit3 className="w-3.5 h-3.5" /></button>
                          <button onClick={() => deleteFile(f.path)} title="Delete"
                            className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-400"
                          ><Trash2 className="w-3.5 h-3.5" /></button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            ) : (
              /* Grid view */
              <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-8 gap-2">
                {filteredFiles.map(f => {
                  const Icon = getFileIcon(f.name, f.type);
                  const isSelected = selectedItems.has(f.path);
                  const ext = f.name.split('.').pop()?.toLowerCase() || '';
                  const iconColor = f.type === 'dir' ? 'text-amber-400' : EXT_COLORS[ext] || 'text-slate-400';
                  return (
                    <button key={f.path} onClick={() => { if (f.type === 'dir') { navigateTo(f.path); } else if (localMode) { previewLocalFile(f); } else { previewFile(f); } }}
                      onContextMenu={e => { e.preventDefault(); toggleSelect(f.path); }}
                      className={`flex flex-col items-center gap-1.5 p-3 rounded-xl border text-xs transition-all ${
                        isSelected ? 'border-lumina-500/40 bg-lumina-500/10' : 'border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10'
                      }`}
                    >
                      <Icon className={`w-8 h-8 ${iconColor}`} />
                      <span className="text-center leading-tight text-slate-300 truncate w-full">{f.name}</span>
                      {f.type === 'file' && <span className="text-[10px] text-slate-500">{formatSize(f.size)}</span>}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Preview panel */}
        {selectedFile && (
          <div className="w-80 shrink-0 overflow-y-auto rounded-xl border border-white/5 bg-white/[0.02]">
            {/* Preview header */}
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{selectedFile.name}</p>
                <p className="text-[10px] text-slate-500">{selectedFile.type === 'dir' ? 'Directory' : formatSize(selectedFile.size)}</p>
              </div>
              <button onClick={() => { setSelectedFile(null); setFileContent(null); }}
                className="p-1 text-slate-500 hover:text-white"
              ><X className="w-4 h-4" /></button>
            </div>

            {/* Preview content */}
            {isImage && !localMode ? (
              <div className="p-4">
                <img src={`${BASE}/files/read?path=${encodeURIComponent(selectedFile.path)}`}
                  alt={selectedFile.name} className="w-full rounded-lg"
                  onError={e => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
                <p className="text-xs text-slate-500 text-center mt-2">Image Preview</p>
              </div>
            ) : contentLoading ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-5 h-5 text-lumina-400 animate-spin" />
              </div>
            ) : isCode && fileContent ? (
              <div className="p-4">
                <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap break-all leading-relaxed max-h-96 overflow-y-auto">
                  {fileContent}
                </pre>
              </div>
            ) : (
              <div className="p-4 space-y-3">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  <span>Modified: {new Date((selectedFile.modified || 0) * 1000).toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <File className="w-3.5 h-3.5 text-slate-500" />
                  <span>Type: {selectedFile.type === 'dir' ? 'Directory' : (selectedFile.extension || 'unknown')}</span>
                </div>
                {selectedFile.type === 'file' && (
                  <>
                    <button onClick={() => downloadFile(selectedFile)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs bg-lumina-500/10 text-lumina-300 hover:bg-lumina-500/20 transition-colors"
                    ><Download className="w-3.5 h-3.5" />Download</button>
                    <button onClick={() => copyFilePath(selectedFile.path)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs bg-white/5 text-slate-300 hover:bg-white/10 transition-colors"
                    ><Copy className="w-3.5 h-3.5" />Copy Path</button>
                    <button onClick={() => deleteFile(selectedFile.path)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-xs bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                    ><Trash2 className="w-3.5 h-3.5" />Delete</button>
                  </>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface DirTreeProps {
  name: string; path: string; depth: number; currentPath: string;
  treeExpanded: Set<string>; treeChildren: Record<string, FileEntry[]>;
  onToggle: (p: string) => void; onNavigate: (p: string) => void;
  onLoadChildren: (p: string) => void;
}

function DirTreeItem(props: DirTreeProps) {
  const { name, path, depth, currentPath, treeExpanded, treeChildren, onToggle, onNavigate, onLoadChildren } = props;
  const isExpanded = treeExpanded.has(path);
  const isActive = currentPath === path;
  const children = treeChildren[path] || [];
  const hasChildren = children.length > 0;

  return (
    <div>
      <button onClick={() => { onToggle(path); if (!treeChildren[path]) onLoadChildren(path); }}
        className={'w-full flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-all ' + (isActive ? 'bg-lumina-500/15 text-lumina-300 border border-lumina-500/20' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent')}
        style={{ paddingLeft: (12 + depth * 12) + 'px' }}
      >
        {hasChildren ? (
          isExpanded ? <ChevronRight className={'w-3 h-3 shrink-0 transition-transform ' + (isExpanded ? 'rotate-90' : '')} /> : <ChevronRight className="w-3 h-3 shrink-0" />
        ) : <div className="w-3 shrink-0" />}
        {isExpanded ? <FolderOpen className="w-3.5 h-3.5 shrink-0 text-amber-400" /> : <Folder className="w-3.5 h-3.5 shrink-0 text-amber-400" />}
        <span className="truncate">{name}</span>
      </button>
      {isExpanded && hasChildren && (
        <div>
          {children.map(child => (
            <DirTreeItem key={child.path}
              name={child.name} path={child.path} depth={depth + 1}
              currentPath={currentPath} treeExpanded={treeExpanded}
              treeChildren={treeChildren} onToggle={onToggle}
              onNavigate={onNavigate} onLoadChildren={onLoadChildren}
            />
          ))}
        </div>
      )}
    </div>
  );
}
