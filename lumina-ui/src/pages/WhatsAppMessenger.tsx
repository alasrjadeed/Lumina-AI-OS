import { useEffect, useState } from 'react';
import {
  MessageSquare, Send, CheckCircle, XCircle, QrCode, Smartphone,
  Loader2, RefreshCw, Copy, Clock, Trash2, History, FileText,
  Image, Phone, ExternalLink, AlertCircle, Star, Zap,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';
import { api } from '../api';

export default function WhatsAppMessenger() {
  const [tab, setTab] = useState('send');
  const [to, setTo] = useState('');
  const [message, setMessage] = useState('');
  const [templateName, setTemplateName] = useState('');
  const [paramsStr, setParamsStr] = useState('');
  const [sent, setSent] = useState<Array<{ to: string; msg: string; ok: boolean; timestamp: number }>>([]);
  const [status, setStatus] = useState<{ configured: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const { addToast } = useToast();

  useEffect(() => {
    api.whatsappStatus().then(setStatus).catch(() => {});
  }, []);

  const [qrTab, setQrTab] = useState<'cloud' | 'web'>('cloud');

  const sendText = async () => {
    if (!to.trim() || !message.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/whatsapp/send/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to: to.trim(), text: message }),
      });
      const data = await res.json();
      const ok = !data?.error && !(data?.message && data.message.includes('Error'));
      setSent(l => [{ to, msg: message, ok, timestamp: Date.now() }, ...l]);
      if (ok) addToast('Message sent', 'success');
      else addToast(data.error || 'Failed to send', 'error');
      setMessage('');
    } catch {
      setSent(l => [{ to, msg: message, ok: false, timestamp: Date.now() }, ...l]);
      addToast('Failed to send', 'error');
    } finally { setLoading(false); }
  };

  const sendTemplate = async () => {
    if (!to.trim() || !templateName.trim()) return;
    setLoading(true);
    try {
      const params = paramsStr ? paramsStr.split(',').map(s => s.trim()) : [];
      const res = await fetch('/api/whatsapp/send/template', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ to: to.trim(), template_name: templateName, params }),
      });
      const data = await res.json();
      const ok = !data?.error;
      setSent(l => [{ to, msg: `Template: ${templateName}`, ok, timestamp: Date.now() }, ...l]);
      if (ok) addToast('Template sent', 'success');
      else addToast(data.error || 'Failed', 'error');
    } catch {
      setSent(l => [{ to, msg: `Template: ${templateName}`, ok: false, timestamp: Date.now() }, ...l]);
      addToast('Failed to send template', 'error');
    } finally { setLoading(false); }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    addToast('Copied', 'success');
  };

  const filteredHistory = sent.filter(s =>
    s.to.includes(historySearch) || s.msg.toLowerCase().includes(historySearch.toLowerCase())
  );

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        icon={MessageSquare}
        title="WhatsApp Messenger"
        description="Send messages, manage templates"
        status={status && !status.configured ? (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            <span className="text-[10px] text-amber-400">Not configured</span>
          </div>
        ) : undefined}
      />

      <div className="flex gap-1 mt-4 mb-5 bg-white/5 rounded-xl p-1 w-fit border border-white/5">
        {(['send', 'template', 'qr', 'history'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              tab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {t === 'send' ? <Send className="w-3.5 h-3.5" /> : t === 'template' ? <FileText className="w-3.5 h-3.5" /> : t === 'qr' ? <QrCode className="w-3.5 h-3.5" /> : <History className="w-3.5 h-3.5" />}
            {t === 'send' ? 'Text' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {tab === 'send' && (
          <div className="max-w-lg space-y-4">
            <Card>
              <CardSection label="Send Text Message">
                <div className="space-y-3">
                  <div className="relative">
                    <Phone className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="text" value={to} onChange={e => setTo(e.target.value)}
                      placeholder="Recipient phone number (e.g. 1234567890)"
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 transition-colors"
                    />
                  </div>
                  <textarea value={message} onChange={e => setMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 resize-none h-24 transition-colors"
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500">{message.length} chars</span>
                    <button onClick={sendText} disabled={loading || !to.trim() || !message.trim()}
                      className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl text-xs font-medium text-white disabled:opacity-40 hover:from-emerald-400 hover:to-emerald-500 transition-all shadow-lg shadow-emerald-500/20"
                    >{loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                      {loading ? 'Sending...' : 'Send'}
                    </button>
                  </div>
                </div>
              </CardSection>
            </Card>

            <Card>
              <CardSection label="Quick Actions">
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Business Stats', action: () => fetch('/api/whatsapp/business/stats').then(r => r.json()).then(d => addToast(`Business stats loaded: ${JSON.stringify(d).slice(0, 100)}...`, 'info')) },
                    { label: 'List Templates', action: () => fetch('/api/whatsapp/templates').then(r => r.json())                      .then(d => addToast(`Found ${d.templates?.length || 0} templates`, 'info')) },
                  ].map(({ label: lbl, action }) => (
                    <button key={lbl} onClick={action}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-300 hover:bg-white/5 border border-white/5 transition-all"
                    ><Zap className="w-3.5 h-3.5 text-slate-400" />{lbl}</button>
                  ))}
                </div>
              </CardSection>
            </Card>
          </div>
        )}

        {tab === 'template' && (
          <div className="max-w-lg">
            <Card>
              <CardSection label="Send Template Message">
                <div className="space-y-3">
                  <div className="relative">
                    <Phone className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="text" value={to} onChange={e => setTo(e.target.value)}
                      placeholder="Recipient phone number"
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 transition-colors"
                    />
                  </div>
                  <div className="relative">
                    <FileText className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input type="text" value={templateName} onChange={e => setTemplateName(e.target.value)}
                      placeholder="Template name (e.g. hello_world)"
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 transition-colors"
                    />
                  </div>
                  <input type="text" value={paramsStr} onChange={e => setParamsStr(e.target.value)}
                    placeholder="Template params (comma separated, e.g. John, order-123)"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 transition-colors"
                  />
                  <p className="text-[10px] text-slate-500">Leave params empty if the template has no variables</p>
                  <button onClick={sendTemplate} disabled={loading || !to.trim() || !templateName.trim()}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl text-xs font-medium text-white disabled:opacity-40 hover:from-emerald-400 hover:to-emerald-500 transition-all shadow-lg shadow-emerald-500/20"
                  >{loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                    {loading ? 'Sending...' : 'Send Template'}
                  </button>
                </div>
              </CardSection>
            </Card>
          </div>
        )}

        {tab === 'qr' && (
          <div className="max-w-lg mx-auto space-y-6">
            <div className="flex gap-1 bg-white/5 rounded-xl p-1 w-fit border border-white/5 mx-auto">
              {(['cloud', 'web'] as const).map(t => (
                <button key={t} onClick={() => setQrTab(t)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                    qrTab === t ? 'bg-lumina-500/20 text-lumina-300 shadow-sm' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >{t === 'cloud' ? <MessageSquare className="w-3.5 h-3.5" /> : <QrCode className="w-3.5 h-3.5" />}
                  {t === 'cloud' ? 'Cloud API' : 'WhatsApp Web'}
                </button>
              ))}
            </div>

            {qrTab === 'cloud' ? (
              <Card>
                <CardSection label="Meta WhatsApp Cloud API">
                  <div className="text-left space-y-4">
                    <p className="text-xs text-slate-400">Free up to 1,000 conversations/month. Official API — your account won't be blocked.</p>
                    <div className="bg-white/[0.03] rounded-xl p-4 space-y-2">
                      <p className="text-xs font-medium text-slate-300 flex items-center gap-2"><Star className="w-3.5 h-3.5 text-emerald-400" /> Get your free API token:</p>
                      <ol className="space-y-2 text-xs text-slate-400">
                        {[
                          'Go to developers.facebook.com',
                          'Create or open your WhatsApp Business App',
                          'Go to WhatsApp → Quickstart',
                          'Copy the Temporary Access Token',
                          'Paste it in .env as WHATSAPP_API_KEY',
                        ].map((step, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold shrink-0">{i + 1}</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                    <a href="https://developers.facebook.com" target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                    ><ExternalLink className="w-3.5 h-3.5" />Open Meta Developer Portal</a>
                  </div>
                </CardSection>
              </Card>
            ) : (
              <Card>
                <CardSection label="WhatsApp Web">
                  <div className="text-center py-8">
                    <QrCode className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-sm text-slate-300 mb-2">WhatsApp Web via Playwright</p>
                    <p className="text-xs text-slate-500">Use the WhatsApp Web automation script from the terminal:</p>
                    <pre className="mt-4 bg-slate-900 rounded-xl p-4 text-xs text-left text-slate-300 font-mono overflow-x-auto">
                      python scripts/login.py
                    </pre>
                    <p className="text-xs text-slate-500 mt-3">Open WhatsApp on your phone → Linked Devices → Link a Device</p>
                  </div>
                </CardSection>
              </Card>
            )}
          </div>
        )}

        {tab === 'history' && (
          <CardSection label="Sent Messages" action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Send className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input type="text" value={historySearch} onChange={e => setHistorySearch(e.target.value)}
                  placeholder="Search..." className="bg-white/5 border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500/50 w-36"
                />
              </div>
              <span className="text-[10px] text-slate-500">{sent.length} total</span>
              {sent.length > 0 && (
                <button onClick={() => setSent([])}
                  className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                ><Trash2 className="w-3.5 h-3.5" /></button>
              )}
            </div>
          }>
            {filteredHistory.length === 0 ? (
              <div className="text-center py-12">
                <Send className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                <p className="text-sm text-slate-500">{sent.length === 0 ? 'No messages sent yet' : 'No matches'}</p>
              </div>
            ) : (
              <div className="space-y-1 divide-y divide-white/[0.03]">
                {filteredHistory.map((s, i) => (
                  <div key={i} className="flex items-start gap-3 px-3 py-2.5 text-xs group">
                    {s.ok
                      ? <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      : <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    }
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-mono text-slate-400">{s.to}</p>
                      <p className="text-sm text-slate-200 truncate">{s.msg}</p>
                      <span className="text-[10px] text-slate-500">{new Date(s.timestamp).toLocaleString()}</span>
                    </div>
                    <button onClick={() => copyToClipboard(s.msg)}
                      className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
                    ><Copy className="w-3.5 h-3.5" /></button>
                  </div>
                ))}
              </div>
            )}
          </CardSection>
        )}
      </div>
    </div>
  );
}
