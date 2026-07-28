import { useState, useEffect } from 'react';
import { BookOpen, Plus, Trash2, Search, RefreshCw, FileText, Layers, BarChart3 } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

export default function RAGPipeline() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [source, setSource] = useState('manual');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [d, s] = await Promise.all([
        fetch(`${BASE}/rag/documents`).then(r => r.json()),
        fetch(`${BASE}/rag/stats`).then(r => r.json()),
      ]);
      setDocuments(d.documents || []);
      setStats(s);
    } catch {}
    setLoading(false);
  }

  async function ingestDoc() {
    if (!title.trim() || !content.trim()) return;
    try {
      const params = new URLSearchParams({ title, content, source });
      await fetch(`${BASE}/rag/ingest?${params.toString()}`, { method: 'POST' });
      setTitle(''); setContent(''); setSource('manual');
      addToast('Document ingested', 'success');
      await loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function loadDoc(id: string) {
    try {
      const r = await fetch(`${BASE}/rag/documents/${id}`);
      const data = await r.json();
      setSelected(data.document);
    } catch {}
  }

  async function deleteDoc(id: string) {
    try {
      await fetch(`${BASE}/rag/documents/${id}`, { method: 'DELETE' });
      addToast('Deleted', 'success');
      if (selected?.id === id) setSelected(null);
      await loadAll();
    } catch {}
  }

  async function search() {
    if (!searchQuery.trim()) return;
    try {
      const r = await fetch(`${BASE}/rag/search?q=${encodeURIComponent(searchQuery)}&top_k=10`);
      const data = await r.json();
      setSearchResults(data.results || []);
    } catch {}
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">RAG Pipeline</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Document ingestion, chunking, and semantic search</p></div>
        <button onClick={loadAll} className="btn btn-ghost p-2"><RefreshCw className="w-4 h-4" /></button>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-64 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          <div className="space-y-3">
            <Card><div className="p-3 space-y-2">
              <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase">Ingest</h3>
              <input className="input text-xs" value={title} onChange={e => setTitle(e.target.value)} placeholder="Document title" />
              <textarea className="input text-xs" rows={4} value={content} onChange={e => setContent(e.target.value)} placeholder="Paste content here..." />
              <input className="input text-xs" value={source} onChange={e => setSource(e.target.value)} placeholder="Source (manual, web, etc)" />
              <button onClick={ingestDoc} className="btn btn-primary text-xs w-full"><Plus className="w-3 h-3" /> Ingest</button>
            </div></Card>

            <div>
              <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Documents</h3>
              {documents.map((d: any) => (
                <div key={d.id} className={`flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer ${selected?.id === d.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}
                  onClick={() => loadDoc(d.id)}>
                  <FileText className="w-3 h-3 mr-1.5 shrink-0" />
                  <span className="flex-1 truncate">{d.title}</span>
                  <span className="text-2xs text-[var(--text-tertiary)]">{d.chunk_count || 0}</span>
                </div>
              ))}
            </div>
            {stats && (
              <div className="pt-2 border-t border-[var(--border-primary)] text-2xs text-[var(--text-tertiary)] space-y-1">
                <p>{stats.total_documents} docs</p>
                <p>{stats.total_chunks} chunks</p>
                <p>{stats.total_words?.toLocaleString()} words</p>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
            <div className="flex items-center gap-1 flex-1 max-w-md bg-[var(--bg-hover)] rounded-lg px-3 py-1.5 border border-[var(--border-primary)] focus-within:border-[var(--border-brand)]">
              <Search className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
              <input className="flex-1 bg-transparent text-xs text-[var(--text-primary)] outline-none" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} placeholder="Search documents..." />
            </div>
            <button onClick={search} className="btn btn-primary text-xs">Search</button>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {searchResults.length > 0 && (
              <div className="mb-6 space-y-3">
                <h2 className="text-sm font-semibold">Search Results ({searchResults.length})</h2>
                {searchResults.map((r: any, i: number) => (
                  <div key={i} className="bg-[var(--bg-tertiary)] rounded-lg p-3 border border-[var(--border-primary)]">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{r.doc_title}</span>
                      <span className="text-2xs text-[var(--text-tertiary)]">Score: {r.score}</span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-3">{r.text}</p>
                    <p className="text-2xs text-[var(--text-tertiary)] mt-1">{r.doc_source}</p>
                  </div>
                ))}
              </div>
            )}

            {selected && !searchResults.length && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-sm font-semibold">{selected.title}</h2>
                  <button onClick={() => deleteDoc(selected.id)} className="btn btn-ghost text-xs text-red-400"><Trash2 className="w-3 h-3" /> Delete</button>
                </div>
                <div className="text-xs text-[var(--text-secondary)] space-y-1">
                  <p>Source: {selected.source}</p>
                  <p>Words: {selected.word_count?.toLocaleString()}</p>
                  <p>Chunks: {selected.chunks?.length || 0}</p>
                </div>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {(selected.chunks || []).map((chunk: any) => (
                    <div key={chunk.id} className="bg-[var(--bg-tertiary)] rounded-lg p-3 border border-[var(--border-primary)]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-2xs text-[var(--text-tertiary)]">Chunk #{chunk.index}</span>
                        <span className="text-2xs text-[var(--text-tertiary)]">{chunk.word_count} words</span>
                      </div>
                      <p className="text-xs text-[var(--text-secondary)]">{chunk.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!searchResults.length && !selected && (
              <div className="text-center py-16 text-[var(--text-tertiary)]">
                <BookOpen className="w-16 h-16 mx-auto mb-4 opacity-20" />
                <p className="text-sm">Select a document or search</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
