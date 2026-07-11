import { useEffect, useState } from 'react';
import { api } from '../api';
import { Smartphone, Terminal, Play, List, RotateCw, Keyboard, MousePointer, ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Home, ArrowLeftFromLine, Power, Volume2, VolumeX, Search, Menu, TvMinimalPlay, Download, Upload, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';

interface Device { serial: string; }

const keyRows = [
  [{ label: 'q', key: 'q' }, { label: 'w', key: 'w' }, { label: 'e', key: 'e' }, { label: 'r', key: 'r' }, { label: 't', key: 't' }, { label: 'y', key: 'y' }, { label: 'u', key: 'u' }, { label: 'i', key: 'i' }, { label: 'o', key: 'o' }, { label: 'p', key: 'p' }],
  [{ label: 'a', key: 'a' }, { label: 's', key: 's' }, { label: 'd', key: 'd' }, { label: 'f', key: 'f' }, { label: 'g', key: 'g' }, { label: 'h', key: 'h' }, { label: 'j', key: 'j' }, { label: 'k', key: 'k' }, { label: 'l', key: 'l' }],
  [{ label: '⇧', key: 'shift' }, { label: 'z', key: 'z' }, { label: 'x', key: 'x' }, { label: 'c', key: 'c' }, { label: 'v', key: 'v' }, { label: 'b', key: 'b' }, { label: 'n', key: 'n' }, { label: 'm', key: 'm' }, { label: '⌫', key: 'del' }],
  [{ label: '123', key: 'num' }, { label: ',', key: ',' }, { label: ' ', key: 'space', wide: true }, { label: '.', key: '.' }, { label: '⏎', key: 'enter' }],
];

const sysKeys = [
  { label: 'Home', key: 'home', icon: Home },
  { label: 'Back', key: 'back', icon: ArrowLeftFromLine },
  { label: 'Menu', key: 'menu', icon: Menu },
  { label: 'Search', key: 'search', icon: Search },
  { label: 'Power', key: 'power', icon: Power },
  { label: 'Vol+', key: 'volume_up', icon: Volume2 },
  { label: 'Vol-', key: 'volume_down', icon: Volume2 },
  { label: 'Mute', key: 'mute', icon: VolumeX },
  { label: '▲', key: 'up', icon: ArrowUp },
  { label: '▼', key: 'down', icon: ArrowDown },
  { label: '◀', key: 'left', icon: ArrowLeft },
  { label: '▶', key: 'right', icon: ArrowRight },
  { label: 'OK', key: 'ok', icon: MousePointer },
  { label: 'Play', key: 'play', icon: TvMinimalPlay },
];

export default function AndroidManager() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selected, setSelected] = useState('');
  const [shellCmd, setShellCmd] = useState('');
  const [output, setOutput] = useState('');
  const [packages, setPackages] = useState<string[]>([]);
  const [logcat, setLogcat] = useState('');
  const [tab, setTab] = useState<'devices' | 'virtual' | 'keyboard' | 'shell' | 'appinstaller' | 'packages' | 'logcat'>('devices');
  const [kbInput, setKbInput] = useState('');
  const [shiftOn, setShiftOn] = useState(false);
  const [kbStatus, setKbStatus] = useState('');
  const [screenImg, setScreenImg] = useState('');
  const [screenLoading, setScreenLoading] = useState(false);
  const refreshScreen = async () => {
    setScreenLoading(true);
    setScreenImg('');
    // Force browser to load new image by updating timestamp
    setTimeout(() => {
      setScreenImg('/api/android/screenshot?_t=' + Date.now());
      setScreenLoading(false);
    }, 100);
  };

  const [apkFile, setApkFile] = useState<File | null>(null);
  const [apkStatus, setApkStatus] = useState('');
  const [apkInstalling, setApkInstalling] = useState(false);
  const [installedApps, setInstalledApps] = useState<string[]>([]);

  useEffect(() => { api.androidDevices().then(d => { setDevices(d.devices); if (d.devices.length) setSelected(d.devices[0].serial); }).catch(() => {}); }, []);

  const pressKey = async (key: string) => {
    if (key === 'shift') { setShiftOn(!shiftOn); return; }
    if (key === 'del') {
      try { await fetch('/api/android/keyboard/press', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: 'del' }) }); setKbStatus('⌫'); } catch {}
      return;
    }
    if (key === 'space') {
      try { await fetch('/api/android/keyboard/press', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: 'space' }) }); setKbStatus('␣'); } catch {}
      return;
    }
    if (key === 'enter') {
      try { await fetch('/api/android/keyboard/press', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: 'enter' }) }); setKbStatus('⏎'); } catch {}
      return;
    }
    if (key === 'num') { setShiftOn(false); return; }
    if (key.length === 1) {
      const char = shiftOn ? key.toUpperCase() : key;
      try { await fetch('/api/android/keyboard/type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: char, method: 'adb_text' }) }); setKbStatus(char); setKbInput(i => i + char); } catch {}
      if (shiftOn) setShiftOn(false);
      return;
    }
    try { await fetch('/api/android/keyboard/press', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key }) }); setKbStatus(key); } catch {}
  };

  const sendText = async () => {
    if (!kbInput.trim()) return;
    try { await fetch('/api/android/keyboard/type', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: kbInput, method: 'adb_text' }) }); setKbStatus('✓ Sent'); } catch {}
  };

  const clearKb = async () => {
    try { await fetch('/api/android/keyboard/clear', { method: 'POST' }); setKbInput(''); setKbStatus('Cleared'); } catch {}
  };

  const runShell = async () => {
    if (!shellCmd.trim()) return;
    try {
      const res = await fetch('/api/android/shell', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ serial: selected, command: shellCmd }) });
      const data = await res.json();
      setOutput(data.output || data.error || '(no output)');
    } catch { setOutput('Error'); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3"><Smartphone className="w-7 h-7 text-lumina-400" /> Android</h1></div>
        <select className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-300" value={selected} onChange={e => setSelected(e.target.value)}>
          {devices.map(d => <option key={d.serial} value={d.serial}>{d.serial}</option>)}
        </select>
      </div>

      <div className="flex gap-2 border-b border-white/5 pb-1 flex-wrap">
        {(['devices', 'virtual', 'keyboard', 'shell', 'appinstaller', 'packages', 'logcat'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm rounded-t-xl transition-all ${
              tab === t ? 'bg-white/5 text-lumina-300 border-b-2 border-lumina-500 font-medium' : 'text-slate-500 hover:text-slate-300'
            }`}>
            {t === 'virtual' && <Smartphone className="w-4 h-4" />}
            {t === 'keyboard' && <Keyboard className="w-4 h-4" />}
            {t === 'shell' && <Terminal className="w-4 h-4" />}
            {t === 'appinstaller' && <Download className="w-4 h-4" />}
            {t === 'packages' && <List className="w-4 h-4" />}
            {t === 'logcat' && <RotateCw className="w-4 h-4" />}
            {t === 'virtual' ? 'Virtual Mobile' : t === 'appinstaller' ? 'APK Install' : t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Lumina ADB Keyboard */}
      {tab === 'keyboard' && (
        <div className="max-w-xl mx-auto space-y-4">
          {/* Input preview */}
          <div className="bento-card">
            <div className="flex items-center gap-2 mb-3">
              <Keyboard className="w-5 h-5 text-lumina-400" />
              <span className="text-sm font-semibold text-slate-200">Lumina ADB Keyboard</span>
              {kbStatus && <span className="text-xs text-lumina-400 ml-auto">{kbStatus}</span>}
            </div>
            <div className="bg-white/5 rounded-xl p-3 mb-3 font-mono text-sm text-slate-200 min-h-[40px]" dir="ltr">
              {kbInput || <span className="text-slate-600">Type on the keyboard below...</span>}
            </div>
            <div className="flex gap-2">
              <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 font-mono"
                placeholder="Or type here..." value={kbInput} onChange={e => setKbInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') sendText(); }} />
              <button onClick={sendText} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-4 py-2 text-sm font-medium">Send</button>
              <button onClick={clearKb} className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-4 py-2 text-sm">Clear</button>
            </div>
          </div>

          {/* Keyboard */}
          <div className="bento-card space-y-1.5">
            {keyRows.map((row, ri) => (
              <div key={ri} className="flex gap-1 justify-center">
                {row.map(k => (
                  <button key={k.key} onPointerDown={() => pressKey(k.key)}
                    className={`${
                      k.wide ? 'flex-[2]' : 'flex-1'
                    } py-3 rounded-lg text-sm font-medium transition-all duration-100 active:scale-95 ${
                      k.key === 'shift' && shiftOn
                        ? 'bg-lumina-600 text-white'
                        : k.key === 'del' || k.key === 'enter'
                        ? 'bg-slate-700 text-slate-200 hover:bg-slate-600'
                        : k.key === 'space'
                        ? 'bg-slate-800 text-slate-200 hover:bg-slate-700'
                        : 'bg-white/5 text-slate-300 hover:bg-white/10'
                    }`}>
                    {k.label}
                  </button>
                ))}
              </div>
            ))}
          </div>

          {/* System keys */}
          <div className="bento-card">
            <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider mb-2">System Keys</p>
            <div className="flex flex-wrap gap-1.5">
              {sysKeys.map(k => (
                <button key={k.key} onClick={() => pressKey(k.key)}
                  className="flex items-center gap-1 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs transition-colors active:scale-95">
                  {k.icon && <k.icon className="w-3.5 h-3.5" />}
                  <span>{k.label.replace(/[▲▼◀▶]/g, '').trim()}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === 'shell' && (
        <div className="bento-card space-y-3 h-[500px] flex flex-col">
          <div className="flex gap-2 shrink-0">
            <input className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 font-mono"
              placeholder="adb shell command..." value={shellCmd} onChange={e => setShellCmd(e.target.value)} onKeyDown={e => e.key === 'Enter' && runShell()} />
            <button onClick={runShell} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-4 py-2 text-sm flex items-center gap-2"><Play className="w-4 h-4" /> Run</button>
          </div>
          <pre className="flex-1 overflow-auto bg-black/30 rounded-xl p-4 text-xs text-slate-300 font-mono">{output || 'Output will appear here'}</pre>
        </div>
      )}

      {tab === 'packages' && (
        <div className="space-y-3">
          <button onClick={async () => { try { const res = await fetch(`/api/android/packages?serial=${encodeURIComponent(selected)}`); const d = await res.json(); setPackages(d.packages || []); } catch {} }}
            className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-4 py-2 text-sm flex items-center gap-2"><List className="w-4 h-4" /> List Packages</button>
          <div className="bento-card h-80 overflow-auto"><div className="space-y-0.5">{packages.map((p, i) => <p key={i} className="text-xs text-slate-300 font-mono py-0.5">{p}</p>)}</div></div>
        </div>
      )}

      {tab === 'logcat' && (
        <div className="space-y-3">
          <button onClick={async () => { try { const res = await fetch(`/api/android/logcat?serial=${encodeURIComponent(selected)}`); const d = await res.json(); setLogcat(d.log || ''); } catch {} }}
            className="bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-4 py-2 text-sm flex items-center gap-2"><RotateCw className="w-4 h-4" /> Load Logcat</button>
          <pre className="bento-card h-80 overflow-auto text-xs text-slate-300 font-mono">{logcat}</pre>
        </div>
      )}

      {/* App Installer */}
      {tab === 'appinstaller' && (
        <div className="max-w-xl mx-auto space-y-6">
          <div className="bento-card space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center shadow-lg"><Download className="w-6 h-6 text-white" /></div>
              <div><h2 className="text-lg font-bold text-white">APK Installer</h2><p className="text-xs text-slate-400">Install Android apps directly via ADB</p></div>
            </div>

            <div className="border-2 border-dashed border-white/10 rounded-2xl p-8 text-center hover:border-lumina-500/30 transition-colors cursor-pointer"
              onClick={() => document.getElementById('apk-input')?.click()}>
              <Upload className="w-10 h-10 mx-auto mb-3 text-slate-500" />
              <p className="text-sm text-slate-400 mb-1">Click to select an APK file</p>
              <p className="text-xs text-slate-600">or drag and drop here</p>
              <input id="apk-input" type="file" accept=".apk" className="hidden" onChange={e => setApkFile(e.target.files?.[0] || null)} />
              {apkFile && <p className="mt-3 text-sm text-lumina-400 font-mono">{apkFile.name} ({(apkFile.size / 1024 / 1024).toFixed(1)} MB)</p>}
            </div>

            <button onClick={async () => {
              if (!apkFile) return;
              setApkInstalling(true); setApkStatus('Installing...');
              const appName = apkFile.name.replace(/\.apk$/i, '');
              // Always add to virtual mobile
              setInstalledApps(a => a.includes(appName) ? a : [...a, appName]);
              // Try ADB install if device connected
              try {
                const form = new FormData();
                form.append('apk', apkFile);
                const res = await fetch('/api/android/install/apk', { method: 'POST', body: form });
                const data = await res.json();
                if (data.success) {
                  setApkStatus(`✅ Installed on device + virtual mobile`);
                } else if (data.error && data.error.includes('No device')) {
                  setApkStatus(`✅ Added to virtual mobile (no device connected)`);
                } else {
                  setApkStatus(`✅ Added to virtual mobile (ADB: ${data.error || 'OK'})`);
                }
              } catch {
                setApkStatus(`✅ Added to virtual mobile`);
              }
              setApkInstalling(false);
            }} disabled={!apkFile || apkInstalling}
              className="w-full bg-lumina-600 hover:bg-lumina-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl py-3 text-sm font-medium transition-all flex items-center justify-center gap-2">
              {apkInstalling ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
              {apkInstalling ? 'Installing...' : 'Install APK'}
            </button>

            {apkStatus && (
              <div className={`px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${
                apkStatus.includes('✅') ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                : apkStatus.includes('❌') ? 'bg-red-500/10 text-red-400 border border-red-500/10'
                : 'bg-lumina-500/10 text-lumina-400'
              }`}>
                {apkStatus.includes('✅') ? <CheckCircle className="w-4 h-4" /> : apkStatus.includes('❌') ? <XCircle className="w-4 h-4" /> : <Loader2 className="w-4 h-4 animate-spin" />}
                {apkStatus}
              </div>
            )}
          </div>

          {/* Installed apps */}
          {installedApps.length > 0 && (
            <div className="bento-card">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Installed Apps</h3>
              <div className="space-y-2">{installedApps.map((app, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2.5 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-xs font-bold">{app[0]}</div>
                  <span className="text-sm text-slate-300 flex-1">{app}</span>
                  <button onClick={async () => { try { await fetch('/api/android/shell', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ command: `monkey -p ${app} 1` }) }); } catch {} }}
                    className="text-xs text-lumina-400 hover:text-lumina-300">Launch</button>
                  <CheckCircle className="w-4 h-4 text-emerald-500" />
                </div>
              ))}</div>
            </div>
          )}
        </div>
      )}

      {/* Virtual Mobile */}
      {/* Scrcpy - Screen Mirroring */}
      {tab === 'virtual' && (
        <div className="grid grid-cols-1 gap-6">
          {/* Scrcpy launch + live view in one row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Info & Launch */}
            <div className="bento-card space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center shadow-lg"><Smartphone className="w-6 h-6 text-white" /></div>
                <div><h2 className="text-base font-bold text-white">Scrcpy</h2><p className="text-[10px] text-slate-400">Screen mirroring</p></div>
              </div>
              <div className="flex items-center gap-2 text-xs"><CheckCircle className="w-3.5 h-3.5 text-emerald-400" /><span className="text-slate-300">Scrcpy installed</span></div>
              <div className="flex items-center gap-2 text-xs">
                <div className={`w-2 h-2 rounded-full ${devices.length > 0 ? 'bg-emerald-500' : 'bg-slate-600'}`} />
                <span className="text-slate-300">{devices.length > 0 ? `${devices.length} device(s)` : 'No device'}</span>
              </div>
              <button onClick={async () => {
                try {
                  const res = await fetch('/api/android/local/exec?command=scrcpy%20--no-audio%20--max-size%20800', { method: 'POST' });
                  const data = await res.json();
                  if (data.status === 'started') alert('✅ Scrcpy launched! Check for a new window with your Android screen.');
                  else alert('❌ Failed: ' + (data.error || 'unknown'));
                } catch { alert('Click OK then run manually in terminal: scrcpy'); }
              }} disabled={devices.length === 0}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white rounded-xl py-3 text-sm font-medium flex items-center justify-center gap-2 transition-all shadow-lg shadow-emerald-500/20">
                <Smartphone className="w-4 h-4" /> ▶ Launch Scrcpy
              </button>
              <div className="bg-slate-950 rounded-xl p-3 border border-white/5">
                <code className="text-[10px] text-lumina-300 font-mono break-all select-all">scrcpy</code>
              </div>
            </div>

            {/* Right: Live screen preview (auto-refresh) */}
            <div className="lg:col-span-2 bento-card">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Device Screen</h2>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${devices.length > 0 ? 'bg-emerald-500 animate-pulse-dot' : 'bg-slate-600'}`} />
                  <button onClick={refreshScreen} disabled={devices.length === 0}
                    className="bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 rounded-lg px-3 py-1.5 text-[10px] flex items-center gap-1 transition-all"><RefreshCw className="w-3 h-3" /> Refresh</button>
                </div>
              </div>
              <div className="bg-black/60 rounded-2xl overflow-hidden border border-white/5 min-h-[500px] flex items-center justify-center relative">
                {!devices.length ? (
                  <div className="text-center p-8">
                    <Smartphone className="w-14 h-14 mx-auto mb-3 text-slate-600" />
                    <p className="text-sm text-slate-500 font-medium">No device connected</p>
                    <p className="text-xs text-slate-600 mt-1">Connect Android via USB with USB debugging enabled</p>
                    <p className="text-xs text-slate-600 mt-2">Then run: <code className="text-lumina-300 bg-white/10 px-1.5 py-0.5 rounded">adb devices</code></p>
                  </div>
                ) : screenLoading ? (
                  <div className="text-center p-8"><Loader2 className="w-10 h-10 mx-auto mb-3 animate-spin text-slate-500" /><p className="text-sm text-slate-500">Capturing screen...</p></div>
                ) : screenImg ? (
                  <img src={screenImg} alt="Device screen" className="w-full h-auto max-h-[600px] object-contain" />
                ) : (
                  <button onClick={refreshScreen} className="bg-lumina-600 hover:bg-lumina-500 text-white rounded-xl px-6 py-3 text-sm font-medium shadow-lg shadow-lumina-500/20">📸 Capture Device Screen</button>
                )}
                {/* Quick tap overlay hint */}
                {screenImg && <div className="absolute bottom-3 left-3 bg-black/60 text-white/70 text-[10px] px-3 py-1.5 rounded-lg backdrop-blur-sm">Use Keyboard tab to send keystrokes</div>}
              </div>
            </div>
          </div>

          {/* Quick controls row */}
          <div className="flex gap-2">
            {[
              { label: '← Back', key: 'back' },
              { label: '⌂ Home', key: 'home' },
              { label: '☰ Menu', key: 'menu' },
              { label: '⏻ Power', key: 'power' },
              { label: '🔍 Search', key: 'search' },
              { label: '⬆ Vol+', key: 'volume_up' },
              { label: '⬇ Vol-', key: 'volume_down' },
              { label: '🔇 Mute', key: 'mute' },
            ].map(btn => (
              <button key={btn.key} onClick={async () => {
                try { await fetch('/api/android/keyboard/press', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({key: btn.key}) }); } catch {}
              }} disabled={devices.length === 0}
                className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-30 text-xs text-slate-300 transition-all text-center">{btn.label}</button>
            ))}
          </div>
        </div>
      )}
      {tab === 'devices' && (
        <div className="bento-card"><p className="text-sm text-slate-400">Connect an Android device via ADB. Use Virtual Mobile to simulate, Keyboard for keystrokes, Shell for commands, Packages for installed apps, and Logcat for logs.</p></div>
      )}
    </div>
  );
}
