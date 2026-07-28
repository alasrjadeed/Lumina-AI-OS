import { useState, useEffect } from 'react';
import { MessageSquare, Mail, Send, Inbox, ChevronRight, RefreshCw, CheckCheck, Trash2, Smartphone, Globe, Settings, BarChart3 } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

const CHANNEL_ICONS: Record<string, any> = {
  whatsapp: MessageSquare,
  email: Mail,
  sms: Smartphone,
  telegram: Send,
  slack: MessageSquare,
  custom: Globe,
};

const CHANNEL_COLORS: Record<string, string> = {
  whatsapp: 'var(--color-success)',
  email: 'var(--color-info)',
  sms: 'var(--color-warning)',
  telegram: 'var(--color-info)',
  slack: 'var(--brand-500)',
  custom: 'var(--text-secondary)',
};

export default function MessagingChannels() {
  const [messages, setMessages] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [unread, setUnread] = useState<Record<string, number>>({});
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [channelFilter, setChannelFilter] = useState<string | null>(null);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [composeChannel, setComposeChannel] = useState('whatsapp');
  const [composeContent, setComposeContent] = useState('');
  const [composeRecipient, setComposeRecipient] = useState('');
  const [composeSubject, setComposeSubject] = useState('');
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, [channelFilter, showUnreadOnly]);

  async function loadAll() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (channelFilter) params.set('channel', channelFilter);
      if (showUnreadOnly) params.set('unread_only', 'true');
      params.set('limit', '100');
      const r = await fetch(`${BASE}/channels/inbox?${params.toString()}`);
      const data = await r.json();
      setMessages(data.messages || []);

      const u = await fetch(`${BASE}/channels/inbox/unread`);
      setUnread((await u.json()).unread || {});

      const c = await fetch(`${BASE}/channels/config`);
      setChannels((await c.json()).channels || []);

      const s = await fetch(`${BASE}/channels/stats`);
      setStats(await s.json());
    } catch {}
    setLoading(false);
  }

  async function sendMessage() {
    if (!composeContent.trim()) return;
    try {
      const params = new URLSearchParams({ channel: composeChannel, content: composeContent, recipient: composeRecipient });
      if (composeSubject) params.set('subject', composeSubject);
      await fetch(`${BASE}/channels/inbox/send?${params.toString()}`, { method: 'POST' });
      setComposeContent(''); setComposeRecipient(''); setComposeSubject('');
      addToast('Message sent', 'success');
      await loadAll();
    } catch (e: any) { addToast(e.message, 'error'); }
  }

  async function markRead(id: string) {
    await fetch(`${BASE}/channels/inbox/${id}/read`, { method: 'POST' });
    await loadAll();
  }

  async function markAllRead() {
    const params = channelFilter ? `?channel=${channelFilter}` : '';
    await fetch(`${BASE}/channels/inbox/read-all${params}`, { method: 'POST' });
    addToast('All marked read', 'success');
    await loadAll();
  }

  async function deleteMsg(id: string) {
    await fetch(`${BASE}/channels/inbox/${id}`, { method: 'DELETE' });
    await loadAll();
  }

  function formatTime(ts: number) {
    const d = new Date(ts * 1000);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  }

  const totalUnread = Object.values(unread).reduce((a, b) => a + b, 0);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Messaging Channels</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">Unified inbox for all communication channels</p></div>
        <div className="flex items-center gap-2">
          <button onClick={markAllRead} className="btn btn-ghost text-xs"><CheckCheck className="w-3.5 h-3.5" /> Mark All Read</button>
          <button onClick={loadAll} className="btn btn-ghost p-2"><RefreshCw className="w-4 h-4" /></button>
        </div>
      </div>

      <div className="flex-1 flex min-h-0">
        <div className="w-56 border-r border-[var(--border-primary)] overflow-y-auto p-3 shrink-0">
          <div className="space-y-3">
            <div>
              <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Channels</h3>
              <div className="space-y-1">
                <button onClick={() => { setChannelFilter(null); setShowUnreadOnly(false); }} className={`flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-xs transition-colors ${!channelFilter && !showUnreadOnly ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}>
                  <Inbox className="w-3.5 h-3.5" /> All {totalUnread > 0 && <span className="ml-auto bg-[var(--brand-500)] text-white text-2xs rounded-full px-1.5 py-0.5">{totalUnread}</span>}
                </button>
                <button onClick={() => { setChannelFilter(null); setShowUnreadOnly(true); }} className={`flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-xs transition-colors ${showUnreadOnly ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}>
                  <CheckCheck className="w-3.5 h-3.5" /> Unread Only {totalUnread > 0 && <span className="ml-auto text-2xs text-[var(--text-tertiary)]">{totalUnread}</span>}
                </button>
                <div className="border-t border-[var(--border-primary)] my-1" />
                {channels.map((ch: any) => {
                  const Icon = CHANNEL_ICONS[ch.type] || Globe;
                  const color = CHANNEL_COLORS[ch.type] || 'var(--text-secondary)';
                  const count = unread[ch.type] || 0;
                  return (
                    <button key={ch.id} onClick={() => { setChannelFilter(ch.type); setShowUnreadOnly(false); }} className={`flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-xs transition-colors ${channelFilter === ch.type ? 'bg-[var(--bg-active)] text-[var(--text-brand)]' : 'hover:bg-[var(--bg-hover)] text-[var(--text-secondary)]'}`}>
                      <Icon className="w-3.5 h-3.5" style={{ color }} />
                      <span className="flex-1 text-left truncate">{ch.name}</span>
                      {count > 0 && <span className="bg-[var(--brand-500)] text-white text-2xs rounded-full px-1.5 py-0.5">{count}</span>}
                    </button>
                  );
                })}
              </div>
            </div>

            {stats && (
              <div className="pt-2 border-t border-[var(--border-primary)]">
                <h3 className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-2">Stats</h3>
                <div className="space-y-1 text-2xs text-[var(--text-secondary)]">
                  <p>{stats.total_messages || 0} total messages</p>
                  <p>{stats.unread || 0} unread</p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
            <span className="text-2xs font-semibold text-[var(--text-tertiary)] uppercase">Compose</span>
            <select className="input text-2xs py-1 w-24" value={composeChannel} onChange={e => setComposeChannel(e.target.value)}>
              {channels.map((ch: any) => <option key={ch.id} value={ch.type}>{ch.name}</option>)}
            </select>
            <input className="input text-xs flex-1 max-w-[200px]" value={composeRecipient} onChange={e => setComposeRecipient(e.target.value)} placeholder="Recipient" />
            <input className="input text-xs flex-1 max-w-[200px]" value={composeSubject} onChange={e => setComposeSubject(e.target.value)} placeholder="Subject" />
            <input className="input text-xs flex-1" value={composeContent} onChange={e => setComposeContent(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()} placeholder="Type a message..." />
            <button onClick={sendMessage} className="btn btn-primary text-xs"><Send className="w-3 h-3" /> Send</button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="p-4 space-y-3">{[1,2,3,4,5].map(i => <div key={i} className="skeleton h-16 w-full" />)}</div>
            ) : messages.length === 0 ? (
              <div className="flex items-center justify-center h-full text-[var(--text-tertiary)]">
                <div className="text-center"><Inbox className="w-12 h-12 mx-auto mb-3 opacity-30" /><p className="text-sm">No messages</p></div>
              </div>
            ) : (
              <div className="divide-y divide-[var(--border-primary)]">
                {messages.map((m: any) => {
                  const Icon = CHANNEL_ICONS[m.channel] || Globe;
                  const color = CHANNEL_COLORS[m.channel] || 'var(--text-secondary)';
                  return (
                    <div key={m.id} className={`flex items-start gap-3 px-4 py-3 hover:bg-[var(--bg-hover)] transition-colors cursor-pointer ${!m.read ? 'bg-[var(--bg-active)] bg-opacity-30' : ''}`}
                      onClick={() => !m.read && markRead(m.id)}>
                      <div className="mt-0.5">
                        <Icon className="w-4 h-4" style={{ color }} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium">{m.sender || m.recipient || 'Unknown'}</span>
                          <span className="text-2xs text-[var(--text-tertiary)]">{formatTime(m.timestamp)}</span>
                        </div>
                        {m.subject && <p className="text-2xs text-[var(--text-tertiary)] mt-0.5">{m.subject}</p>}
                        <p className={`text-xs mt-0.5 line-clamp-2 ${!m.read ? 'font-medium' : 'text-[var(--text-secondary)]'}`}>{m.content}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-2xs text-[var(--text-tertiary)] capitalize">{m.direction}</span>
                          <span className="text-2xs text-[var(--text-tertiary)]">{m.channel}</span>
                        </div>
                      </div>
                      <button onClick={e => { e.stopPropagation(); deleteMsg(m.id); }} className="p-1 text-red-400 hover:text-red-300 opacity-0 hover:opacity-100 transition-opacity">
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
