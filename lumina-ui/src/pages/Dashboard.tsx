import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Bot, Activity, Zap, Shield, Globe, Server, Users, CheckCircle,
  Cpu, HardDrive, Clock, BarChart3, MessageSquare, Code2, Bug,
  Layers, Radio, Database, UserCheck, Briefcase, TrendingUp,
  RefreshCw, Loader2, ArrowRight, ChevronRight, PoundSterling,
  Wifi, Smartphone, Eye, Heart, Terminal, BookOpen, AlertTriangle,
  PieChart, Gauge, Sparkles, FileCode, Workflow,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';

const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function SkeletonLine({ className = '' }: { className?: string }) {
  return <div className={`bg-white/5 rounded animate-pulse ${className}`} />;
}

function compactNum(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

interface Section { id: string; label: string; icon: any; }
const SECTIONS: Section[] = [
  { id: 'overview', label: 'Overview', icon: Gauge },
  { id: 'system', label: 'System', icon: Server },
  { id: 'providers', label: 'Providers', icon: Radio },
  { id: 'agents', label: 'Agents', icon: Bot },
  { id: 'crm', label: 'CRM', icon: Briefcase },
  { id: 'marketing', label: 'Marketing', icon: TrendingUp },
  { id: 'tasks', label: 'Tasks', icon: Layers },
  { id: 'activity', label: 'Activity', icon: Clock },
];

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState('overview');
  const [loaded, setLoaded] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [health, setHealth] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [desktop, setDesktop] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [agentRuns, setAgentRuns] = useState<any[]>([]);
  const [crmSummary, setCrmSummary] = useState<any>(null);
  const [marketingSummary, setMarketingSummary] = useState<any>(null);
  const [taskStats, setTaskStats] = useState<any>(null);
  const [employeeStatus, setEmployeeStatus] = useState<any>(null);
  const [learningStats, setLearningStats] = useState<any>(null);
  const [processCount, setProcessCount] = useState(0);
  const [chatThreads, setChatThreads] = useState(0);
  const [codeReviews, setCodeReviews] = useState(0);
  const [whatsapp, setWhatsapp] = useState<any>(null);
  const [error, setError] = useState('');

  const loadAll = useCallback(async () => {
    setRefreshing(true);
    setError('');
    try {
      const results = await Promise.allSettled([
        get('/system/health'),
        get('/system/config'),
        get('/desktop/info'),
        get('/desktop/stats'),
        get('/agents'),
        get('/agents/runs?limit=5'),
        get('/crm/summary'),
        get('/marketing/summary'),
        get('/tasks/stats'),
        get('/employee/status'),
        get('/learning/stats'),
        get('/desktop/processes?limit=0'),
        get('/chat/conversations'),
        get('/code/review/history?limit=0'),
        get('/whatsapp/status'),
      ]);
      if (results[0].status === 'fulfilled') setHealth(results[0].value);
      if (results[1].status === 'fulfilled') setConfig(results[1].value);
      if (results[2].status === 'fulfilled') setDesktop(results[2].value);
      if (results[3].status === 'fulfilled') setStats(results[3].value);
      if (results[4].status === 'fulfilled') {
        const data = results[4].value as { agents: string[] };
        setAgents(Array.isArray(data.agents) ? data.agents : []);
      }
      if (results[5].status === 'fulfilled') setAgentRuns((results[5].value as any).runs || []);
      if (results[6].status === 'fulfilled') setCrmSummary(results[6].value);
      if (results[7].status === 'fulfilled') setMarketingSummary(results[7].value);
      if (results[8].status === 'fulfilled') setTaskStats(results[8].value);
      if (results[9].status === 'fulfilled') setEmployeeStatus(results[9].value);
      if (results[10].status === 'fulfilled') setLearningStats(results[10].value);
      if (results[11].status === 'fulfilled') {
        const v = results[11].value as any;
        setProcessCount(v.count || v.processes?.length || 0);
      }
      if (results[12].status === 'fulfilled') setChatThreads((results[12].value as any).total || 0);
      if (results[13].status === 'fulfilled') setCodeReviews((results[13].value as any).total || 0);
      if (results[14].status === 'fulfilled') setWhatsapp(results[14].value);
    } catch (e: any) {
      setError(e.message);
    }
    setRefreshing(false);
    setLoaded(true);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const providerEntries = config ? Object.entries(config.providers || {}) : [];
  const connectedCount = providerEntries.filter(([_, v]) => v).length;
  const totalCount = providerEntries.length;
  const diskPercent = stats?.disk_percent ?? 0;

  if (!loaded) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-4">
          <SkeletonLine className="w-10 h-10 rounded-xl" />
          <div className="space-y-2">
            <SkeletonLine className="w-48 h-6" />
            <SkeletonLine className="w-64 h-3" />
          </div>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1,2,3,4,5,6,7,8].map(i => <SkeletonLine key={i} className="h-24 rounded-2xl" />)}
        </div>
      </div>
    );
  }

  const StatCard = ({ icon: Icon, label, value, sub, color, href }: {
    icon: any; label: string; value: string; sub?: string; color?: string; href?: string;
  }) => {
    const c = color || 'from-lumina-500 to-lumina-700';
      const inner = (
        <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${c} p-[1px] transition-all duration-300 hover:scale-[1.02] group cursor-pointer`}>
        <div className="rounded-2xl bg-slate-950/90 backdrop-blur-sm p-4 h-full">
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <p className="text-[10px] font-medium text-white/50 uppercase tracking-wider">{label}</p>
              <p className="text-xl font-bold text-white mt-1 tracking-tight truncate">{value}</p>
              {sub && <p className="text-[10px] text-white/40 mt-0.5">{sub}</p>}
            </div>
            <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center backdrop-blur-sm shrink-0 ml-2 group-hover:scale-110 transition-transform">
              <Icon className="w-4.5 h-4.5 text-white/80" />
            </div>
          </div>
        </div>
      </div>
    );
    return href ? <Link to={href}>{inner}</Link> : inner;
  };

  const cardClasses = 'text-slate-400 hover:text-slate-200';
  const navBtn = (s: Section) => (
    <button key={s.id} onClick={() => setActiveSection(s.id)}
      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[10px] font-medium transition-all whitespace-nowrap ${
        activeSection === s.id
          ? 'bg-lumina-600/15 text-lumina-300 border border-lumina-500/20'
          : 'text-slate-500 hover:text-slate-300'
      }`}>
      <s.icon className="w-3 h-3" /> {s.label}
    </button>
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-lumina-400 to-lumina-600 flex items-center justify-center shadow-lg shadow-lumina-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Dashboard</h1>
            <p className="text-xs text-slate-400">
              {health?.status === 'ok'
                ? `All systems operational · ${health?.version || ''}`
                : 'Loading system data...'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-500 animate-ping opacity-30" />
            </div>
            <span className="text-[10px] font-medium text-emerald-400">Online</span>
          </div>
          <button onClick={loadAll} disabled={refreshing}
            className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 disabled:opacity-50 transition-all">
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Section nav */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {SECTIONS.map(s => navBtn(s))}
      </div>

      {/* ── OVERVIEW ── */}
      {activeSection === 'overview' && (
        <div className="space-y-6">
          {/* Stats row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard icon={Heart} label="Status" value={health?.status || '—'} sub={health?.version} color="from-emerald-500 to-emerald-700" />
            <StatCard icon={Bot} label="Agents" value={String(agents.length)} sub={agentRuns.length > 0 ? `${agentRuns.length} recent runs` : ''} color="from-lumina-500 to-lumina-700" />
            <StatCard icon={Radio} label="Providers" value={`${connectedCount}/${totalCount}`} sub="connected" color="from-violet-500 to-violet-700" />
            <StatCard icon={Server} label="Services" value={String(config ? Object.keys(config.providers || {}).length : 0)} sub={desktop?.hostname || ''} color="from-amber-500 to-amber-700" />
            <StatCard icon={Layers} label="Tasks" value={String(taskStats?.total || 0)} sub={`${taskStats?.running || 0} running`} color="from-blue-500 to-blue-700" href="/tasks" />
            <StatCard icon={Cpu} label="CPU Cores" value={String(desktop?.cpu_count || stats?.cpu_count || 0)} sub={desktop?.os || ''} color="from-cyan-500 to-cyan-700" />
            <StatCard icon={MessageSquare} label="Chats" value={String(chatThreads)} sub="conversations" color="from-pink-500 to-pink-700" href="/chat" />
            <StatCard icon={Code2} label="Code Reviews" value={String(codeReviews)} sub="total reviews" color="from-indigo-500 to-indigo-700" href="/code/review" />
          </div>

          {/* System + Disk + Agent Runs */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card hover={false} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <Server className="w-4 h-4 text-lumina-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">System</span>
              </div>
              <div className="space-y-2 text-xs">
                {[
                  ['OS', desktop?.os || health?.os || '—'],
                  ['Host', desktop?.hostname || '—'],
                  ['Version', health?.version || config?.version || '—'],
                  ['CPU', `${desktop?.cpu_count || stats?.cpu_count || '?'} cores`],
                ].map(([l, v]) => (
                  <div key={l} className="flex justify-between py-0.5">
                    <span className="text-slate-500">{l}</span>
                    <span className="text-slate-300 font-medium">{v}</span>
                  </div>
                ))}
              </div>
              {diskPercent > 0 && (
                <div className="pt-2">
                  <div className="flex justify-between text-[11px] mb-1">
                    <span className="text-slate-500">Disk</span>
                    <span className={diskPercent > 90 ? 'text-red-400' : 'text-slate-300'}>{diskPercent.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${
                      diskPercent > 90 ? 'bg-red-500' : diskPercent > 70 ? 'bg-amber-500' : 'bg-emerald-500'
                    }`} style={{ width: `${diskPercent}%` }} />
                  </div>
                  {stats?.disk_free && (
                    <p className="text-[9px] text-slate-600 mt-1">{compactNum(stats.disk_free)} free / {compactNum(stats.disk_total)} total</p>
                  )}
                </div>
              )}
            </Card>

            {/* Quick Links */}
            <Card hover={false} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <Zap className="w-4 h-4 text-lumina-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Quick Actions</span>
              </div>
              <div className="space-y-1">
                {[
                  { icon: MessageSquare, label: 'Chat', to: '/chat', desc: 'Ask your AI assistant' },
                  { icon: Code2, label: 'Code Generator', to: '/code/generate', desc: 'Generate code with AI' },
                  { icon: Bug, label: 'Code Review', to: '/code/review', desc: 'Analyze code quality' },
                  { icon: Bot, label: 'Agents', to: '/agents', desc: 'Run specialized AI agents' },
                  { icon: Briefcase, label: 'CRM', to: '/crm', desc: 'Manage deals & contacts' },
                ].map(item => (
                  <Link key={item.to} to={item.to}
                    className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.03] border border-transparent hover:border-white/5 transition-all group">
                    <div className="w-8 h-8 rounded-lg bg-white/[0.03] border border-white/5 flex items-center justify-center">
                      <item.icon className="w-4 h-4 text-lumina-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-300 group-hover:text-white transition-colors">{item.label}</p>
                      <p className="text-[9px] text-slate-500">{item.desc}</p>
                    </div>
                    <ChevronRight className="w-3 h-3 text-slate-600" />
                  </Link>
                ))}
              </div>
            </Card>

            {/* Learning & Employee */}
            <Card hover={false} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <BookOpen className="w-4 h-4 text-lumina-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Intelligence</span>
              </div>
              <div className="space-y-3">
                {employeeStatus && (
                  <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/5">
                    <Bot className="w-4 h-4 text-lumina-400" />
                    <div>
                      <p className="text-[10px] text-slate-500">Employee</p>
                      <p className="text-xs text-slate-300">{employeeStatus.missions_completed || 0} missions · {employeeStatus.tools_available || 0} tools</p>
                    </div>
                  </div>
                )}
                {learningStats && (
                  <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/5">
                    <Activity className="w-4 h-4 text-lumina-400" />
                    <div>
                      <p className="text-[10px] text-slate-500">Learning</p>
                      <p className="text-xs text-slate-300">{learningStats.total_actions || 0} actions · {learningStats.patterns_detected || 0} patterns</p>
                    </div>
                  </div>
                )}
                {crmSummary && (
                  <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/5">
                    <Briefcase className="w-4 h-4 text-lumina-400" />
                    <div>
                      <p className="text-[10px] text-slate-500">CRM Pipeline</p>
                      <p className="text-xs text-slate-300">${(crmSummary.pipeline_value || 0).toLocaleString()} · {crmSummary.total_deals || 0} deals</p>
                    </div>
                  </div>
                )}
                {whatsapp && (
                  <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/5">
                    <MessageSquare className="w-4 h-4 text-lumina-400" />
                    <div>
                      <p className="text-[10px] text-slate-500">WhatsApp</p>
                      <p className="text-xs text-slate-300">{whatsapp.configured ? 'Connected' : 'Not configured'}</p>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Agent Runs */}
          {agentRuns.length > 0 && (
            <Card hover={false} className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-white/5">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-lumina-400" />
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Recent Agent Runs</span>
                </div>
                <Link to="/agents" className="text-[10px] text-lumina-400 hover:text-lumina-300 flex items-center gap-1">
                  View all <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
              <div className="space-y-1">
                {agentRuns.slice(0, 5).map((run: any, i: number) => (
                  <div key={run.run_id || i} className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${
                      run.status === 'success' ? 'bg-emerald-500' :
                      run.status === 'error' ? 'bg-red-500' : 'bg-amber-500'
                    }`} />
                    <span className="text-xs text-slate-300 min-w-[100px] truncate">{run.agent_name || run.agent_id || 'Agent'}</span>
                    <span className="text-[10px] text-slate-500 flex-1 truncate">{run.task?.slice(0, 50)}</span>
                    {run.duration_ms && <span className="text-[9px] text-slate-600 shrink-0">{(run.duration_ms / 1000).toFixed(1)}s</span>}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ── SYSTEM ── */}
      {activeSection === 'system' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card hover={false} className="space-y-4 lg:col-span-2">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <Cpu className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">System Info</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {[
                ['OS', desktop?.os || '—'],
                ['Release', stats?.release || '—'],
                ['Arch', stats?.arch || '—'],
                ['Hostname', desktop?.hostname || '—'],
                ['CPU Cores', String(desktop?.cpu_count || stats?.cpu_count || '—')],
                ['Processes', String(processCount)],
              ].map(([l, v]) => (
                <div key={l} className="bg-white/[0.02] rounded-xl px-4 py-3 border border-white/5">
                  <p className="text-[9px] text-slate-500 uppercase tracking-wider">{l}</p>
                  <p className="text-sm text-slate-200 font-medium mt-1">{v}</p>
                </div>
              ))}
            </div>
          </Card>

          <div className="space-y-4">
            <Card hover={false} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <HardDrive className="w-4 h-4 text-lumina-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Disk Usage</span>
              </div>
              <div className="space-y-3">
                {['total', 'used', 'free'].map(key => (
                  <div key={key} className="flex justify-between text-xs">
                    <span className="text-slate-500 capitalize">{key}</span>
                    <span className="text-slate-300">{compactNum(stats?.[`disk_${key}`] || 0)}</span>
                  </div>
                ))}
                <div className="h-2.5 bg-white/5 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${
                    diskPercent > 90 ? 'bg-red-500' : diskPercent > 70 ? 'bg-amber-500' : 'bg-emerald-500'
                  }`} style={{ width: `${diskPercent}%` }} />
                </div>
              </div>
            </Card>

            <Card hover={false} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <Terminal className="w-4 h-4 text-lumina-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Application</span>
              </div>
              {[
                ['Name', config?.app_name || '—'],
                ['Version', config?.version || '—'],
                ['Provider', health?.primary_provider || '—'],
              ].map(([l, v]) => (
                <div key={l} className="flex justify-between text-xs py-1">
                  <span className="text-slate-500">{l}</span>
                  <span className="text-slate-300">{v}</span>
                </div>
              ))}
            </Card>
          </div>
        </div>
      )}

      {/* ── PROVIDERS ── */}
      {activeSection === 'providers' && (
        <Card hover={false} className="space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-white/5">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">AI Providers</span>
            </div>
            <span className="text-[10px] px-2 py-1 rounded-full bg-white/5 text-slate-400">{connectedCount}/{totalCount} connected</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {providerEntries.map(([name, enabled]) => (
              <div key={name}
                className="flex items-center justify-between px-4 py-3 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] border border-white/5 transition-all group">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-2.5 h-2.5 rounded-full transition-all ${
                    enabled ? 'bg-emerald-500 shadow-lg shadow-emerald-500/30' : 'bg-slate-600'
                  }`} />
                  <span className="text-sm text-slate-300 group-hover:text-white transition-colors truncate capitalize">
                    {name.replace(/_/g, ' ')}
                  </span>
                </div>
                {enabled ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <span className="text-[10px] text-slate-600">off</span>
                )}
              </div>
            ))}
            {providerEntries.length === 0 && (
              <p className="col-span-full text-center py-8 text-sm text-slate-500">No provider information available</p>
            )}
          </div>
        </Card>
      )}

      {/* ── AGENTS ── */}
      {activeSection === 'agents' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card hover={false} className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <Bot className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Available Agents ({agents.length})</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {agents.length > 0 ? agents.map((a: any) => (
                <span key={a.id || a}
                  className="px-2.5 py-1.5 bg-white/5 rounded-lg text-[11px] text-slate-300 border border-white/5 hover:bg-white/10 hover:border-lumina-500/30 transition-all cursor-default">
                  {a.name || (typeof a === 'string' ? a.replace(/_/g, ' ') : '')}
                </span>
              )) : (
                <p className="text-xs text-slate-500 py-4">Loading agents...</p>
              )}
            </div>
          </Card>

          <Card hover={false} className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <Activity className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Agent Runs ({agentRuns.length})</span>
            </div>
            <div className="space-y-1 max-h-64 overflow-y-auto">
              {agentRuns.length > 0 ? agentRuns.map((run: any, i: number) => (
                <div key={run.run_id || i} className="flex items-center gap-3 px-3 py-2 rounded-xl bg-white/[0.02] border border-white/5">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${
                    run.status === 'success' ? 'bg-emerald-500' :
                    run.status === 'error' ? 'bg-red-500' : 'bg-amber-500'
                  }`} />
                  <span className="text-[10px] text-slate-500 min-w-[80px] truncate">{run.agent_name || 'Agent'}</span>
                  <span className="text-[10px] text-slate-400 flex-1 truncate">{run.task?.slice(0, 60)}</span>
                  {run.duration_ms && <span className="text-[9px] text-slate-600">{(run.duration_ms / 1000).toFixed(1)}s</span>}
                </div>
              )) : (
                <p className="text-xs text-slate-500 py-4 text-center">No recent runs</p>
              )}
            </div>
          </Card>

          {employeeStatus && (
            <Card hover={false} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/5">
                <UserCheck className="w-4 h-4 text-lumina-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Autonomous Employee</span>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {[
                  ['Status', employeeStatus.status || 'ready'],
                  ['Missions', String(employeeStatus.missions_completed || 0)],
                  ['Tools', String(employeeStatus.tools_available || 0)],
                ].map(([l, v]) => (
                  <div key={l} className="bg-white/[0.02] rounded-xl px-3 py-2.5 border border-white/5 text-center">
                    <p className="text-[18px] font-bold text-white">{v}</p>
                    <p className="text-[9px] text-slate-500 mt-0.5">{l}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ── CRM ── */}
      {activeSection === 'crm' && crmSummary && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card hover={false} className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-white/5">
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-lumina-400" />
                <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">CRM Overview</span>
              </div>
              <Link to="/crm" className="text-[10px] text-lumina-400 hover:text-lumina-300 flex items-center gap-1">
                Full CRM <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                ['Total Deals', String(crmSummary.total_deals || 0), 'text-blue-400'],
                ['Total Contacts', String(crmSummary.total_contacts || 0), 'text-emerald-400'],
                ['Pipeline Value', `$${(crmSummary.pipeline_value || 0).toLocaleString()}`, 'text-amber-400'],
                ['Won Value', `$${(crmSummary.won_value || 0).toLocaleString()}`, 'text-emerald-400'],
                ['Lost Value', `$${(crmSummary.lost_value || 0).toLocaleString()}`, 'text-red-400'],
                ['Conversion', crmSummary.conversion_rate || '0%', 'text-lumina-400'],
              ].map(([l, v, c]) => (
                <div key={l} className="bg-white/[0.02] rounded-xl px-4 py-3 border border-white/5">
                  <p className={`text-lg font-bold ${c}`}>{v}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">{l}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card hover={false} className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <PieChart className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Pipeline</span>
            </div>
            {crmSummary.total_value > 0 && (
              <div className="space-y-2">
                {[
                  { label: 'Won', value: crmSummary.won_value || 0, color: 'bg-emerald-500' },
                  { label: 'Pipeline', value: crmSummary.pipeline_value || 0, color: 'bg-amber-500' },
                  { label: 'Lost', value: crmSummary.lost_value || 0, color: 'bg-red-500' },
                ].map(({ label, value, color }) => {
                  const pct = crmSummary.total_value > 0 ? (value / crmSummary.total_value) * 100 : 0;
                  return (
                    <div key={label}>
                      <div className="flex justify-between text-[11px] mb-0.5">
                        <span className="text-slate-500">{label}</span>
                        <span className="text-slate-300">${value.toLocaleString()}</span>
                      </div>
                      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ── MARKETING ── */}
      {activeSection === 'marketing' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card hover={false} className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <TrendingUp className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Marketing Summary</span>
            </div>
            {marketingSummary ? (
              <div className="grid grid-cols-2 gap-3">
                {[
                  ['Active Campaigns', String(marketingSummary.active_campaigns || 0)],
                  ['Total Campaigns', String(marketingSummary.total_campaigns || 0)],
                  ['Total Budget', `$${(marketingSummary.total_budget || 0).toLocaleString()}`],
                  ['Total Spent', `$${(marketingSummary.total_spent || 0).toLocaleString()}`],
                  ['Impressions', compactNum(marketingSummary.total_impressions || 0)],
                  ['Clicks', compactNum(marketingSummary.total_clicks || 0)],
                  ['Conversions', String(marketingSummary.total_conversions || 0)],
                  ['Content Published', String(marketingSummary.content_published || 0)],
                ].map(([l, v]) => (
                  <div key={l} className="bg-white/[0.02] rounded-xl px-4 py-3 border border-white/5">
                    <p className="text-xs font-medium text-slate-200">{v}</p>
                    <p className="text-[9px] text-slate-500">{l}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-slate-500 py-4 text-center">No marketing data available</p>
            )}
          </Card>

          <Card hover={false} className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <Globe className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">WhatsApp Business</span>
            </div>
            {whatsapp ? (
              <div className="space-y-2">
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <CheckCircle className={`w-5 h-5 ${whatsapp.configured ? 'text-emerald-400' : 'text-slate-600'}`} />
                  <div>
                    <p className="text-xs text-slate-300">{whatsapp.configured ? 'Connected' : 'Not Connected'}</p>
                    <p className="text-[10px] text-slate-500">{whatsapp.has_api_key ? 'API key configured' : 'No API key'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <Database className="w-5 h-5 text-lumina-400" />
                  <div>
                    <p className="text-xs text-slate-300">{whatsapp.products || 0} products</p>
                    <p className="text-[10px] text-slate-500">Catalog items</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 py-4 text-center">No WhatsApp data</p>
            )}
          </Card>
        </div>
      )}

      {/* ── TASKS ── */}
      {activeSection === 'tasks' && taskStats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card hover={false} className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <Layers className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Task Overview</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                ['Total', taskStats.total || 0, 'text-slate-200'],
                ['Pending', taskStats.pending || 0, 'text-amber-400'],
                ['Running', taskStats.running || 0, 'text-blue-400'],
                ['Completed', taskStats.completed || 0, 'text-emerald-400'],
                ['Failed', taskStats.failed || 0, 'text-red-400'],
                ['Active Runs', taskStats.active_runs || 0, 'text-lumina-400'],
              ].map(([l, v, c]) => (
                <div key={l} className="bg-white/[0.02] rounded-xl px-4 py-3 border border-white/5">
                  <p className={`text-lg font-bold ${c}`}>{v}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">{l}</p>
                </div>
              ))}
            </div>
          </Card>

          <Card hover={false} className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <BarChart3 className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Task Distribution</span>
            </div>
            {taskStats.total > 0 && (
              <div className="space-y-2">
                {[
                  { label: 'Completed', count: taskStats.completed || 0, color: 'bg-emerald-500' },
                  { label: 'Pending', count: taskStats.pending || 0, color: 'bg-amber-500' },
                  { label: 'Running', count: taskStats.running || 0, color: 'bg-blue-500' },
                  { label: 'Failed', count: taskStats.failed || 0, color: 'bg-red-500' },
                ].map(({ label, count, color }) => {
                  const pct = taskStats.total > 0 ? (count / taskStats.total) * 100 : 0;
                  return (
                    <div key={label}>
                      <div className="flex justify-between text-[11px] mb-0.5">
                        <span className="text-slate-500">{label}</span>
                        <span className="text-slate-300">{count} ({pct.toFixed(0)}%)</span>
                      </div>
                      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ── ACTIVITY ── */}
      {activeSection === 'activity' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card hover={false} className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <MessageSquare className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Recent Activity</span>
            </div>
            <div className="space-y-2">
              {[
                { icon: MessageSquare, label: 'Chat', value: `${chatThreads} conversations`, color: 'text-lumina-400' },
                { icon: Code2, label: 'Code Reviews', value: `${codeReviews} reviews`, color: 'text-emerald-400' },
                { icon: Bot, label: 'Agent Runs', value: `${agentRuns.length} recent runs`, color: 'text-violet-400' },
                { icon: BookOpen, label: 'Learning', value: `${learningStats?.total_actions || 0} total actions`, color: 'text-amber-400' },
                { icon: Smartphone, label: 'Android', value: `${(stats as any)?.android_devices || 0} devices`, color: 'text-green-400' },
                { icon: Eye, label: 'Vision', value: `${(stats as any)?.cameras || 0} cameras`, color: 'text-cyan-400' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <item.icon className={`w-4 h-4 ${item.color}`} />
                  <span className="text-xs text-slate-300 flex-1">{item.label}</span>
                  <span className="text-[10px] text-slate-500">{item.value}</span>
                </div>
              ))}
            </div>
          </Card>

          <Card hover={false} className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-white/5">
              <Zap className="w-4 h-4 text-lumina-400" />
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Quick Actions</span>
            </div>
            <div className="space-y-1">
              {[
                { icon: MessageSquare, label: 'New Chat', to: '/chat' },
                { icon: Code2, label: 'Generate Code', to: '/code/generate' },
                { icon: Bug, label: 'Review Code', to: '/code/review' },
                { icon: Bot, label: 'Run Agent', to: '/agents' },
                { icon: Briefcase, label: 'CRM Dashboard', to: '/crm' },
                { icon: FileCode, label: 'Content Writer', to: '/writer' },
              ].map(item => (
                <Link key={item.to} to={item.to}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-white/[0.03] border border-transparent hover:border-white/5 transition-all group">
                  <item.icon className="w-4 h-4 text-lumina-400" />
                  <span className="text-xs text-slate-300 flex-1 group-hover:text-white transition-colors">{item.label}</span>
                  <ChevronRight className="w-3 h-3 text-slate-600" />
                </Link>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
