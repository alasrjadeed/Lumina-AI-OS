import { useEffect, useState } from 'react';
import { api } from '../api';
import type { AppConfig } from '../types';
import { Settings as SettingsIcon, CheckCircle, XCircle } from 'lucide-react';

export default function Settings() {
  const [config, setConfig] = useState<AppConfig | null>(null);

  useEffect(() => {
    api.config().then(setConfig).catch(() => {});
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-white flex items-center gap-2">
        <SettingsIcon className="w-6 h-6 text-lumina-400" /> Settings
      </h1>

      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">System Info</h2>
        <div className="space-y-3 text-sm">
          <Row label="Application" value={config?.app_name || '...'} />
          <Row label="Version" value={config?.version || '...'} />
          <Row label="Groq Enabled" value={config?.providers?.groq ? 'Yes' : 'No'} />
        </div>
      </div>

      <div className="bg-slate-900 rounded-xl border border-slate-800 p-5">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">AI Providers</h2>
        <div className="space-y-3">
          {config && Object.entries(config.providers).map(([name, enabled]) => (
            <div key={name} className="flex items-center justify-between py-2">
              <span className="text-sm text-slate-300 capitalize">{name.replace(/_/g, ' ')}</span>
              {enabled ? (
                <span className="flex items-center gap-1.5 text-emerald-400 text-sm">
                  <CheckCircle className="w-3.5 h-3.5" /> Active
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-slate-500 text-sm">
                  <XCircle className="w-3.5 h-3.5" /> Not configured
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-5">
        <p className="text-xs text-slate-500 leading-relaxed">
          To configure additional providers, edit the <code className="text-lumina-400 bg-slate-800 px-1 rounded">.env</code> file in the workspace directory with your API keys.
        </p>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-slate-400">{label}</span>
      <span className="text-slate-200 font-medium">{value}</span>
    </div>
  );
}
