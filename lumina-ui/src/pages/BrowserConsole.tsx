import { useState } from 'react';
import { Globe, ArrowRight, MousePointer, Type, Code, Image, X } from 'lucide-react';

export default function BrowserConsole() {
  const [url, setUrl] = useState('');
  const [content, setContent] = useState('');
  const [links, setLinks] = useState<Array<{ text: string; href: string }>>([]);
  const [selector, setSelector] = useState('');
  const [fillValue, setFillValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState<string[]>([]);

  const addLog = (msg: string) => setLog(l => [...l, `[${new Date().toLocaleTimeString()}] ${msg}`]);

  const navigate = async () => {
    if (!url.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/browser/navigate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) });
      const data = await res.json();
      addLog(`Navigated to ${url}`);
      const contentRes = await fetch('/api/browser/content');
      const contentData = await contentRes.json();
      setContent(contentData.html?.slice(0, 5000) || '(empty)');
      const linksRes = await fetch('/api/browser/links');
      const linksData = await linksRes.json();
      setLinks(Array.isArray(linksData) ? linksData : linksData.links || []);
    } catch { addLog('Error navigating'); }
    setLoading(false);
  };

  const clickElement = async () => {
    if (!selector.trim()) return;
    try {
      await fetch('/api/browser/click', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ selector }) });
      addLog(`Clicked ${selector}`);
    } catch { addLog('Click failed'); }
  };

  const fillElement = async () => {
    if (!selector.trim()) return;
    try {
      await fetch('/api/browser/fill', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ selector, value: fillValue }) });
      addLog(`Filled ${selector} with "${fillValue}"`);
    } catch { addLog('Fill failed'); }
  };

  const takeScreenshot = async () => {
    try {
      const res = await fetch('/api/browser/screenshot', { method: 'POST' });
      const data = await res.json();
      addLog(`Screenshot: ${data.path || 'taken'}`);
    } catch { addLog('Screenshot failed'); }
  };

  return (
    <div className="p-6 space-y-6 h-full flex flex-col">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2 shrink-0"><Globe className="w-6 h-6 text-lumina-400" /> Browser Console</h1>

      <div className="flex gap-2 shrink-0">
        <input className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500" placeholder="https://example.com" value={url} onChange={e => setUrl(e.target.value)} onKeyDown={e => e.key === 'Enter' && navigate()} />
        <button onClick={navigate} disabled={loading} className="bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 text-white rounded-lg px-4 py-2"><ArrowRight className="w-4 h-4" /></button>
      </div>

      <div className="flex gap-2 shrink-0 flex-wrap">
        <input className="flex-1 min-w-32 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500" placeholder="CSS selector" value={selector} onChange={e => setSelector(e.target.value)} />
        <button onClick={clickElement} className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm flex items-center gap-1"><MousePointer className="w-3.5 h-3.5" /> Click</button>
        <input className="w-40 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-lumina-500" placeholder="Fill value" value={fillValue} onChange={e => setFillValue(e.target.value)} />
        <button onClick={fillElement} className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm flex items-center gap-1"><Type className="w-3.5 h-3.5" /> Fill</button>
        <button onClick={takeScreenshot} className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg px-3 py-2 text-sm flex items-center gap-1"><Image className="w-3.5 h-3.5" /> Screenshot</button>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-4 min-h-0">
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 flex flex-col min-h-0">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 shrink-0">Page Content</h2>
          <pre className="flex-1 overflow-auto text-xs text-slate-300 font-mono whitespace-pre-wrap break-all">{content || 'No page loaded'}</pre>
        </div>
        <div className="flex flex-col gap-4 min-h-0">
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 flex-1 overflow-auto">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Links ({links.length})</h2>
            {links.map((l, i) => <div key={i} className="py-1 border-b border-slate-800 last:border-0"><p className="text-xs text-slate-300 truncate">{l.text || '(no text)'}</p><p className="text-xs text-lumina-400 truncate">{l.href}</p></div>)}
          </div>
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 h-40 overflow-auto">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Action Log</h2>
            {log.map((l, i) => <p key={i} className="text-xs text-slate-400 font-mono">{l}</p>)}
            {log.length === 0 && <p className="text-xs text-slate-600">No actions yet</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
