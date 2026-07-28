import { useState, useEffect } from 'react';
import { TreePine, MessageSquare, Database, Clock, Brain, Layers, Cpu, Search, ChevronRight, ChevronDown, FileText, RefreshCw } from 'lucide-react';
import Card from '../components/ui/Card';

const BASE = '/api';

const LAYER_ICONS: Record<string, any> = {
  'Short-Term Memory': MessageSquare,
  'Long-Term Memory': Database,
  'Episodic Memory': Clock,
  'Semantic Memory': Brain,
  'Vector Store': Layers,
  'Working Memory': Cpu,
  'Conversation Log': MessageSquare,
};

const LAYER_COLORS: Record<string, string> = {
  'Short-Term Memory': 'var(--color-info)',
  'Long-Term Memory': 'var(--color-success)',
  'Episodic Memory': 'var(--color-warning)',
  'Semantic Memory': 'var(--brand-500)',
  'Vector Store': 'var(--color-error)',
  'Working Memory': 'var(--color-info)',
  'Conversation Log': 'var(--text-secondary)',
};

export default function MemoryTree() {
  const [tree, setTree] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expandedLayers, setExpandedLayers] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [searching, setSearching] = useState(false);

  useEffect(() => { loadTree(); }, []);

  async function loadTree() {
    setLoading(true);
    try {
      const r = await fetch(`${BASE}/memory-tree`);
      const data = await r.json();
      setTree(data.tree || null);
    } catch {}
    setLoading(false);
  }

  async function handleSearch() {
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const r = await fetch(`${BASE}/memory-tree/search?q=${encodeURIComponent(searchQuery)}`);
      const data = await r.json();
      setSearchResults(data.results || []);
    } catch {}
    setSearching(false);
  }

  function toggleLayer(name: string) {
    setExpandedLayers(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  }

  function selectItem(item: any) {
    setSelectedItem(item);
  }

  function Skeleton() {
    return <div className="space-y-3">{[1,2,3,4].map(i => <div key={i} className="skeleton h-12 w-full" />)}</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div className="flex items-center gap-3">
          <div><h1 className="text-xl font-semibold">Memory Tree</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Explore all 8 memory layers in a wiki-style tree</p></div>
        </div>
        <button onClick={loadTree} className="btn btn-ghost p-2"><RefreshCw className="w-4 h-4" /></button>
      </div>

      <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        <div className="flex items-center gap-1 flex-1 max-w-md bg-[var(--bg-hover)] rounded-lg px-3 py-1.5 border border-[var(--border-primary)] focus-within:border-[var(--border-brand)]">
          <Search className="w-3.5 h-3.5 text-[var(--text-tertiary)]" />
          <input className="flex-1 bg-transparent text-xs text-[var(--text-primary)] outline-none placeholder:text-[var(--text-tertiary)]" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()} placeholder="Search memory..." />
        </div>
        <button onClick={handleSearch} className="btn btn-primary text-xs px-3 py-1.5">Search</button>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-72 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          {loading ? <Skeleton /> : !tree ? (
            <div className="text-center py-8 text-[var(--text-tertiary)] text-xs">No memory data</div>
          ) : (
            <div className="space-y-1">
              {(tree.layers || []).map((layer: any) => {
                const Icon = LAYER_ICONS[layer.name] || FileText;
                const color = LAYER_COLORS[layer.name] || 'var(--text-secondary)';
                const expanded = expandedLayers.has(layer.name);
                return (
                  <div key={layer.name}>
                    <button onClick={() => toggleLayer(layer.name)} className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg hover:bg-[var(--bg-hover)] text-xs text-left transition-colors">
                      {expanded ? <ChevronDown className="w-3 h-3 text-[var(--text-tertiary)] shrink-0" /> : <ChevronRight className="w-3 h-3 text-[var(--text-tertiary)] shrink-0" />}
                      <Icon className="w-3.5 h-3.5 shrink-0" style={{ color }} />
                      <span className="flex-1 truncate font-medium">{layer.name}</span>
                      <span className="text-2xs text-[var(--text-tertiary)]">{layer.count}</span>
                    </button>
                    {expanded && (
                      <div className="ml-5 space-y-0.5 mt-0.5">
                        {layer.items.map((item: any) => (
                          <button key={item.id} onClick={() => selectItem(item)} className="flex items-center gap-2 w-full px-2 py-1 rounded-md hover:bg-[var(--bg-hover)] text-xs text-left transition-colors">
                            <FileText className="w-3 h-3 text-[var(--text-tertiary)] shrink-0" />
                            <span className="truncate text-[var(--text-secondary)]">{item.title || item.id}</span>
                          </button>
                        ))}
                        {layer.items.length === 0 && <span className="text-2xs text-[var(--text-tertiary)] px-2">Empty</span>}
                      </div>
                    )}
                  </div>
                );
              })}
              <div className="pt-2 mt-2 border-t border-[var(--border-primary)]">
                <div className="flex items-center justify-between text-2xs text-[var(--text-tertiary)] px-2">
                  <span>{tree.layer_count} layers</span>
                  <span>{tree.total_items} items</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {searchResults.length > 0 && (
            <div className="mb-6">
              <h2 className="text-sm font-semibold mb-3">Search Results</h2>
              <div className="space-y-2">
                {searchResults.map((r: any, i: number) => (
                  <div key={i} className="bg-[var(--bg-tertiary)] rounded-lg p-3 border border-[var(--border-primary)]">
                    <div className="text-xs" dangerouslySetInnerHTML={{ __html: r.content || r.text || JSON.stringify(r) }} />
                    <div className="flex items-center gap-2 mt-1 text-2xs text-[var(--text-tertiary)]">
                      {r.score != null && <span>Score: {(r.score * 100).toFixed(0)}%</span>}
                      {r.source && <span>Source: {r.source}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedItem && !searchResults.length && (
            <div className="max-w-2xl">
              <Card><div className="p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <TreePine className="w-4 h-4 text-[var(--brand-500)]" />
                  <h2 className="text-sm font-semibold">Memory Detail</h2>
                </div>
                <div className="space-y-2 text-xs">
                  {Object.entries(selectedItem).filter(([k]) => k !== 'id').map(([key, val]) => (
                    <div key={key}>
                      <span className="text-[var(--text-tertiary)] capitalize">{key.replace(/_/g, ' ')}: </span>
                      <span className="text-[var(--text-primary)]">{String(val)}</span>
                    </div>
                  ))}
                </div>
              </div></Card>
            </div>
          )}

          {!searchResults.length && !selectedItem && (
            <div className="text-center py-16 text-[var(--text-tertiary)]">
              <TreePine className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-sm">Select a memory item from the tree</p>
              <p className="text-xs mt-1">Or search across all memory layers</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
