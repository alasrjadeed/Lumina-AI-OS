import { useState, useEffect } from 'react';
import { Calendar, Plus, Trash2, CheckCircle, Circle, Clock, Users, FileText, ListTodo, ChevronRight, RefreshCw } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

export default function MeetingAgents() {
  const [meetings, setMeetings] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [meeting, setMeeting] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: '', description: '', scheduled_at: '', duration_minutes: 30, participants: '' });
  const [noteContent, setNoteContent] = useState('');
  const [actionText, setActionText] = useState('');
  const { addToast } = useToast();

  useEffect(() => { loadMeetings(); }, []);

  async function loadMeetings() {
    setLoading(true);
    try {
      const r = await fetch(`${BASE}/meetings`);
      const data = await r.json();
      setMeetings(data.meetings || []);
    } catch {}
    setLoading(false);
  }

  async function loadMeeting(id: string) {
    try {
      const r = await fetch(`${BASE}/meetings/${id}`);
      const data = await r.json();
      setMeeting(data.meeting);
      setSelectedId(id);
    } catch {}
  }

  async function createMeeting() {
    if (!form.title.trim()) return;
    try {
      const params = new URLSearchParams({
        title: form.title,
        description: form.description,
        duration_minutes: String(form.duration_minutes),
      });
      if (form.scheduled_at) params.set('scheduled_at', form.scheduled_at);
      if (form.participants) params.set('participants', form.participants);
      await fetch(`${BASE}/meetings?${params.toString()}`, { method: 'POST' });
      setForm({ title: '', description: '', scheduled_at: '', duration_minutes: 30, participants: '' });
      addToast('Meeting created', 'success');
      await loadMeetings();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function deleteMeeting(id: string) {
    try {
      await fetch(`${BASE}/meetings/${id}`, { method: 'DELETE' });
      addToast('Deleted', 'success');
      if (selectedId === id) { setMeeting(null); setSelectedId(null); }
      await loadMeetings();
    } catch { addToast('Delete failed', 'error'); }
  }

  async function updateStatus(id: string, status: string) {
    try {
      await fetch(`${BASE}/meetings/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) });
      addToast(`Status: ${status}`, 'success');
      await loadMeeting(id);
      await loadMeetings();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function addNote() {
    if (!noteContent.trim() || !selectedId) return;
    try {
      const params = new URLSearchParams({ content: noteContent });
      await fetch(`${BASE}/meetings/${selectedId}/notes?${params.toString()}`, { method: 'POST' });
      setNoteContent('');
      addToast('Note added', 'success');
      await loadMeeting(selectedId);
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function addAction() {
    if (!actionText.trim() || !selectedId) return;
    try {
      const params = new URLSearchParams({ text: actionText });
      await fetch(`${BASE}/meetings/${selectedId}/actions?${params.toString()}`, { method: 'POST' });
      setActionText('');
      addToast('Action added', 'success');
      await loadMeeting(selectedId);
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function toggleAction(itemId: string) {
    if (!selectedId) return;
    try {
      await fetch(`${BASE}/meetings/${selectedId}/actions/${itemId}/toggle`, { method: 'POST' });
      await loadMeeting(selectedId);
    } catch {}
  }

  function StatusBadge({ status }: { status: string }) {
    const c: Record<string, string> = { scheduled: 'badge-info', in_progress: 'badge-warning', completed: 'badge-success', cancelled: 'badge-error' };
    return <span className={`badge ${c[status] || 'badge-info'}`}>{status}</span>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Meeting Agents</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Schedule meetings, take notes, track action items</p></div>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-64 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          <div className="space-y-3">
            <Card><div className="p-3 space-y-2">
              <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase">New Meeting</h3>
              <input className="input text-xs" value={form.title} onChange={e => setForm(p => ({...p, title: e.target.value}))} placeholder="Meeting title" />
              <input className="input text-xs" type="datetime-local" value={form.scheduled_at} onChange={e => setForm(p => ({...p, scheduled_at: e.target.value}))} />
              <input className="input text-xs" value={form.participants} onChange={e => setForm(p => ({...p, participants: e.target.value}))} placeholder="Participants (comma-sep)" />
              <button onClick={createMeeting} className="btn btn-primary text-xs w-full"><Plus className="w-3 h-3" /> Schedule</button>
            </div></Card>

            <div>
              <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Meetings</h3>
              {meetings.map((m: any) => (
                <div key={m.id} className={`flex items-center justify-between px-2 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${selectedId === m.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}
                  onClick={() => loadMeeting(m.id)}>
                  <div className="flex items-center gap-1.5 flex-1 min-w-0">
                    <Calendar className="w-3 h-3 shrink-0" />
                    <span className="truncate">{m.title}</span>
                  </div>
                  <StatusBadge status={m.status} />
                </div>
              ))}
              {meetings.length === 0 && !loading && <p className="text-2xs text-[var(--text-tertiary)] px-2">No meetings</p>}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {!meeting ? (
            <div className="text-center py-16 text-[var(--text-tertiary)]">
              <Calendar className="w-16 h-16 mx-auto mb-4 opacity-20" />
              <p className="text-sm">Select a meeting to view details</p>
            </div>
          ) : (
            <div className="max-w-3xl space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-semibold">{meeting.title}</h2>
                    <StatusBadge status={meeting.status} />
                  </div>
                  <p className="text-sm text-[var(--text-secondary)] mt-1">{meeting.description || 'No description'}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-[var(--text-tertiary)]">
                    <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(meeting.scheduled_at).toLocaleString()}</span>
                    <span>{meeting.duration_minutes} min</span>
                    <span className="flex items-center gap-1"><Users className="w-3 h-3" /> {meeting.participants?.length || 0} participants</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {meeting.status === 'scheduled' && <button onClick={() => updateStatus(meeting.id, 'in_progress')} className="btn btn-sm btn-primary text-xs">Start</button>}
                  {meeting.status === 'in_progress' && <button onClick={() => updateStatus(meeting.id, 'completed')} className="btn btn-sm btn-primary text-xs">Complete</button>}
                  <button onClick={() => deleteMeeting(meeting.id)} className="btn btn-sm btn-ghost text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card><div className="p-4 space-y-3">
                  <h3 className="text-xs font-semibold flex items-center gap-1.5"><FileText className="w-3.5 h-3.5" /> Notes ({meeting.note_count || 0})</h3>
                  <div className="flex gap-2">
                    <input className="input text-xs flex-1" value={noteContent} onChange={e => setNoteContent(e.target.value)} onKeyDown={e => e.key === 'Enter' && addNote()} placeholder="Add a note..." />
                    <button onClick={addNote} className="btn btn-primary text-xs"><Plus className="w-3 h-3" /></button>
                  </div>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {(meeting.notes || []).map((n: any) => (
                      <div key={n.id} className="bg-[var(--bg-hover)] rounded-lg p-2">
                        <p className="text-xs">{n.content}</p>
                        <div className="flex items-center gap-2 mt-1 text-2xs text-[var(--text-tertiary)]">
                          {n.author && <span>{n.author}</span>}
                          <span>{new Date(n.created_at).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div></Card>

                <Card><div className="p-4 space-y-3">
                  <h3 className="text-xs font-semibold flex items-center gap-1.5"><ListTodo className="w-3.5 h-3.5" /> Action Items ({meeting.action_count || 0})</h3>
                  <div className="flex gap-2">
                    <input className="input text-xs flex-1" value={actionText} onChange={e => setActionText(e.target.value)} onKeyDown={e => e.key === 'Enter' && addAction()} placeholder="New action..." />
                    <button onClick={addAction} className="btn btn-primary text-xs"><Plus className="w-3 h-3" /></button>
                  </div>
                  <div className="space-y-1">
                    {(meeting.action_items || []).map((a: any) => (
                      <div key={a.id} className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-[var(--bg-hover)] cursor-pointer" onClick={() => toggleAction(a.id)}>
                        {a.done ? <CheckCircle className="w-3.5 h-3.5 text-[var(--color-success)] shrink-0" /> : <Circle className="w-3.5 h-3.5 text-[var(--text-tertiary)] shrink-0" />}
                        <span className={`text-xs flex-1 ${a.done ? 'line-through text-[var(--text-tertiary)]' : ''}`}>{a.text}</span>
                        {a.assignee && <span className="text-2xs text-[var(--text-tertiary)]">{a.assignee}</span>}
                      </div>
                    ))}
                  </div>
                </div></Card>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
