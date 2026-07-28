import { useState, useEffect } from 'react';
import { Mail, Send, Plus, Trash2, Play, Settings2, FileText, Upload, RefreshCw, Eye, CheckCircle, XCircle, Clock } from 'lucide-react';
import Card from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api';

async function get<T>(path: string): Promise<T> { const r = await fetch(`${BASE}${path}`); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function post<T>(path: string, body?: any): Promise<T> { const r = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: body ? JSON.stringify(body) : undefined }); if (!r.ok) throw new Error(await r.text()); return r.json(); }
async function del(path: string): Promise<any> { const r = await fetch(`${BASE}${path}`, { method: 'DELETE' }); if (!r.ok) throw new Error(await r.text()); return r.json(); }

function StatCard({ label, value, color = 'brand' }: { label: string; value: string | number; color?: string }) {
  const colors: Record<string, string> = { brand: 'var(--brand-500)', green: 'var(--color-success)', amber: 'var(--color-warning)', red: 'var(--color-error)' };
  return <div className="bg-[var(--bg-tertiary)] rounded-xl p-4"><p className="text-2xs text-[var(--text-tertiary)] uppercase tracking-wider">{label}</p><p className="text-2xl font-bold mt-1" style={{ color: colors[color] }}>{value}</p></div>;
}

function Skeleton({ h = 'h-8' }: { h?: string }) { return <div className={`skeleton ${h} w-full`} />; }

export default function EmailCampaigns() {
  const [tab, setTab] = useState<'campaigns' | 'templates' | 'smtp' | 'send'>('campaigns');
  const [smtp, setSmtp] = useState<any>(null);
  const [smtpForm, setSmtpForm] = useState({ host: '', port: 587, username: '', password: '', use_tls: true });
  const [templates, setTemplates] = useState<any[]>([]);
  const [templateForm, setTemplateForm] = useState({ name: '', subject: '', body: '', is_html: false });
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [campaignForm, setCampaignForm] = useState({ name: '', template: '', recipients: '' });
  const [sendForm, setSendForm] = useState({ to: '', subject: '', body: '', is_html: false });
  const [loading, setLoading] = useState(true);
  const [importCampaign, setImportCampaign] = useState('');
  const [importCol, setImportCol] = useState('email');
  const [importPath, setImportPath] = useState('');
  const { addToast } = useToast();

  useEffect(() => { loadAll(); }, [tab]);

  async function loadAll() {
    setLoading(true);
    try {
      if (tab === 'campaigns') setCampaigns((await get('/email/campaigns')).campaigns || []);
      if (tab === 'templates') setTemplates((await get('/email/templates')).templates || []);
      if (tab === 'smtp') setSmtp(await get('/email/smtp'));
    } catch (e: any) { addToast(e.message, 'error'); }
    setLoading(false);
  }

  async function handleSaveSmtp() {
    try { await post('/email/smtp', smtpForm); addToast('SMTP saved', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleCreateTemplate() {
    try { await post('/email/templates', templateForm); setTemplateForm({ name: '', subject: '', body: '', is_html: false }); addToast('Template created', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleDeleteTemplate(name: string) {
    try { await del(`/email/templates/${encodeURIComponent(name)}`); addToast('Template deleted', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleCreateCampaign() {
    const recipients = campaignForm.recipients.split('\n').map(r => r.trim()).filter(Boolean);
    try { await post('/email/campaigns', { ...campaignForm, recipients }); setCampaignForm({ name: '', template: '', recipients: '' }); addToast('Campaign created', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleRunCampaign(name: string) {
    try { await post(`/email/campaigns/${encodeURIComponent(name)}/run`); addToast('Campaign running', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleDeleteCampaign(name: string) {
    try { await del(`/email/campaigns/${encodeURIComponent(name)}`); addToast('Campaign deleted', 'success'); loadAll(); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleSend() {
    try { await post('/email/send', sendForm); addToast('Email sent', 'success'); setSendForm({ to: '', subject: '', body: '', is_html: false }); } catch (e: any) { addToast(e.message, 'error'); }
  }
  async function handleImport() {
    try { const r = await post(`/email/campaigns/${encodeURIComponent(importCampaign)}/import?csv_path=${encodeURIComponent(importPath)}&email_column=${importCol}`); addToast(`Imported ${r.imported} recipients`, 'success'); } catch (e: any) { addToast(e.message, 'error'); }
  }

  const tabs = [
    { id: 'campaigns' as const, label: 'Campaigns', icon: Mail },
    { id: 'templates' as const, label: 'Templates', icon: FileText },
    { id: 'smtp' as const, label: 'SMTP Config', icon: Settings2 },
    { id: 'send' as const, label: 'Quick Send', icon: Send },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-primary)] shrink-0">
        <div><h1 className="text-xl font-semibold">Email Campaigns</h1><p className="text-sm text-[var(--text-secondary)] mt-0.5">SMTP config, templates, campaigns, and sending</p></div>
      </div>
      <div className="flex items-center gap-1 px-4 py-2 border-b border-[var(--border-primary)] shrink-0">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg transition-colors ${tab === t.id ? 'bg-[var(--bg-active)] text-[var(--text-brand)] border border-[var(--border-brand)]' : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {/* CAMPAIGNS TAB */}
        {tab === 'campaigns' && (
          <div className="space-y-6">
            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">Create Campaign</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="input-group"><label className="input-label">Campaign Name</label><input className="input" value={campaignForm.name} onChange={e => setCampaignForm(p => ({ ...p, name: e.target.value }))} placeholder="Summer promo" /></div>
                <div className="input-group"><label className="input-label">Template</label><select className="select" value={campaignForm.template} onChange={e => setCampaignForm(p => ({ ...p, template: e.target.value }))}><option value="">Select template</option>{templates.map(t => <option key={t.name} value={t.name}>{t.name}</option>)}</select></div>
                <div className="flex items-end"><button onClick={handleCreateCampaign} className="btn btn-primary"><Plus className="w-4 h-4" /> Create</button></div>
              </div>
              <div className="input-group"><label className="input-label">Recipients (one per line)</label><textarea className="input h-20" value={campaignForm.recipients} onChange={e => setCampaignForm(p => ({ ...p, recipients: e.target.value }))} placeholder="user1@example.com&#10;user2@example.com" /></div>
            </div></Card>

            <Card><div className="space-y-3">
              <h2 className="text-lg font-semibold">Import Recipients</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                <div className="input-group"><label className="input-label">Campaign</label><select className="select" value={importCampaign} onChange={e => setImportCampaign(e.target.value)}><option value="">Select</option>{campaigns.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}</select></div>
                <div className="input-group"><label className="input-label">CSV Path</label><input className="input" value={importPath} onChange={e => setImportPath(e.target.value)} placeholder="/path/to/recipients.csv" /></div>
                <button onClick={handleImport} className="btn btn-secondary"><Upload className="w-4 h-4" /> Import</button>
              </div>
            </div></Card>

            {loading ? <div className="space-y-2">{Array(3).fill(0).map((_,i) => <Skeleton key={i} h="h-16" />)}</div> : campaigns.length === 0 ? <div className="text-center py-12 text-[var(--text-tertiary)]"><Mail className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No campaigns yet</p></div>
            : <div className="space-y-2">
              {campaigns.map((c: any) => (
                <div key={c.name} className="bg-[var(--bg-tertiary)] rounded-xl p-4 flex items-center justify-between hover:bg-[var(--bg-hover)] transition-colors">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{c.name}</span>
                      <span className={`badge ${c.status === 'sent' ? 'badge-success' : c.status === 'running' ? 'badge-warning' : c.status === 'failed' ? 'badge-error' : 'badge-info'}`}>{c.status}</span>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-[var(--text-secondary)]">
                      <span>Template: {c.template}</span>
                      <span>Recipients: {c.recipients_count}</span>
                      {c.sent && <span style={{ color: 'var(--color-success)' }}>Sent: {c.sent}</span>}
                      {c.failed && <span style={{ color: 'var(--color-error)' }}>Failed: {c.failed}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleRunCampaign(c.name)} className="btn btn-primary btn-sm"><Play className="w-3 h-3" /> Run</button>
                    <button onClick={() => handleDeleteCampaign(c.name)} className="btn btn-ghost btn-sm text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                </div>
              ))}
            </div>}
          </div>
        )}

        {/* TEMPLATES TAB */}
        {tab === 'templates' && (
          <div className="space-y-6">
            <Card><div className="space-y-4">
              <h2 className="text-lg font-semibold">New Template</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="input-group"><label className="input-label">Name</label><input className="input" value={templateForm.name} onChange={e => setTemplateForm(p => ({ ...p, name: e.target.value }))} placeholder="welcome_email" /></div>
                <div className="input-group"><label className="input-label">Subject</label><input className="input" value={templateForm.subject} onChange={e => setTemplateForm(p => ({ ...p, subject: e.target.value }))} placeholder="Welcome to Lumina" /></div>
              </div>
              <div className="input-group"><label className="input-label">Body</label><textarea className="input h-32" value={templateForm.body} onChange={e => setTemplateForm(p => ({ ...p, body: e.target.value }))} placeholder="Hi {{name}}, welcome..." /></div>
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer"><input type="checkbox" checked={templateForm.is_html} onChange={e => setTemplateForm(p => ({ ...p, is_html: e.target.checked }))} className="w-3.5 h-3.5 rounded accent-[var(--brand-500)]" /> HTML Template</label>
                <button onClick={handleCreateTemplate} className="btn btn-primary"><Plus className="w-4 h-4" /> Create Template</button>
              </div>
            </div></Card>

            {loading ? <div className="space-y-2">{Array(3).fill(0).map((_,i) => <Skeleton key={i} h="h-16" />)}</div> : templates.length === 0 ? <div className="text-center py-12 text-[var(--text-tertiary)]"><FileText className="w-12 h-12 mx-auto mb-3 opacity-30" /><p>No templates yet</p></div>
            : <div className="space-y-2">
              {templates.map((t: any) => (
                <div key={t.name} className="bg-[var(--bg-tertiary)] rounded-xl p-4 flex items-center justify-between hover:bg-[var(--bg-hover)] transition-colors">
                  <div>
                    <div className="flex items-center gap-2"><span className="font-medium">{t.name}</span>{t.is_html && <span className="badge badge-brand">HTML</span>}</div>
                    <p className="text-sm text-[var(--text-secondary)] mt-0.5">{t.subject}</p>
                    {t.variables && t.variables.length > 0 && <p className="text-2xs text-[var(--text-tertiary)] mt-1">Variables: {t.variables.join(', ')}</p>}
                  </div>
                  <button onClick={() => handleDeleteTemplate(t.name)} className="btn btn-ghost btn-sm text-red-400"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              ))}
            </div>}
          </div>
        )}

        {/* SMTP TAB */}
        {tab === 'smtp' && (
          <Card><div className="space-y-4">
            <h2 className="text-lg font-semibold">SMTP Configuration</h2>
            {smtp && !smtpForm.host && <div className="text-sm text-[var(--text-secondary)] mb-2">Current host: {smtp.host || 'Not configured'}</div>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="input-group"><label className="input-label">Host</label><input className="input" value={smtpForm.host} onChange={e => setSmtpForm(p => ({ ...p, host: e.target.value }))} placeholder="smtp.gmail.com" /></div>
              <div className="input-group"><label className="input-label">Port</label><input className="input" type="number" value={smtpForm.port} onChange={e => setSmtpForm(p => ({ ...p, port: +e.target.value }))} /></div>
              <div className="input-group"><label className="input-label">Username</label><input className="input" value={smtpForm.username} onChange={e => setSmtpForm(p => ({ ...p, username: e.target.value }))} placeholder="user@gmail.com" /></div>
              <div className="input-group"><label className="input-label">Password</label><input className="input" type="password" value={smtpForm.password} onChange={e => setSmtpForm(p => ({ ...p, password: e.target.value }))} /></div>
            </div>
            <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer"><input type="checkbox" checked={smtpForm.use_tls} onChange={e => setSmtpForm(p => ({ ...p, use_tls: e.target.checked }))} className="w-3.5 h-3.5 rounded accent-[var(--brand-500)]" /> Use TLS</label>
            <button onClick={handleSaveSmtp} className="btn btn-primary"><Settings2 className="w-4 h-4" /> Save Configuration</button>
          </div></Card>
        )}

        {/* QUICK SEND TAB */}
        {tab === 'send' && (
          <Card><div className="space-y-4">
            <h2 className="text-lg font-semibold">Quick Send</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="input-group"><label className="input-label">To</label><input className="input" value={sendForm.to} onChange={e => setSendForm(p => ({ ...p, to: e.target.value }))} placeholder="recipient@example.com" /></div>
              <div className="input-group"><label className="input-label">Subject</label><input className="input" value={sendForm.subject} onChange={e => setSendForm(p => ({ ...p, subject: e.target.value }))} placeholder="Hello from Lumina" /></div>
            </div>
            <div className="input-group"><label className="input-label">Body</label><textarea className="input h-32" value={sendForm.body} onChange={e => setSendForm(p => ({ ...p, body: e.target.value }))} placeholder="Your message here..." /></div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer"><input type="checkbox" checked={sendForm.is_html} onChange={e => setSendForm(p => ({ ...p, is_html: e.target.checked }))} className="w-3.5 h-3.5 rounded accent-[var(--brand-500)]" /> HTML</label>
              <button onClick={handleSend} className="btn btn-primary"><Send className="w-4 h-4" /> Send Email</button>
            </div>
          </div></Card>
        )}
      </div>
    </div>
  );
}
