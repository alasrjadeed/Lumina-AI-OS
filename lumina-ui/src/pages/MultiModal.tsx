import { useState, useEffect, useRef } from 'react';
import { Image, FileUp, Trash2, RefreshCw, FileText, Music, Video, Download, Copy } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

const CATEGORY_ICONS: Record<string, any> = {
  image: Image,
  audio: Music,
  video: Video,
  document: FileText,
};

const CATEGORY_COLORS: Record<string, string> = {
  image: 'var(--brand-500)',
  audio: 'var(--color-info)',
  video: 'var(--color-warning)',
  document: 'var(--text-secondary)',
};

export default function MultiModal() {
  const [files, setFiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useToast();

  useEffect(() => { loadFiles(); }, []);

  async function loadFiles() {
    setLoading(true);
    try {
      const params = categoryFilter ? `?category=${categoryFilter}` : '';
      const r = await fetch(`${BASE}/uploads${params}`);
      const data = await r.json();
      setFiles(data.files || []);
    } catch {}
    setLoading(false);
  }

  async function handleUpload(f: File) {
    const formData = new FormData();
    formData.append('file', f);
    try {
      const r = await fetch(`${BASE}/uploads`, { method: 'POST', body: formData });
      const data = await r.json();
      if (data.file) {
        addToast(`Uploaded ${f.name}`, 'success');
        await loadFiles();
      } else {
        addToast(data.detail || 'Upload failed', 'error');
      }
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleUpload(f);
  }

  async function loadPreview(id: string) {
    try {
      const r = await fetch(`${BASE}/uploads/${id}`);
      const data = await r.json();
      setPreview(data.file);
    } catch {}
  }

  async function deleteFile(id: string) {
    try {
      await fetch(`${BASE}/uploads/${id}`, { method: 'DELETE' });
      addToast('Deleted', 'success');
      if (preview?.id === id) setPreview(null);
      await loadFiles();
    } catch {}
  }

  function formatSize(kb: number) {
    if (kb > 1024) return `${(kb / 1024).toFixed(1)} MB`;
    return `${kb.toFixed(0)} KB`;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Multi-modal Input</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Upload and manage images, audio, video, and documents</p></div>
        <button onClick={loadFiles} className="btn btn-ghost p-2"><RefreshCw className="w-4 h-4" /></button>
      </div>

      <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {[null, 'image', 'audio', 'video', 'document'].map(cat => (
          <button key={cat || 'all'} onClick={() => { setCategoryFilter(cat); }} className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${categoryFilter === cat ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'}`}>
            {cat || 'All'}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${dragging ? 'border-[var(--brand-500)] bg-[var(--bg-active)]' : 'border-[var(--border-primary)] hover:border-[var(--border-brand)]'}`}
          onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
          <FileUp className="w-8 h-8 mx-auto mb-2 text-[var(--text-tertiary)]" />
          <p className="text-sm text-[var(--text-secondary)]">Drag & drop files here or</p>
          <button onClick={() => fileInputRef.current?.click()} className="btn btn-primary text-xs mt-2">Browse Files</button>
          <input ref={fileInputRef} type="file" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {files.map((f: any) => {
            const Icon = CATEGORY_ICONS[f.category] || FileText;
            const color = CATEGORY_COLORS[f.category] || 'var(--text-secondary)';
            return (
              <div key={f.id} className="bg-[var(--bg-tertiary)] rounded-xl p-3 border border-[var(--border-primary)] hover:border-[var(--border-brand)] cursor-pointer transition-colors"
                onClick={() => loadPreview(f.id)}>
                <Icon className="w-6 h-6 mb-2" style={{ color }} />
                <p className="text-xs truncate font-medium">{f.stored_name}</p>
                <p className="text-2xs text-[var(--text-tertiary)]">{formatSize(f.size_kb)}</p>
              </div>
            );
          })}
          {!loading && files.length === 0 && (
            <div className="col-span-full text-center py-12 text-[var(--text-tertiary)]">
              <Image className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No files uploaded</p>
            </div>
          )}
        </div>

        {preview && (
          <Card><div className="p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold">{preview.filename || preview.stored_name}</h2>
              <div className="flex items-center gap-1">
                <button onClick={() => deleteFile(preview.id)} className="btn btn-ghost text-xs text-red-400"><Trash2 className="w-3 h-3" /> Delete</button>
              </div>
            </div>
            <div className="text-xs text-[var(--text-secondary)] space-y-1">
              <p>Category: {preview.category}</p>
              <p>Size: {formatSize(preview.size_kb)}</p>
              <p>Uploaded: {new Date(preview.uploaded_at * 1000).toLocaleString()}</p>
            </div>
            {preview.category === 'image' && preview.base64 && (
              <img src={`data:image/png;base64,${preview.base64}`} alt={preview.filename} className="max-w-full max-h-96 rounded-lg" />
            )}
            {preview.category !== 'image' && (
              <div className="bg-[var(--bg-hover)] rounded-lg p-4 text-xs text-[var(--text-tertiary)] text-center">Preview not available for {preview.category} files</div>
            )}
          </div></Card>
        )}
      </div>
    </div>
  );
}
