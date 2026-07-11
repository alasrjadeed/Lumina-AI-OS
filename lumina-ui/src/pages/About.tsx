import { Globe, MapPin, Phone, ExternalLink, Sparkles } from 'lucide-react';

export default function About() {
  return (
    <div className="max-w-3xl mx-auto py-8 px-6 space-y-8">
      <div className="text-center">
        <img src="/lumina.png" alt="Lumina" className="w-16 h-16 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-white tracking-tight">Lumina AI OS</h1>
        <p className="text-lumina-400 font-medium mt-1">v1.0.0</p>
        <p className="text-sm text-slate-400 mt-3 max-w-lg mx-auto leading-relaxed">
          The world's first Autonomous AI Employee Operating System — combining
          AI-powered chat, desktop automation, browser control, CRM, marketing,
          and multi-agent orchestration into one unified platform.
        </p>
      </div>

      <div className="bento-card">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-lumina-400" /> About the Developer
        </h2>
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-lumina-600/20 border border-lumina-500/20 flex items-center justify-center shrink-0">
              <span className="text-lg font-bold text-lumina-400">AJ</span>
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">AL ASAR JADEED</h3>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                A Bahrain-based digital agency specializing in GEO (Generative Engine Optimization),
                AEO (Answer Engine Optimization), SEO, website design, and social media marketing.
                With 10+ years of experience and 500+ successful projects, they serve clients across
                Bahrain and the GCC region.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
              <Globe className="w-4 h-4 text-lumina-400 shrink-0" />
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Website</p>
                <a href="https://alasarjadeed.com" target="_blank" rel="noopener noreferrer"
                  className="text-xs text-lumina-400 hover:text-lumina-300 underline underline-offset-2">
                  alasarjadeed.com
                </a>
              </div>
            </div>
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
              <MapPin className="w-4 h-4 text-lumina-400 shrink-0" />
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Location</p>
                <p className="text-xs text-slate-300">Bahrain</p>
              </div>
            </div>
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
              <Phone className="w-4 h-4 text-lumina-400 shrink-0" />
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Phone</p>
                <p className="text-xs text-slate-300">+973 3634 4490</p>
              </div>
            </div>
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
              <ExternalLink className="w-4 h-4 text-lumina-400 shrink-0" />
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wider">Services</p>
                <p className="text-xs text-slate-300">GEO · AEO · SEO · Web Design · Social Media</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bento-card">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Key Features</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm">
          {[
            'AI Chat & Code Generation',
            'Desktop Automation',
            'Browser Agent',
            'Android Device Control',
            'CRM & Pipeline Management',
            'SEO & Marketing Tools',
            'Multi-Agent Orchestration',
            'Voice Assistant (Jarvis)',
            'Computer Vision',
            'Task Queue & Scheduling',
            'Visual Flow Builder',
            'Project Management',
          ].map(f => (
            <div key={f} className="flex items-center gap-2 px-3 py-2 rounded-lg text-slate-400">
              <div className="w-1.5 h-1.5 rounded-full bg-lumina-500 shrink-0" />
              {f}
            </div>
          ))}
        </div>
      </div>

      <p className="text-center text-[10px] text-slate-600">
        &copy; {new Date().getFullYear()} AL ASAR JADEED. All rights reserved.
      </p>
    </div>
  );
}
