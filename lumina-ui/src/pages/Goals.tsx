import { useState, useEffect } from 'react';
import { Target, Plus, Trash2, Edit3, CheckCircle, XCircle, ArrowRight, Clock, ListTodo, BarChart3, Circle, GripVertical } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';
async function get<T>(path: string): Promise<T> { const r = await fetch(`${BASE}${path}`); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function post<T>(path: string, body?: any): Promise<T> { const r = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function del<T>(path: string): Promise<T> { const r = await fetch(`${BASE}${path}`, { method: 'DELETE' }); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function patch<T>(path: string, body: any): Promise<T> { const r = await fetch(`${BASE}${path}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); if (!r.ok) throw new Error(await r.text()); return r.json(); }

const KANBAN_COLUMNS = ['backlog', 'todo', 'in_progress', 'review', 'done'];
const COLUMN_LABELS: Record<string, string> = { backlog: 'Backlog', todo: 'Todo', in_progress: 'In Progress', review: 'Review', done: 'Done' };
const COLUMN_COLORS: Record<string, string> = { backlog: 'var(--text-tertiary)', todo: 'var(--color-info)', in_progress: 'var(--color-warning)', review: 'var(--brand-500)', done: 'var(--color-success)' };
const PRIORITY_LABELS = ['Low', 'Medium', 'High', 'Critical'];
const PRIORITY_COLORS = ['var(--text-tertiary)', 'var(--color-info)', 'var(--color-warning)', 'var(--color-error)'];

export default function Goals() {
  const [tab, setTab] = useState<'goals' | 'kanban' | 'stats'>('kanban');
  const [goals, setGoals] = useState<any[]>([]);
  const [kanban, setKanban] = useState<Record<string, any[]>>({});
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dragging, setDragging] = useState<string | null>(null);
  const [goalForm, setGoalForm] = useState({ title: '', description: '', tags: '' });
  const [todoForm, setTodoForm] = useState({ title: '', goal_id: '', description: '', priority: 0 });
  const [editingTodo, setEditingTodo] = useState<string | null>(null);
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, [tab]);

  async function loadAll() {
    setLoading(true);
    try {
      if (tab === 'goals') {
        const g: any = await get('/goals');
        setGoals(g.goals || []);
      } else if (tab === 'kanban') {
        const k: any = await get('/goals/board/kanban');
        setKanban(k.columns || { backlog: [], todo: [], in_progress: [], review: [], done: [] });
      } else {
        const s: any = await get('/goals/stats');
        setStats(s);
      }
    } catch { /* silent */ }
    setLoading(false);
  }

  function Skeleton({ h = 'h-12' }: { h?: string }) {
    return <div className={`skeleton ${h} w-full`} />;
  }

  function PriorityBadge({ p }: { p: number }) {
    return <span className="text-2xs font-semibold px-1.5 py-0.5 rounded" style={{ backgroundColor: PRIORITY_COLORS[p] + '20', color: PRIORITY_COLORS[p] }}>{PRIORITY_LABELS[p] || 'Low'}</span>;
  }

  function StatusBadge({ status }: { status: string }) {
    const c: Record<string, string> = { active: 'badge-brand', paused: 'badge-warning', completed: 'badge-success', cancelled: 'badge-error' };
    return <span className={`badge ${c[status] || 'badge-info'}`}>{status}</span>;
  }

  async function handleAddGoal() {
    if (!goalForm.title.trim()) return;
    try {
      const params = new URLSearchParams({ title: goalForm.title, description: goalForm.description });
      if (goalForm.tags) params.set('tags', goalForm.tags);
      await post('/goals?' + params.toString());
      setGoalForm({ title: '', description: '', tags: '' });
      addToast('Goal created', 'success');
      loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function handleDeleteGoal(id: string) {
    try { await del(`/goals/${id}`); addToast('Goal deleted', 'success'); loadAll(); } catch { addToast('Delete failed', 'error'); }
  }

  async function handleUpdateGoal(id: string, data: any) {
    try { await patch(`/goals/${id}`, data); addToast('Goal updated', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function handleAddTodo() {
    if (!todoForm.title.trim()) return;
    try {
      const params = new URLSearchParams({ title: todoForm.title });
      if (todoForm.goal_id) params.set('goal_id', todoForm.goal_id);
      if (todoForm.description) params.set('description', todoForm.description);
      params.set('priority', String(todoForm.priority));
      await post('/goals/todos?' + params.toString());
      setTodoForm({ title: '', goal_id: '', description: '', priority: 0 });
      addToast('Todo created', 'success');
      loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function handleMoveTodo(id: string, status: string) {
    try { await post(`/goals/todos/${id}/move?status=${status}`); addToast('Moved', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function handleDeleteTodo(id: string) {
    try { await del(`/goals/todos/${id}`); addToast('Todo deleted', 'success'); loadAll(); } catch { addToast('Delete failed', 'error'); }
  }

  async function handleUpdateTodo(id: string, data: any) {
    try { await patch(`/goals/todos/${id}`, data); setEditingTodo(null); addToast('Todo updated', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }

  function onDragStart(todoId: string) { setDragging(todoId); }
  function onDrop(targetCol: string) {
    if (dragging) { handleMoveTodo(dragging, targetCol); setDragging(null); }
  }

  const tabs = [
    { id: 'kanban' as const, label: 'Kanban', icon: ListTodo },
    { id: 'goals' as const, label: 'Goals', icon: Target },
    { id: 'stats' as const, label: 'Stats', icon: BarChart3 },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Goals & Todos</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Long-term goals, priorities, and kanban board</p></div>
      </div>

      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {/* KANBAN TAB */}
        {tab === 'kanban' && (
          <div className="space-y-6">
            <div className="grid grid-cols-5 gap-3">
              {KANBAN_COLUMNS.map(col => (
                <div key={col} className="bg-[var(--bg-tertiary)] rounded-xl p-3 min-h-[300px] border-2 border-transparent hover:border-[var(--border-brand)] transition-colors"
                  onDragOver={e => e.preventDefault()} onDrop={() => onDrop(col)}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold" style={{ color: COLUMN_COLORS[col] }}>{COLUMN_LABELS[col]}</span>
                    <span className="text-2xs text-[var(--text-tertiary)]">{(kanban[col] || []).length}</span>
                  </div>
                  <div className="space-y-2">
                    {(kanban[col] || []).map((t: any) => (
                      <div key={t.id} className="bg-[var(--bg-elevated)] rounded-lg p-2.5 border border-[var(--border-primary)] cursor-grab hover:border-[var(--border-brand)] transition-colors"
                        draggable onDragStart={() => onDragStart(t.id)}>
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <div className="text-xs font-medium truncate">{t.title}</div>
                            {t.goal_title && <div className="text-2xs text-[var(--text-tertiary)] mt-0.5 truncate">{t.goal_title}</div>}
                            {t.description && <div className="text-2xs text-[var(--text-secondary)] mt-1 line-clamp-2">{t.description}</div>}
                          </div>
                          <div className="flex items-center gap-1 shrink-0">
                            {t.priority > 0 && <PriorityBadge p={t.priority} />}
                          </div>
                        </div>
                        <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-[var(--border-primary)]">
                          <span className="text-2xs text-[var(--text-tertiary)]">{new Date(t.created_at).toLocaleDateString()}</span>
                          <div className="flex items-center gap-1">
                            <button onClick={() => handleDeleteTodo(t.id)} className="text-red-400 hover:text-red-300 p-0.5"><XCircle className="w-3 h-3" /></button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <Card><div className="p-4 space-y-4">
              <h2 className="text-sm font-semibold">New Todo</h2>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
                <div className="input-group md:col-span-2"><label className="input-label">Title</label><input className="input" value={todoForm.title} onChange={e => setTodoForm(p => ({...p, title: e.target.value}))} placeholder="Write unit tests" /></div>
                <div className="input-group"><label className="input-label">Goal ID (optional)</label><input className="input" value={todoForm.goal_id} onChange={e => setTodoForm(p => ({...p, goal_id: e.target.value}))} placeholder="goal_id" /></div>
                <div className="input-group"><label className="input-label">Priority (0-3)</label><input className="input" type="number" min={0} max={3} value={todoForm.priority} onChange={e => setTodoForm(p => ({...p, priority: +e.target.value}))} /></div>
                <button onClick={handleAddTodo} className="btn btn-primary"><Plus className="w-4 h-4" /> Add Todo</button>
              </div>
            </div></Card>
          </div>
        )}

        {/* GOALS TAB */}
        {tab === 'goals' && (
          <div className="space-y-6">
            <Card><div className="p-4 space-y-4">
              <h2 className="text-sm font-semibold">New Goal</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
                <div className="input-group md:col-span-2"><label className="input-label">Title</label><input className="input" value={goalForm.title} onChange={e => setGoalForm(p => ({...p, title: e.target.value}))} placeholder="Build feature X" /></div>
                <div className="input-group"><label className="input-label">Tags (comma-separated)</label><input className="input" value={goalForm.tags} onChange={e => setGoalForm(p => ({...p, tags: e.target.value}))} placeholder="ai, frontend" /></div>
                <button onClick={handleAddGoal} className="btn btn-primary"><Plus className="w-4 h-4" /> Add Goal</button>
              </div>
              <div className="input-group"><label className="input-label">Description</label><textarea className="input" rows={2} value={goalForm.description} onChange={e => setGoalForm(p => ({...p, description: e.target.value}))} placeholder="Goal description..." /></div>
            </div></Card>

            {loading ? (
              <div className="space-y-3">{[1,2,3].map(i => <Skeleton key={i} h="h-20" />)}</div>
            ) : goals.length === 0 ? (
              <div className="text-center py-12 text-[var(--text-tertiary)]"><Target className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No goals yet</p><p className="text-xs mt-1">Create your first goal above</p></div>
            ) : (
              <div className="space-y-3">
                {goals.map((g: any) => (
                  <div key={g.id} className="bg-[var(--bg-tertiary)] rounded-xl p-4 border border-[var(--border-primary)] hover:border-[var(--border-brand)] transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-semibold">{g.title}</h3>
                          <StatusBadge status={g.status} />
                        </div>
                        {g.description && <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2">{g.description}</p>}
                        <div className="flex items-center gap-3 mt-2">
                          {g.tags?.length > 0 && g.tags.map((t: string) => <span key={t} className="text-2xs px-2 py-0.5 rounded-full bg-[var(--bg-hover)] text-[var(--text-tertiary)]">{t}</span>)}
                          <span className="text-2xs text-[var(--text-tertiary)]">Created {new Date(g.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 ml-3">
                        {g.status !== 'completed' && <button onClick={() => handleUpdateGoal(g.id, { status: 'completed' })} className="text-green-400 hover:text-green-300 p-1"><CheckCircle className="w-4 h-4" /></button>}
                        <button onClick={() => handleDeleteGoal(g.id)} className="text-red-400 hover:text-red-300 p-1"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* STATS TAB */}
        {tab === 'stats' && (
          <div className="space-y-6">
            {stats ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {[
                    { l: 'Total Goals', v: stats.total_goals || 0, c: 'var(--brand-500)' },
                    { l: 'Active Goals', v: stats.active_goals || 0, c: 'var(--color-info)' },
                    { l: 'Completed Goals', v: stats.completed_goals || 0, c: 'var(--color-success)' },
                    { l: 'Total Todos', v: stats.total_todos || 0, c: 'var(--text-primary)' },
                    { l: 'Done Todos', v: stats.done_todos || 0, c: 'var(--color-success)' },
                  ].map(s => (
                    <div key={s.l} className="bg-[var(--bg-tertiary)] rounded-xl p-4">
                      <p className="text-2xs text-[var(--text-tertiary)] uppercase">{s.l}</p>
                      <p className="text-2xl font-bold mt-1" style={{ color: s.c }}>{s.v}</p>
                    </div>
                  ))}
                </div>
                <Card><div className="p-4 space-y-3">
                  <h2 className="text-sm font-semibold">Progress</h2>
                  <div className="space-y-2">
                    {[
                      { l: 'Active Goals', v: stats.active_goals || 0, max: Math.max(stats.total_goals || 1, 1) },
                      { l: 'Completed Goals', v: stats.completed_goals || 0, max: Math.max(stats.total_goals || 1, 1) },
                      { l: 'In Progress Todos', v: stats.in_progress_todos || 0, max: Math.max(stats.total_todos || 1, 1) },
                      { l: 'Done Todos', v: stats.done_todos || 0, max: Math.max(stats.total_todos || 1, 1) },
                    ].map(bar => (
                      <div key={bar.l}>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-[var(--text-secondary)]">{bar.l}</span>
                          <span className="text-[var(--text-primary)] font-medium">{bar.v}/{bar.max}</span>
                        </div>
                        <div className="w-full h-2 bg-[var(--bg-hover)] rounded-full overflow-hidden">
                          <div className="h-full rounded-full bg-[var(--brand-500)] transition-all duration-500" style={{ width: `${Math.round((bar.v / bar.max) * 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div></Card>
              </>
            ) : (
              <div className="text-center py-12 text-[var(--text-tertiary)]"><BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No stats available</p></div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
