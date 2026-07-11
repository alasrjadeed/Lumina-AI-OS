import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Send, Bot, User, Loader2, Sparkles, Copy, Check,
  Plus, MessageSquare, Trash2, Edit3,
  Search, X, PanelLeftClose, PanelLeft,
  Code2, Brain, Globe, Terminal, Database, Cpu,
  Hash,
} from 'lucide-react';
import { useToast } from '../hooks/useToast';

const BASE = '/api/chat';

interface Message {
  role: 'user' | 'assistant' | 'slash';
  content: string;
  timestamp?: string;
}

interface Thread {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

const AGENTS = ['CEO_AI', 'SoftwareEngineer', 'DataAnalyst', 'DevOps', 'Researcher'];

const SUGGESTIONS = [
  { icon: Code2, label: 'Write code', text: 'Write a Python function to fetch and parse JSON from an API' },
  { icon: Brain, label: 'Explain concept', text: 'Explain how attention works in transformer models' },
  { icon: Globe, label: 'Research topic', text: 'What are the latest developments in AI agents?' },
  { icon: Terminal, label: 'Debug help', text: 'Help me debug a memory leak in my Node.js app' },
  { icon: Database, label: 'Data analysis', text: 'Show me how to analyze a CSV with Pandas' },
  { icon: Cpu, label: 'System status', text: '/status' },
];

interface ConversationItem {
  id: string;
  title: string;
  message_count: number;
  updated_at: string;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function renderMarkdown(text: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(renderInline(text.slice(lastIndex, match.index)));
    }
    const [, lang, code] = match;
    parts.push(<CodeBlock key={match.index} code={code.replace(/\n$/, '')} language={lang || 'text'} />);
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < text.length) {
    parts.push(renderInline(text.slice(lastIndex)));
  }

  return parts.length > 0 ? parts : renderInline(text);
}

function renderInline(text: string): React.ReactNode {
  const segments = text.split(/(`[^`]+`)/g);
  return (
    <span>
      {segments.map((seg, i) => {
        if (seg.startsWith('`') && seg.endsWith('`')) {
          return <code key={i} className="px-1.5 py-0.5 bg-white/10 rounded text-[13px] font-mono text-lumina-300">{seg.slice(1, -1)}</code>;
        }
        return <span key={i}>{seg}</span>;
      })}
    </span>
  );
}

function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="my-3 rounded-xl overflow-hidden border border-white/10 bg-slate-900/80">
      <div className="flex items-center justify-between px-4 py-1.5 bg-white/5 border-b border-white/5">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">{language}</span>
        <button onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
          className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors">
          {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="p-4 text-sm text-slate-200 font-mono leading-relaxed overflow-x-auto whitespace-pre-wrap">{code}</pre>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center shadow-lg shadow-lumina-500/20">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="bg-white/5 border border-white/5 rounded-2xl px-5 py-3">
        <div className="flex gap-1.5">
          <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [agent, setAgent] = useState('CEO_AI');
  const [showCommands, setShowCommands] = useState(false);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeThread, setActiveThread] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const streamRef = useRef<AbortController | null>(null);
  const { addToast } = useToast();

  const fetchConversations = useCallback(async () => {
    try {
      const res = await get<{ conversations: ConversationItem[] }>('/conversations');
      setConversations(res.conversations);
    } catch { /* silent */ }
  }, []);

  const loadThread = useCallback(async (threadId: string) => {
    setActiveThread(threadId);
    setMessages([]);
    try {
      const res = await get<{ conversations: Message[] }>(`/history?thread_id=${threadId}`);
      setMessages(res.conversations);
    } catch {
      addToast('Failed to load conversation', 'error');
    }
  }, [addToast]);

  const createNew = useCallback(async () => {
    try {
      const res = await post<{ conversation: Thread }>('/conversations?title=New Chat', {});
      setActiveThread(res.conversation.id);
      setMessages([]);
      fetchConversations();
    } catch {
      addToast('Failed to create conversation', 'error');
    }
  }, [fetchConversations, addToast]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startNew = () => {
    setActiveThread(null);
    setMessages([]);
    setInput('');
  };

  const stopStreaming = () => {
    streamRef.current?.abort();
    setStreaming(false);
    setLoading(false);
  };

  const send = async () => {
    const msg = input.trim();
    if (!msg || loading) return;
    setInput('');
    setShowCommands(false);

    const userMsg: Message = { role: 'user', content: msg, timestamp: new Date().toISOString() };
    setMessages(m => [...m, userMsg]);
    setLoading(true);
    setStreaming(true);

    try {
      const assistantMsg: Message = { role: 'assistant', content: '', timestamp: new Date().toISOString() };
      setMessages(m => [...m, assistantMsg]);

      const controller = new AbortController();
      streamRef.current = controller;

      const res = await fetch(`${BASE}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, thread_id: activeThread, agent }),
        signal: controller.signal,
      });

      if (!res.ok) throw new Error('Stream failed');

      const reader = res.body?.getReader();
      if (!reader) throw new Error('No reader');

      const decoder = new TextDecoder();
      let buffer = '';
      let threadId = activeThread;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.thread_id) threadId = data.thread_id;
              if (data.done) {
                if (data.token) {
                  setMessages(m => {
                    const updated = [...m];
                    const last = updated[updated.length - 1];
                    if (last?.role === 'assistant') last.content += data.token;
                    return updated;
                  });
                }
                setStreaming(false);
                setLoading(false);
                if (threadId && !activeThread) {
                  setActiveThread(threadId);
                  fetchConversations();
                } else if (threadId) {
                  fetchConversations();
                }
              } else if (data.token) {
                setMessages(m => {
                  const updated = [...m];
                  const last = updated[updated.length - 1];
                  if (last?.role === 'assistant') last.content += data.token;
                  return updated;
                });
              }
            } catch { /* skip */ }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setMessages(m => {
          const updated = [...m];
          const last = updated[updated.length - 1];
          if (last?.role === 'assistant') last.content = 'Error: Failed to get response.';
          return updated;
        });
      }
      setStreaming(false);
      setLoading(false);
    }
  };

  const filteredConversations = conversations.filter(c =>
    !searchQuery || c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (streaming) { stopStreaming(); return; }
      send();
    }
  };

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 overflow-hidden border-r border-white/5 flex flex-col bg-slate-950/30 shrink-0`}>
        <div className="p-3 space-y-2">
          <button onClick={createNew}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-lumina-600/15 border border-lumina-500/20 text-xs font-medium text-lumina-300 hover:bg-lumina-600/25 transition-all">
            <Plus className="w-3.5 h-3.5" /> New Chat
          </button>
          <div className="relative">
            <Search className="w-3 h-3 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg pl-8 pr-2 py-1.5 text-[10px] text-slate-300 outline-none focus:border-lumina-500/50 placeholder-slate-500"
              placeholder="Search conversations..." />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
          <button onClick={startNew}
            className={`w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs transition-all ${
              !activeThread ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}>
            <Sparkles className="w-3.5 h-3.5 text-lumina-400" />
            <span className="truncate">New Chat</span>
          </button>

          {filteredConversations.map(conv => (
            <div key={conv.id}
              className={`group flex items-center gap-2 px-3 py-2 rounded-lg text-xs cursor-pointer transition-all ${
                activeThread === conv.id
                  ? 'bg-white/[0.06] text-slate-200 border border-white/5'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/[0.03]'
              }`}
              onClick={() => loadThread(conv.id)}>
              <MessageSquare className="w-3 h-3 shrink-0" />
              <span className="flex-1 truncate">{conv.title}</span>
              <span className="text-[9px] text-slate-600 shrink-0">{conv.message_count}</span>
              <div className="hidden group-hover:flex items-center gap-0.5 shrink-0">
                <button onClick={e => { e.stopPropagation(); }}
                  className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-slate-300">
                  <Edit3 className="w-3 h-3" />
                </button>
                <button onClick={async e => {
                  e.stopPropagation();
                  try {
                    await fetch(`${BASE}/conversations/${conv.id}`, { method: 'DELETE' });
                    if (activeThread === conv.id) setActiveThread(null);
                    fetchConversations();
                  } catch { addToast('Failed to delete', 'error'); }
                }}
                  className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-red-400">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="p-3 border-t border-white/5 text-[9px] text-slate-600">
          {conversations.length} conversations
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center gap-3 px-6 py-3 border-b border-white/5 shrink-0">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-1.5 rounded-lg hover:bg-white/5 text-slate-500 hover:text-slate-300 transition-colors">
            {sidebarOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center">
              <Bot className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <h2 className="text-xs font-semibold text-slate-200">Chat</h2>
              <p className="text-[9px] text-slate-500">{loading ? 'Generating...' : `${messages.length} messages`}</p>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <select value={agent} onChange={e => setAgent(e.target.value)}
              className="bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-[10px] text-slate-300 outline-none focus:border-lumina-500/50">
              {AGENTS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
            {streaming && (
              <button onClick={stopStreaming}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400 text-[10px] hover:bg-red-500/20 transition-colors">
                <X className="w-3 h-3" /> Stop
              </button>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
          {messages.length === 0 && !loading && (
            <div className="text-center mt-12 animate-fade-in">
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-lumina-400/10 to-lumina-600/10 border border-lumina-500/20 flex items-center justify-center">
                <Sparkles className="w-8 h-8 text-lumina-400/60" />
              </div>
              <p className="text-slate-400 text-sm font-medium">Ask anything to get started</p>
              <p className="text-xs text-slate-600 mt-1">Or try one of these:</p>
              <div className="flex flex-wrap justify-center gap-2 mt-4 max-w-lg mx-auto">
                {SUGGESTIONS.map((s, i) => (
                  <button key={i} onClick={() => { setInput(s.text); inputRef.current?.focus(); }}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white/[0.03] border border-white/5 text-[10px] text-slate-400 hover:text-slate-200 hover:bg-white/[0.06] hover:border-lumina-500/20 transition-all">
                    <s.icon className="w-3 h-3 text-lumina-400" />
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 animate-fade-in ${m.role === 'assistant' ? '' : 'flex-row-reverse'}`}>
              <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 shadow-lg ${
                m.role === 'assistant'
                  ? 'bg-gradient-to-br from-lumina-400 to-lumina-600 shadow-lumina-500/20'
                  : 'bg-white/10'
              }`}>
                {m.role === 'assistant' ? <Bot className="w-4 h-4 text-white" /> : <User className="w-4 h-4 text-slate-300" />}
              </div>
              <div className={`max-w-[80%] rounded-2xl px-5 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                m.role === 'assistant'
                  ? 'bg-white/5 border border-white/5 text-slate-200'
                  : 'bg-gradient-to-r from-lumina-600/20 to-lumina-600/5 text-lumina-200 border border-lumina-500/20'
              }`}>
                {m.role === 'assistant' ? renderMarkdown(m.content) : m.content}
                {m.timestamp && m.role === 'assistant' && m.content && (
                  <div className="flex items-center justify-end gap-2 mt-2 opacity-0 hover:opacity-100 transition-opacity">
                    <button onClick={() => { navigator.clipboard.writeText(m.content); addToast('Copied', 'success'); }}
                      className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-slate-300">
                      <Copy className="w-3 h-3" />
                    </button>
                    <span className="text-[9px] text-slate-600">{new Date(m.timestamp).toLocaleTimeString()}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && !streaming && messages[messages.length - 1]?.role !== 'assistant' && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <div className="px-6 py-4 border-t border-white/5 shrink-0">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-3 pr-10 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 focus:bg-white/10 transition-all duration-200 resize-none max-h-32"
                placeholder={streaming ? 'AI is responding...' : 'Type a message...'}
                value={input}
                onChange={e => { setInput(e.target.value); if (e.target.value.startsWith('/')) setShowCommands(true); else setShowCommands(false); }}
                onKeyDown={handleKeyDown}
                rows={1}
                onInput={e => { const t = e.currentTarget; t.style.height = 'auto'; t.style.height = `${Math.min(t.scrollHeight, 128)}px`; }}
                disabled={streaming}
              />
              {input.startsWith('/') && showCommands && (
                <div className="absolute bottom-full left-0 right-0 mb-1 bg-slate-900 border border-white/10 rounded-xl overflow-hidden shadow-xl z-10">
                  <div className="px-3 py-1.5 text-[9px] text-slate-500 uppercase tracking-wider bg-white/[0.02]">Commands</div>
                  {['/help', '/status', '/agents', '/skills', '/code', '/crm', '/files', '/read'].map(cmd => {
                    const matched = input.length <= 1 || cmd.startsWith(input.toLowerCase());
                    if (!matched) return null;
                    return (
                      <button key={cmd} onClick={() => { setInput(cmd + ' '); setShowCommands(false); inputRef.current?.focus(); }}
                        className="w-full text-left flex items-center gap-2.5 px-3 py-2 text-xs text-slate-300 hover:bg-white/5 transition-colors">
                        <Hash className="w-3 h-3 text-lumina-400" />
                        {cmd}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            <button
              onClick={streaming ? stopStreaming : send}
              disabled={!streaming && (!input.trim() || loading)}
              className={`rounded-2xl p-3.5 transition-all duration-200 shadow-lg ${
                streaming
                  ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20'
                  : 'bg-gradient-to-r from-lumina-500 to-lumina-600 hover:from-lumina-400 hover:to-lumina-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 shadow-lumina-500/20 hover:shadow-lumina-500/30 disabled:shadow-none'
              }`}
            >
              {streaming ? <X className="w-4 h-4" /> : loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-[9px] text-slate-600 mt-1.5 text-center">
            Agent: {agent} · {streaming ? 'Streaming...' : `${messages.length} messages`}
          </p>
        </div>
      </div>
    </div>
  );
}
