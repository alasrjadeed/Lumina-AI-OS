import { useState, useEffect, useCallback } from 'react';
import {
  Folder, File, FolderOpen, ChevronRight, ChevronDown, Search,
  List, Grid, Upload, Plus, Trash2, Download, Copy, Edit3, X,
  FileText, Image, FileCode, FileJson, FileArchive, FileSpreadsheet,
  Music, Video, ExternalLink, RefreshCw, ArrowUp, Home,
  MoreHorizontal, CheckSquare, Square, Eye, Terminal,
  FilePlus, FolderPlus, BoxSelect, Star, Clock, Move,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card from '../components/ui/Card';
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

const HOME_DIR = '/home/oem';

export default function FileManager() {
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
  const { addToast } = useToast();

  const loadDir = useCallback(async (path: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE}/files?path=${encodeURIComponent(path)}`);
      const data = await res.json();
      const items: FileEntry[] = (data.files || data.entries || []).filter((f: FileEntry) => f.name !== '.' && f.name !== '..');
      items.sort((a: FileEntry, b: FileEntry) => {
        if (a.type !== b.type) return a.type === 'dir' ? -1 : 1;
        return a.name.localeCompare(b.name);
      });
      setFiles(items);
    } catch (e: any) {
      addToast(`Failed to load directory: ${e.message}`, 'error');
      setFiles([]);
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    loadDir(currentPath);
    setSelectedFile(null);
    setFileContent(null);
    setSelectedItems(new Set());
  }, [currentPath, loadDir]);

  const navigateTo = (path: string) => {
    setCurrentPath(path);
    if (!treeExpanded.has(path)) {
      setTreeExpanded(prev => new Set([...prev, path]));
    }
  };

  const goUp = () => {
    const parent = currentPath.split('/').slice(0, -1).join('/') || '/';
    navigateTo(parent);
  };

  const goHome = () => navigateTo(HOME_DIR);

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

  const previewFile = async (file: FileEntry) => {
    setSelectedFile(file);
    setContentLoading(true);
    setFileContent(null);
    const ext = file.name.split('.').pop()?.toLowerCase() || '';
    try {
      if (CODE_EXTENSIONS.has(ext) || ext === '') {
        const res = await fetch(`${BASE}/files/read?path=${encodeURIComponent(file.path)}`);
        if (res.ok) {
          const data = await res.json();
          setFileContent(data.content || data.text || '');
        } else {
          setFileContent(null);
        }
      }
    } catch {} finally {
      setContentLoading(false);
    }
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
    const parent = oldPath.split('/').slice(0, -1).join('/');
    const newPath = `${parent}/${renameValue.trim()}`;
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
  const pathParts = currentPath.split('/').filter(Boolean);

  return (
    <div className="flex flex-col h-full">
      <PageHeader icon={Folder} title="File Manager" description={currentPath} />

      <div className="flex-1 flex gap-3 min-h-0 mt-4">
        {/* Tree sidebar */}
        <div className="w-56 shrink-0 overflow-y-auto rounded-xl border border-white/5 bg-white/[0.02] p-2">
          <button onClick={goHome}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-300 hover:bg-white/5 transition-colors mb-1"
          ><Home className="w-3.5 h-3.5" /> Home</button>
          <div className="text-[10px] text-slate-600 uppercase tracking-wider px-3 py-1.5">Directories</div>
          <DirTreeItem
            name={HOME_DIR.split('/').pop() || 'home'}
            path={HOME_DIR}
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
          <div className="flex items-center gap-2 mb-3">
            <button onClick={goUp} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
              <ArrowUp className="w-4 h-4" />
            </button>
            <button onClick={goHome} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
              <Home className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-0.5 text-xs flex-1 min-w-0 overflow-x-auto">
              <button onClick={goHome} className="px-2 py-1 rounded text-slate-400 hover:text-white hover:bg-white/5 whitespace-nowrap shrink-0">~</button>
              {pathParts.map((part, i) => {
                const fullPath = '/' + pathParts.slice(0, i + 1).join('/');
                return (
                  <span key={fullPath} className="flex items-center gap-0.5 shrink-0">
                    <ChevronRight className="w-3 h-3 text-slate-600" />
                    <button onClick={() => navigateTo(fullPath)}
                      className={`px-2 py-1 rounded whitespace-nowrap ${
                        i === pathParts.length - 1 ? 'text-white bg-white/10' : 'text-slate-400 hover:text-white hover:bg-white/5'
                      }`}
                    >{part}</button>
                  </span>
                );
              })}
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Filter..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-32"
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
                <p className="text-sm text-slate-500">Empty directory</p>
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
                          <button onClick={() => { if (f.type === 'dir') navigateTo(f.path); else previewFile(f); }}
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
                    <button key={f.path} onClick={() => { if (f.type === 'dir') navigateTo(f.path); else previewFile(f); }}
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
            {isImage ? (
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

function DirTreeItem({ name, path, depth, currentPath, treeExpanded, treeChildren, onToggle, onNavigate, onLoadChildren }: {
  name: string; path: string; depth: number; currentPath: string;
  treeExpanded: Set<string>; treeChildren: Record<string, FileEntry[]>;
  onToggle: (p: string) => void; onNavigate: (p: string) => void;
  onLoadChildren: (p: string) => void;
}) {
  const isExpanded = treeExpanded.has(path);
  const isActive = currentPath === path;
  const children = treeChildren[path] || [];
  const hasChildren = children.length > 0;

  return (
    <div>
      <button onClick={() => {
        onToggle(path);
        if (!treeChildren[path]) onLoadChildren(path);
      }}
        className={`w-full flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs transition-colors ${
          isActive
            ? 'bg-lumina-500/15 text-lumina-300'
            : 'text-slate-400 hover:text-white hover:bg-white/5'
        }`}
        style={{ paddingLeft: `${12 + depth * 12}px` }}
      >
        {hasChildren ? (
          isExpanded ? <ChevronDown className="w-3 h-3 shrink-0" /> : <ChevronRight className="w-3 h-3 shrink-0" />
        ) : <div className="w-3 shrink-0" />}
        {isExpanded ? <FolderOpen className="w-3.5 h-3.5 shrink-0 text-amber-400" /> : <Folder className="w-3.5 h-3.5 shrink-0 text-amber-400" />}
        <span className="truncate ml-1">{name}</span>
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
