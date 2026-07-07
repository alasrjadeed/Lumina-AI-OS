import { useEffect, useState } from 'react';
import {
  Store, MessageSquare, Phone, QrCode, Settings, Send, Plus, Trash2, Upload, Download, Bot,
  Package, DollarSign, TrendingUp, Grid3X3, Image, Loader2, CheckCircle, XCircle, Smartphone,
  Globe, Search, User, Clock, ChevronDown, Copy, Camera,
} from 'lucide-react';

interface Product { id: string; name: string; description: string; price: number; image_url: string; category: string; status: string; }
interface Stats { total_products: number; total_value: number; avg_price: number; by_category: Record<string, number>; drafts: number; published: number; }

export default function WhatsAppBusiness() {
  const [tab, setTab] = useState('dashboard');
  const [products, setProducts] = useState<Product[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState('');

  // Product form
  const [name, setName] = useState(''); const [desc, setDesc] = useState('');
  const [price, setPrice] = useState(''); const [imageUrl, setImageUrl] = useState('');
  const [category, setCategory] = useState('');

  // Chat
  const [to, setTo] = useState(''); const [message, setMessage] = useState('');
  const [sent, setSent] = useState<Array<{ to: string; msg: string; ok: boolean }>>([]);

  const fetchData = () => {
    fetch('/api/whatsapp/business/stats').then(r => r.json()).then(setStats).catch(() => {});
    fetch('/api/whatsapp/business/products').then(r => r.json()).then(d => setProducts(d.products || [])).catch(() => {});
    fetch('/api/whatsapp/status').then(r => r.json()).then(setStatus).catch(() => {});
  };
  useEffect(fetchData, []);

  const addProduct = async () => {
    if (!name.trim()) return;
    const res = await fetch('/api/whatsapp/business/products', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description: desc, price: parseFloat(price) || 0, image_url: imageUrl, category }),
    });
    const d = await res.json(); setMsg(`✅ Added: ${d.name}`);
    setName(''); setDesc(''); setPrice(''); setImageUrl(''); setCategory('');
    setShowAdd(false); fetchData(); setTimeout(() => setMsg(''), 2000);
  };

  const deleteProduct = async (id: string) => {
    try { await fetch(`/api/whatsapp/business/products/${id}`, { method: 'DELETE' }); fetchData(); } catch {}
  };

  const autoUpload = async () => {
    setUploading(true);
    try { await fetch('/api/whatsapp/business/auto-upload', { method: 'POST' }); setMsg('✅ Auto-upload done!'); fetchData(); } catch { setMsg('❌ Failed'); }
    setUploading(false);
  };

  const sendMsg = async () => {
    if (!to.trim() || !message.trim()) return;
    try {
      const res = await fetch('/api/whatsapp/send/text', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ to: to.trim(), text: message }) });
      const data = await res.json();
      setSent(l => [...l, { to, msg: message, ok: !data.error }]);
      setMessage('');
    } catch { setSent(l => [...l, { to, msg: message, ok: false }]); }
  };

  const totalValue = products.reduce((a, p) => a + p.price, 0);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Store },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'products', label: 'Products', icon: Package },
    { id: 'calls', label: 'Calls', icon: Phone },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3"><Store className="w-6 h-6 text-lumina-400" /> WhatsApp Business</h1>
          <p className="text-sm text-slate-400 mt-0.5">Messaging, catalog & business tools</p>
        </div>
        {msg && <span className="text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-full">{msg}</span>}
      </div>

      {/* Status bar */}
      <div className="flex items-center gap-4 px-4 py-2.5 rounded-xl bg-white/[0.02] border border-white/5 text-xs">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${status?.configured ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          <span className="text-slate-400">API: {status?.configured ? 'Connected' : 'Not configured'}</span>
        </div>
        <div className="w-px h-4 bg-white/5" />
        <span className="text-slate-400">{stats?.total_products || 0} products</span>
        <div className="w-px h-4 bg-white/5" />
        <span className="text-slate-400">{sent.length} messages sent</span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
        <StatCard icon={Package} label="Products" value={String(stats?.total_products || 0)} color="lumina" />
        <StatCard icon={DollarSign} label="Total Value" value={`$${(stats?.total_value || 0).toLocaleString()}`} color="emerald" />
        <StatCard icon={TrendingUp} label="Avg Price" value={`$${stats?.avg_price || '0'}`} color="violet" />
        <StatCard icon={CheckCircle} label="Published" value={String(stats?.published || 0)} color="blue" />
        <StatCard icon={Grid3X3} label="Categories" value={String(Object.keys(stats?.by_category || {}).length)} color="amber" />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/5 pb-1 overflow-x-auto">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm rounded-t-xl transition-all whitespace-nowrap ${
              tab === t.id ? 'bg-white/5 text-lumina-300 border-b-2 border-lumina-500 font-medium' : 'text-slate-500 hover:text-slate-300'
            }`}><t.icon className="w-4 h-4" />{t.label}</button>
        ))}
      </div>

      {/* ─── DASHBOARD ─── */}
      {tab === 'dashboard' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bento-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <button onClick={() => setTab('chat')} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm text-slate-300 transition-all"><MessageSquare className="w-4 h-4 text-lumina-400" /> Send Message</button>
              <button onClick={() => setShowAdd(true)} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm text-slate-300 transition-all"><Plus className="w-4 h-4 text-emerald-400" /> Add Product</button>
              <button onClick={autoUpload} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm text-slate-300 transition-all"><Bot className="w-4 h-4 text-violet-400" /> Auto-Upload Catalog</button>
              <button onClick={() => setTab('settings')} className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm text-slate-300 transition-all"><QrCode className="w-4 h-4 text-amber-400" /> Pair WhatsApp Device</button>
            </div>
          </div>
          <div className="bento-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Overview</h3>
            <div className="space-y-3">
              <div><p className="text-xs text-slate-400">Catalog Status</p><p className="text-sm text-slate-200">{stats?.total_products ? `${stats.published} published, ${stats.drafts} drafts` : 'Empty catalog'}</p></div>
              <div className="h-px bg-white/5" />
              <div><p className="text-xs text-slate-400">Categories</p><div className="flex flex-wrap gap-1.5 mt-1">
                {Object.entries(stats?.by_category || {}).map(([c, n]) => (
                  <span key={c} className="px-2 py-0.5 rounded-full bg-white/5 text-[10px] text-slate-400">{c || 'Uncategorized'} ({n})</span>
                ))}
                {!Object.keys(stats?.by_category || {}).length && <span className="text-xs text-slate-600">No categories</span>}
              </div></div>
              <div className="h-px bg-white/5" />
              <div><p className="text-xs text-slate-400">API</p><p className="text-sm text-slate-200">{status?.configured ? '✅ Connected' : '⏳ Pending (Meta review)'}</p></div>
            </div>
          </div>
        </div>
      )}

      {/* ─── CHAT ─── */}
      {tab === 'chat' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Contacts */}
          <div className="bento-card">
            <div className="flex items-center gap-2 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
                <input className="w-full bg-white/5 border border-white/10 rounded-xl pl-8 pr-3 py-2 text-xs text-white outline-none focus:border-lumina-500/50" placeholder="Search contacts..." />
              </div>
            </div>
            <div className="space-y-1">
              {sent.length === 0 && <p className="text-xs text-slate-600 text-center py-8">No conversations yet.<br />Send a message to start.</p>}
              {[...new Set(sent.map(s => s.to))].map((num, i) => (
                <div key={i} onClick={() => setTo(num)} className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/5 cursor-pointer transition-colors">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center text-white text-xs font-bold">{num.slice(-2)}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-slate-200 truncate font-medium">{num}</p>
                    <p className="text-[10px] text-slate-500 truncate">{sent.filter(s => s.to === num).pop()?.msg.slice(0, 30)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Chat Area */}
          <div className="lg:col-span-2 bento-card flex flex-col">
            <div className="flex-1 overflow-auto space-y-3 mb-4 min-h-[300px]">
              {sent.filter(s => s.to === to).map((s, i) => (
                <div key={i} className={`flex gap-3 ${s.ok ? '' : 'opacity-60'}`}>
                  <div className="w-7 h-7 rounded-full bg-lumina-600 flex items-center justify-center shrink-0"><User className="w-3.5 h-3.5 text-white" /></div>
                  <div>
                    <p className="text-xs text-slate-400">{s.to}</p>
                    <div className={`mt-1 px-4 py-2 rounded-2xl text-sm ${s.ok ? 'bg-lumina-600/20 text-slate-200' : 'bg-red-500/20 text-red-300'}`}>
                      {s.msg}
                    </div>
                  </div>
                </div>
              ))}
              {sent.length === 0 && <div className="text-center py-12 text-slate-600 text-sm">Select a contact or send a new message</div>}
            </div>
            <div className="flex gap-2 pt-3 border-t border-white/5">
              <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Phone number" value={to} onChange={e => setTo(e.target.value)} />
              <input className="flex-[2] bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50" placeholder="Type a message..." value={message} onChange={e => setMessage(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMsg()} />
              <button onClick={sendMsg} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-4 py-2.5"><Send className="w-4 h-4" /></button>
            </div>
          </div>
        </div>
      )}

      {/* ─── PRODUCTS ─── */}
      {tab === 'products' && (
        <div className="bento-card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Catalog ({products.length})</h3>
            <div className="flex gap-2">
              <button onClick={() => setShowAdd(true)} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-3 py-1.5 text-xs font-medium flex items-center gap-1"><Plus className="w-3 h-3" /> Add</button>
              <button onClick={autoUpload} disabled={uploading} className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white rounded-xl px-3 py-1.5 text-xs font-medium flex items-center gap-1">
                {uploading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Bot className="w-3 h-3" />} Auto
              </button>
              <button onClick={async () => { const res = await fetch('/api/whatsapp/business/export'); const d = await res.json(); setMsg(`✅ Exported ${d.count}`); }} className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-3 py-1.5 text-xs flex items-center gap-1"><Download className="w-3 h-3" /> Export</button>
            </div>
          </div>
          {showAdd && (
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4 p-4 bg-white/5 rounded-xl border border-white/5">
              <input className="bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-lumina-500/50" placeholder="Name *" value={name} onChange={e => setName(e.target.value)} />
              <input className="bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-lumina-500/50" placeholder="Description" value={desc} onChange={e => setDesc(e.target.value)} />
              <input className="bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-lumina-500/50" placeholder="Price $" type="number" value={price} onChange={e => setPrice(e.target.value)} />
              <input className="bg-slate-950 border border-white/10 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-lumina-500/50" placeholder="Image URL" value={imageUrl} onChange={e => setImageUrl(e.target.value)} />
              <div className="flex gap-2">
                <button onClick={addProduct} className="flex-1 bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-3 py-2 text-xs font-medium">Add</button>
                <button onClick={() => setShowAdd(false)} className="px-3 py-2 text-xs text-slate-400 hover:text-slate-200">Cancel</button>
              </div>
            </div>
          )}
          <div className="space-y-1">
            {products.map(p => (
              <div key={p.id} className="flex items-center gap-4 px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-all group">
                {p.image_url ? <img src={p.image_url} alt={p.name} className="w-10 h-10 rounded-xl object-cover" />
                  : <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center"><Image className="w-4 h-4 text-white" /></div>}
                <div className="flex-1 min-w-0"><p className="text-sm text-slate-200 truncate">{p.name}</p><p className="text-xs text-slate-500 truncate">{p.category || 'No category'}</p></div>
                <div className="text-right shrink-0"><p className="text-sm font-semibold text-lumina-400">${p.price.toFixed(2)}</p><span className={`text-[10px] px-1.5 py-0.5 rounded-full ${p.status === 'published' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>{p.status}</span></div>
                <button onClick={() => deleteProduct(p.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100"><Trash2 className="w-4 h-4" /></button>
              </div>
            ))}
            {products.length === 0 && <p className="text-sm text-slate-500 text-center py-8">Catalog is empty. Add your first product.</p>}
          </div>
        </div>
      )}

      {/* ─── CALLS ─── */}
      {tab === 'calls' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bento-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2 mb-4"><Phone className="w-4 h-4" /> Make a Call</h3>
            <div className="space-y-4">
              <input className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-lumina-500/50 font-mono" placeholder="Phone number with country code" value={to} onChange={e => setTo(e.target.value)} />
              <div className="flex gap-3">
                <button onClick={async () => {
                  if (!to.trim()) return;
                  setMsg('🔊 Initiating voice call via browser...');
                  try {
                    await fetch('/api/browser/agent', {
                      method: 'POST', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ task: `Go to web.whatsapp.com, search for the contact with phone number ${to}, open the chat, and click the voice call button. If not logged in, just report the status.`, headless: false }),
                    });
                  } catch {}
                  setTimeout(() => setMsg(''), 3000);
                }} className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl py-3 text-sm font-medium flex items-center justify-center gap-2 transition-all">
                  <Phone className="w-4 h-4" /> Voice Call
                </button>
                <button onClick={async () => {
                  if (!to.trim()) return;
                  setMsg('📹 Initiating video call...');
                  try {
                    await fetch('/api/browser/agent', {
                      method: 'POST', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ task: `Go to web.whatsapp.com, find contact ${to}, open chat, click the video call button. Report status.`, headless: false }),
                    });
                  } catch {}
                  setTimeout(() => setMsg(''), 3000);
                }} className="flex-1 bg-violet-600 hover:bg-violet-500 text-white rounded-xl py-3 text-sm font-medium flex items-center justify-center gap-2 transition-all">
                  <Camera className="w-4 h-4" /> Video Call
                </button>
              </div>
              <div className="bg-white/5 rounded-xl p-4 text-xs text-slate-500">
                <p className="font-medium text-slate-400 mb-1">How it works:</p>
                <p>The browser agent opens WhatsApp Web and clicks the call button. Make sure you're logged into WhatsApp Web first.</p>
              </div>
            </div>
          </div>
          <div className="bento-card">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2 mb-4"><Clock className="w-4 h-4" /> Call History</h3>
            <div className="text-center py-12 text-sm text-slate-500">
              <Phone className="w-12 h-12 mx-auto mb-3 text-slate-600 opacity-50" />
              <p>No call history yet</p>
              <p className="text-xs text-slate-600 mt-1">Calls placed here will appear in history</p>
            </div>
          </div>
        </div>
      )}

      {/* ─── SETTINGS ─── */}
      {tab === 'settings' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bento-card space-y-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Settings className="w-4 h-4" /> API Configuration</h3>
            <div className="flex items-center justify-between py-2">
              <div><p className="text-sm text-slate-200">Meta Cloud API</p><p className="text-xs text-slate-500">Free up to 1,000 convos/month</p></div>
              <div className={`px-3 py-1 rounded-full text-xs font-medium ${status?.configured ? 'bg-emerald-500/10 text-emerald-400' : 'bg-amber-500/10 text-amber-400'}`}>
                {status?.configured ? 'Connected' : 'Pending Review'}
              </div>
            </div>
            <div className="bg-white/5 rounded-xl p-4 space-y-2">
              <p className="text-xs text-slate-500"><span className="text-slate-400">Phone ID:</span> <code className="text-lumina-300 font-mono">{status?.has_phone_id ? '1257983506231819' : 'Not set'}</code></p>
              <p className="text-xs text-slate-500"><span className="text-slate-400">Token:</span> {status?.has_api_key ? '✅ Configured' : '⏳ Waiting for Meta approval'}</p>
            </div>
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
              <p className="text-xs text-amber-400 font-medium mb-1">📱 WhatsApp Web Pairing</p>
              <p className="text-xs text-slate-500 mb-3">Connect your phone via QR code for WhatsApp Web access (required for calls).</p>
              <ol className="space-y-1.5 text-xs text-slate-400 list-decimal list-inside">
                <li>Open WhatsApp on your phone</li>
                <li>Menu (⋮) → Linked Devices → Link a Device</li>
                <li>Scan the QR code that appears</li>
              </ol>
            </div>
          </div>
          <div className="bento-card space-y-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2"><Smartphone className="w-4 h-4" /> Device Info</h3>
            <div className="bg-white/5 rounded-xl p-4 text-xs text-slate-500 space-y-2">
              <p>WhatsApp Business API status is shown above. The catalog and messaging features work once the API token is configured.</p>
              <p>For calls, you need an active WhatsApp Web session.</p>
            </div>
            <div className="flex gap-2">
              <button onClick={() => navigator.clipboard.writeText('1257983506231819')} className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl py-2.5 text-xs font-medium flex items-center justify-center gap-1.5"><Copy className="w-3 h-3" /> Copy Phone ID</button>
              <button onClick={() => fetch('/api/whatsapp/status').then(r => r.json()).then(d => setStatus(d))} className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl py-2.5 text-xs font-medium flex items-center justify-center gap-1.5"><Loader2 className="w-3 h-3" /> Refresh Status</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: string; color: string }) {
  const colors: Record<string, string> = { lumina: 'from-lumina-500 to-lumina-700', emerald: 'from-emerald-500 to-emerald-700', violet: 'from-violet-500 to-violet-700', blue: 'from-blue-500 to-blue-700', amber: 'from-amber-500 to-amber-700' };
  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${colors[color]} p-[1px] transition-all hover:scale-[1.02]`}>
      <div className="rounded-2xl bg-slate-950/90 backdrop-blur-sm p-4">
        <div className="flex items-start justify-between">
          <div><p className="text-[10px] font-medium text-white/60 uppercase tracking-wider">{label}</p><p className="text-sm font-bold text-white mt-1">{value}</p></div>
          <Icon className="w-6 h-6 text-white/30" />
        </div>
      </div>
    </div>
  );
}
