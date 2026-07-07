import { useState, useEffect, useCallback } from 'react';
import {
  Crown, Code, Bug, Palette, Globe, Container, Shield, Database,
  Smartphone, Megaphone, BarChart3, FileText, Headphones, ClipboardList,
  Bot, Play, Loader2, CheckCircle, XCircle, AlertTriangle, Clock,
  ArrowRight, ChevronRight, RefreshCw, Search, Zap, Timer, Layers,
  Users, Network, GitBranch, Sparkles, Activity, Plus, X, Menu,
  TrendingUp, HelpCircle, AtSign, Calculator, Calendar, Share2, PenLine,
  Eye,
} from 'lucide-react';
import PageHeader from '../components/ui/PageHeader';
import Card, { CardSection } from '../components/ui/Card';
import { useToast } from '../hooks/useToast';

const BASE = '/api/multiagent';

interface AgentInfo {
  id: string; name: string; category: string; description: string;
  icon: string; capabilities: string[]; team: string; system_prompt?: string;
}

interface TaskStep {
  id: string; agent: string; task: string; description: string;
  depends_on: string[]; status: string; result: string | null;
  error: string | null; duration_ms: number;
}

interface OrchestrationRun {
  run_id: string; task: string; phases: TaskStep[];
  status: string; output: string; error: string;
  started_at: number; completed_at: number; duration_ms: number;
}

interface AgentRun {
  run_id: string; agent_id: string; agent_name: string; task: string;
  status: string; output: string; error: string;
  started_at: string; completed_at: string; duration_ms: number;
}

interface TeamsData {
  teams: Record<string, AgentInfo[]>;
  total_teams: number;
}

const ICON_MAP: Record<string, any> = {
  Crown, ClipboardList, Code, Bug, Palette, Globe, Container, Shield,
  Database, Smartphone, Megaphone, BarChart3, FileText, Headphones, Bot,
  TrendingUp, HelpCircle, AtSign, Calculator, Calendar, Share2, PenLine, Eye,
};

function getAgentIcon(id: string) {
  const iconMap: Record<string, string> = {
    ceo: 'Crown', planner: 'ClipboardList', programmer: 'Code',
    tester: 'Bug', designer: 'Palette', browser_operator: 'Globe',
    devops_engineer: 'Container', security_auditor: 'Shield',
    database_engineer: 'Database', mobile_developer: 'Smartphone',
    marketing_agent: 'Megaphone', finance_agent: 'BarChart3',
    documentation_writer: 'FileText', voice_assistant: 'Headphones',
    sales_agent: 'TrendingUp', customer_support_agent: 'HelpCircle',
    email_manager: 'AtSign', accountant: 'Calculator',
    personal_assistant: 'Calendar', social_media_manager: 'Share2',
    proposal_writer: 'PenLine', security_monitor: 'Eye',
  };
  return ICON_MAP[iconMap[id]] || Bot;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

const TEAMS_LABELS: Record<string, string> = {
  leadership: 'Leadership',
  development: 'Development',
  quality: 'Quality',
  design: 'Design',
  automation: 'Automation',
  infrastructure: 'Infrastructure',
  security: 'Security',
  business: 'Business',
  content: 'Content',
  support: 'Support',
  marketing: 'Marketing',
  communication: 'Communication',
};

function PhaseStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-slate-500/10 text-slate-400',
    running: 'bg-blue-500/10 text-blue-400',
    success: 'bg-emerald-500/10 text-emerald-400',
    failed: 'bg-red-500/10 text-red-400',
    skipped: 'bg-amber-500/10 text-amber-400',
  };
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}

function formatDuration(ms: number) {
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
}

export default function MultiAgent() {
  const { addToast } = useToast();
  const [activeView, setActiveView] = useState('overview');
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [teams, setTeams] = useState<TeamsData | null>(null);
  const [orchRuns, setOrchRuns] = useState<OrchestrationRun[]>([]);
  const [selectedOrch, setSelectedOrch] = useState<OrchestrationRun | null>(null);
  const [loading, setLoading] = useState(false);

  const [task, setTask] = useState('');
  const [orchestrating, setOrchestrating] = useState(false);
  const [currentOrch, setCurrentOrch] = useState<OrchestrationRun | null>(null);

  const [search, setSearch] = useState('');
  const [selectedAgent, setSelectedAgent] = useState<AgentInfo | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [agentsData, teamsData, orchData] = await Promise.all([
        get<{ agents: AgentInfo[] }>('/agents'),
        get<TeamsData>('/teams'),
        get<{ runs: OrchestrationRun[] }>('/orchestrate/runs'),
      ]);
      setAgents(agentsData.agents);
      setTeams(teamsData);
      setOrchRuns(orchData.runs);
    } catch { addToast('Failed to load agent data', 'error'); }
  }, [addToast]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const startOrchestration = async () => {
    if (!task.trim()) return;
    setOrchestrating(true);
    setCurrentOrch(null);
    try {
      const run = await post<OrchestrationRun>('/orchestrate', { task });
      setCurrentOrch(run);
      addToast('Orchestration complete', 'success');
      loadAll();
    } catch {
      addToast('Orchestration failed', 'error');
    }
    setOrchestrating(false);
  };

  const isCEO = (a: AgentInfo) => a.id === 'ceo';
  const specialistAgents = agents.filter(a => !isCEO(a));
  const filteredSpecialists = specialistAgents.filter(a =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.id.includes(search.toLowerCase()) ||
    a.description.toLowerCase().includes(search.toLowerCase()) ||
    a.capabilities.some(c => c.toLowerCase().includes(search.toLowerCase()))
  );

  const ceoAgent = agents.find(isCEO);

  const views = [
    { id: 'overview', label: 'Overview', icon: Network },
    { id: 'orchestrate', label: 'Orchestrate', icon: GitBranch },
    { id: 'agents', label: 'Agents', icon: Users },
    { id: 'history', label: `History (${orchRuns.length})`, icon: Clock },
  ];

  const renderHierarchy = () => (
    <div className="flex flex-col items-center py-6">
      {ceoAgent && (
        <div className="relative">
          <button onClick={() => setSelectedAgent(ceoAgent)}
            className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 border border-amber-500/30 rounded-2xl p-5 text-center w-48 hover:from-amber-500/30 hover:to-amber-600/20 transition-all group">
            <div className="w-14 h-14 rounded-2xl bg-amber-500/20 text-amber-400 flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
              <Crown className="w-7 h-7" />
            </div>
            <p className="text-sm font-semibold text-slate-200">CEO AI</p>
            <p className="text-[10px] text-slate-500 mt-1">Orchestrator</p>
          </button>
          <div className="h-8 w-px bg-gradient-to-b from-amber-500/40 to-slate-600/20 mx-auto" />
          <div className="w-64 h-px bg-gradient-to-r from-transparent via-slate-600/30 to-transparent mx-auto" />
        </div>
      )}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-7 gap-2 mt-4 max-w-4xl">
        {specialistAgents.map(a => {
          const Icon = getAgentIcon(a.id);
          return (
            <button key={a.id} onClick={() => setSelectedAgent(a)}
              className="bg-white/[0.02] border border-white/5 hover:border-lumina-500/30 rounded-xl p-3 text-center group transition-all">
              <div className="w-9 h-9 rounded-xl bg-lumina-600/10 text-lumina-400 flex items-center justify-center mx-auto mb-2 group-hover:bg-lumina-600/20 transition-colors">
                <Icon className="w-4 h-4" />
              </div>
              <p className="text-[10px] font-medium text-slate-300 truncate leading-tight">{a.name}</p>
            </button>
          );
        })}
      </div>
    </div>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      <Card hover={false} className="overflow-hidden">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/15 text-amber-400 flex items-center justify-center">
                <Crown className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-200">Agent Hierarchy</p>
                <p className="text-[10px] text-slate-500">1 CEO · {specialistAgents.length} Specialists</p>
              </div>
            </div>
            <button onClick={() => setActiveView('orchestrate')}
              className="text-xs bg-lumina-600 hover:bg-lumina-500 text-white rounded-lg px-4 py-2 font-medium transition-all flex items-center gap-2">
              <Zap className="w-3.5 h-3.5" /> New Task
            </button>
          </div>
          {renderHierarchy()}
        </div>
      </Card>

      {teams && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(teams.teams).map(([teamId, members]) => (
            <Card key={teamId} hover={false}>
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-semibold text-slate-300">
                    {TEAMS_LABELS[teamId] || teamId}
                  </p>
                  <span className="text-[10px] text-slate-600">{members.length}</span>
                </div>
                <div className="space-y-1.5">
                  {members.map(m => {
                    const Icon = getAgentIcon(m.id);
                    return (
                      <div key={m.id} className="flex items-center gap-2 bg-white/[0.02] rounded-lg px-2.5 py-1.5">
                        <Icon className="w-3.5 h-3.5 text-lumina-400 shrink-0" />
                        <span className="text-[11px] text-slate-400">{m.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );

  const renderOrchestrate = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="space-y-4">
        <Card hover={false} className="space-y-4">
          <CardSection label="New Orchestration">
            <textarea value={task} onChange={e => setTask(e.target.value)} rows={5}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none focus:border-lumina-500/50 resize-none"
              placeholder="Describe a complex task for the multi-agent system...

Examples:
- 'Build a full-stack TODO app with React, FastAPI, and PostgreSQL'
- 'Create a marketing landing page with SEO optimization'
- 'Design a microservice architecture for an e-commerce platform'
- 'Perform a security audit on our API and fix all vulnerabilities'" />
          </CardSection>
          <button onClick={startOrchestration} disabled={orchestrating || !task.trim()}
            className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-600 text-white rounded-xl px-6 py-3 text-sm font-semibold transition-all flex items-center gap-2 shadow-lg shadow-amber-500/20 w-fit">
            {orchestrating ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitBranch className="w-4 h-4" />}
            {orchestrating ? 'Orchestrating...' : 'Run Multi-Agent Task'}
          </button>
        </Card>

        {currentOrch && (
          <Card hover={false} className="space-y-4 border-amber-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  currentOrch.status === 'success' ? 'bg-emerald-500' :
                  currentOrch.status === 'failed' ? 'bg-red-500' :
                  currentOrch.status === 'partial' ? 'bg-amber-500' : 'bg-slate-500'
                }`} />
                <span className="text-sm font-medium text-slate-200">Orchestration Result</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                  currentOrch.status === 'success' ? 'bg-emerald-500/10 text-emerald-400' :
                  currentOrch.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                  currentOrch.status === 'partial' ? 'bg-amber-500/10 text-amber-400' :
                  'bg-slate-500/10 text-slate-400'
                }`}>{currentOrch.status}</span>
              </div>
              <span className="text-[10px] text-slate-600 flex items-center gap-1">
                <Timer className="w-3 h-3" /> {formatDuration(currentOrch.duration_ms)}
              </span>
            </div>

            <div className="space-y-1.5">
              {currentOrch.phases.length > 0 && (
                <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Phases</p>
              )}
              <div className="space-y-1.5 max-h-60 overflow-y-auto">
                {currentOrch.phases.map((phase, i) => {
                  const Icon = getAgentIcon(
                    Object.entries({
                      planner: 'planner', programmer: 'programmer', tester: 'tester',
                      designer: 'designer', 'browser operator': 'browser_operator',
                      'devops engineer': 'devops_engineer', 'security auditor': 'security_auditor',
                      'database engineer': 'database_engineer', 'mobile developer': 'mobile_developer',
                      'marketing agent': 'marketing_agent', 'finance agent': 'finance_agent',
                      'documentation writer': 'documentation_writer', 'voice assistant': 'voice_assistant',
                      'sales agent': 'sales_agent', 'customer support': 'customer_support_agent',
                      'email manager': 'email_manager', accountant: 'accountant',
                      'personal assistant': 'personal_assistant', 'social media manager': 'social_media_manager',
                      'proposal writer': 'proposal_writer', 'security monitor': 'security_monitor',
                    }).find(([, v]) => v === phase.agent.toLowerCase().replace(/\s+/g, '_'))?.[0] || phase.agent
                  );
                  const agentKey = phase.agent.toLowerCase().replace(/\s+/g, '_');
                  const canonicalKey = Object.keys({
                    planner: 1, programmer: 1, tester: 1, designer: 1,
                    browser_operator: 1, devops_engineer: 1, security_auditor: 1,
                    database_engineer: 1, mobile_developer: 1, marketing_agent: 1,
                    finance_agent: 1, documentation_writer: 1, voice_assistant: 1,
                    sales_agent: 1, customer_support_agent: 1, email_manager: 1,
                    accountant: 1, personal_assistant: 1, social_media_manager: 1,
                    proposal_writer: 1, security_monitor: 1,
                  }).find(k => k.includes(agentKey) || agentKey.includes(k));
                  const PhaseIcon = canonicalKey ? getAgentIcon(canonicalKey) : Bot;
                  return (
                    <div key={phase.id} className={`rounded-xl border p-3 transition-all ${
                      phase.status === 'success' ? 'bg-emerald-500/5 border-emerald-800/20' :
                      phase.status === 'failed' ? 'bg-red-500/5 border-red-800/20' :
                      phase.status === 'running' ? 'bg-blue-500/5 border-blue-800/20' :
                      phase.status === 'skipped' ? 'bg-amber-500/5 border-amber-800/20' :
                      'bg-white/5 border-white/5'
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <PhaseIcon className="w-4 h-4 text-lumina-400 shrink-0" />
                          <div className="min-w-0">
                            <p className="text-xs font-medium text-slate-200 truncate">{phase.agent}</p>
                            <p className="text-[10px] text-slate-500 truncate">{phase.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <PhaseStatusBadge status={phase.status} />
                          {phase.duration_ms > 0 && (
                            <span className="text-[10px] text-slate-600">{formatDuration(phase.duration_ms)}</span>
                          )}
                        </div>
                      </div>
                      {phase.result && phase.status === 'success' && (
                        <pre className="text-[10px] text-slate-400 whitespace-pre-wrap font-sans line-clamp-2 mt-1 bg-slate-950/30 rounded-lg p-2">{phase.result.slice(0, 300)}</pre>
                      )}
                      {phase.error && (
                        <p className="text-[10px] text-red-400 mt-1">{phase.error}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {currentOrch.output && (
              <div className="bg-slate-950/50 rounded-xl p-4 border border-white/5">
                <p className="text-[10px] text-slate-500 mb-2 font-medium uppercase tracking-wider">Synthesis</p>
                <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-64 overflow-y-auto">{currentOrch.output}</pre>
              </div>
            )}
          </Card>
        )}
      </div>

      <div className="space-y-4">
        <Card hover={false} className="space-y-4">
          <CardSection label="Recent Orchestrations">
            {orchRuns.length === 0 ? (
              <div className="text-center py-8">
                <GitBranch className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                <p className="text-sm text-slate-400">No orchestrations yet</p>
                <p className="text-xs text-slate-500 mt-1">Submit a task to see results here</p>
              </div>
            ) : (
              <div className="space-y-1.5 max-h-96 overflow-y-auto">
                {orchRuns.map(r => (
                  <button key={r.run_id} onClick={() => setSelectedOrch(r)}
                    className="w-full flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all text-left">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-slate-200 truncate">{r.task.slice(0, 80)}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {r.phases.length} phases · {formatDuration(r.duration_ms)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      <PhaseStatusBadge status={r.status} />
                      <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </CardSection>
        </Card>
      </div>
    </div>
  );

  const renderAgentDetail = (a: AgentInfo) => {
    const Icon = getAgentIcon(a.id);
    return (
      <div className="space-y-4">
        <button onClick={() => setSelectedAgent(null)}
          className="text-xs text-lumina-400 hover:text-lumina-300 flex items-center gap-1">
          <ChevronRight className="w-3 h-3 rotate-180" /> Back to agents
        </button>
        <Card hover={false}>
          <div className="p-6">
            <div className="flex items-start gap-4">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center shrink-0 ${
                a.id === 'ceo' ? 'bg-amber-500/20 text-amber-400' : 'bg-lumina-600/15 text-lumina-400'
              }`}>
                <Icon className="w-8 h-8" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-lg font-semibold text-slate-200">{a.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{a.id} · {a.team}</p>
                <p className="text-sm text-slate-400 mt-2">{a.description}</p>
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {a.capabilities?.map(c => (
                    <span key={c} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-slate-400">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Card>
        {a.system_prompt && (
          <Card hover={false}>
            <CardSection label="System Prompt">
              <pre className="text-[11px] text-slate-400 whitespace-pre-wrap font-mono bg-slate-950/50 rounded-xl p-4 border border-white/5 max-h-80 overflow-y-auto leading-relaxed">
                {a.system_prompt}
              </pre>
            </CardSection>
          </Card>
        )}
      </div>
    );
  };

  const renderAgentGrid = () => (
    <div className="space-y-6">
      {selectedAgent ? renderAgentDetail(selectedAgent) : (
        <>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/5 rounded-xl px-4 py-2.5 flex-1 border border-white/10">
              <Search className="w-4 h-4 text-slate-500" />
              <input value={search} onChange={e => setSearch(e.target.value)}
                className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                placeholder="Search agents by name, capability, or description..." />
            </div>
            <span className="text-xs text-slate-500">{agents.length} agents</span>
          </div>

          {agents.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filteredSpecialists.map(a => {
                const Icon = getAgentIcon(a.id);
                return (
                  <button key={a.id} onClick={() => setSelectedAgent(a)}
                    className="text-left bg-white/[0.02] border border-white/10 hover:border-lumina-500/30 hover:bg-white/[0.04] rounded-xl p-4 transition-all group">
                    <div className="flex items-start gap-3">
                      <div className="w-11 h-11 rounded-xl bg-lumina-600/15 text-lumina-400 flex items-center justify-center shrink-0 group-hover:bg-lumina-600/25 transition-colors">
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-slate-200 truncate">{a.name}</p>
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500">{a.team}</span>
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{a.description}</p>
                        <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                          {a.capabilities?.slice(0, 4).map(c => (
                            <span key={c} className="text-[9px] px-1.5 py-0.5 rounded-full bg-white/5 text-slate-500">{c}</span>
                          ))}
                          {(a.capabilities?.length || 0) > 4 && (
                            <span className="text-[9px] text-slate-600">+{a.capabilities!.length - 4}</span>
                          )}
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-lumina-400 transition-colors shrink-0 mt-1" />
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );

  const renderHistory = () => (
    <div className="space-y-4">
      {selectedOrch ? (
        <div className="space-y-4">
          <button onClick={() => setSelectedOrch(null)}
            className="text-xs text-lumina-400 hover:text-lumina-300 flex items-center gap-1">
            <ChevronRight className="w-3 h-3 rotate-180" /> Back to history
          </button>
          <Card hover={false} className="space-y-4 border-amber-500/20">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  selectedOrch.status === 'success' ? 'bg-emerald-500' :
                  selectedOrch.status === 'failed' ? 'bg-red-500' :
                  selectedOrch.status === 'partial' ? 'bg-amber-500' : 'bg-slate-500'
                }`} />
                <div>
                  <p className="text-sm font-medium text-slate-200">Orchestration</p>
                  <p className="text-[10px] text-slate-500">{selectedOrch.run_id} · {new Date(selectedOrch.started_at * 1000).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-600 flex items-center gap-1"><Timer className="w-3 h-3" /> {formatDuration(selectedOrch.duration_ms)}</span>
                <PhaseStatusBadge status={selectedOrch.status} />
              </div>
            </div>
            <div className="bg-white/5 rounded-lg px-4 py-3">
              <p className="text-[10px] text-slate-500 mb-1">Task</p>
              <p className="text-sm text-slate-300">{selectedOrch.task}</p>
            </div>
            <div className="space-y-1.5">
              <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Phases</p>
              <div className="space-y-1.5">
                {selectedOrch.phases.map(phase => {
                  const canonicalKey = Object.keys({
                    planner: 1, programmer: 1, tester: 1, designer: 1,
                    browser_operator: 1, devops_engineer: 1, security_auditor: 1,
                    database_engineer: 1, mobile_developer: 1, marketing_agent: 1,
                    finance_agent: 1, documentation_writer: 1, voice_assistant: 1,
                    sales_agent: 1, customer_support_agent: 1, email_manager: 1,
                    accountant: 1, personal_assistant: 1, social_media_manager: 1,
                    proposal_writer: 1, security_monitor: 1,
                  }).find(k => k.includes(phase.agent.toLowerCase().replace(/\s+/g, '_'))
                    || phase.agent.toLowerCase().replace(/\s+/g, '_').includes(k));
                  const PhaseIcon = canonicalKey ? getAgentIcon(canonicalKey) : Bot;
                  return (
                    <div key={phase.id} className={`rounded-xl border p-3 ${
                      phase.status === 'success' ? 'bg-emerald-500/5 border-emerald-800/20' :
                      phase.status === 'failed' ? 'bg-red-500/5 border-red-800/20' :
                      phase.status === 'running' ? 'bg-blue-500/5 border-blue-800/20' :
                      phase.status === 'skipped' ? 'bg-amber-500/5 border-amber-800/20' :
                      'bg-white/5 border-white/5'
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <PhaseIcon className="w-4 h-4 text-lumina-400" />
                          <span className="text-xs font-medium text-slate-200">{phase.agent}</span>
                          <span className="text-[10px] text-slate-500">{phase.description}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <PhaseStatusBadge status={phase.status} />
                          {phase.duration_ms > 0 && <span className="text-[10px] text-slate-600">{formatDuration(phase.duration_ms)}</span>}
                        </div>
                      </div>
                      {phase.task && (
                        <p className="text-[10px] text-slate-500 mb-1 bg-slate-950/30 rounded-lg p-2">Task: {phase.task}</p>
                      )}
                      {phase.result && (
                        <pre className="text-[10px] text-slate-400 whitespace-pre-wrap font-sans mt-1 max-h-32 overflow-y-auto">{phase.result.slice(0, 500)}</pre>
                      )}
                      {phase.error && <p className="text-[10px] text-red-400 mt-1">{phase.error}</p>}
                    </div>
                  );
                })}
              </div>
            </div>
            {selectedOrch.output && (
              <div className="bg-slate-950/50 rounded-xl p-4 border border-white/5">
                <p className="text-[10px] text-slate-500 mb-2">Synthesis</p>
                <pre className="text-sm text-slate-300 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">{selectedOrch.output}</pre>
              </div>
            )}
          </Card>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">{orchRuns.length} orchestration runs</span>
            <button onClick={loadAll} className="p-2 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-slate-200 transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          {orchRuns.length === 0 ? (
            <Card hover={false} className="text-center py-12">
              <GitBranch className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-sm text-slate-400">No orchestrations yet</p>
              <p className="text-xs text-slate-500 mt-1">Submit a task in the Orchestrate tab</p>
            </Card>
          ) : (
            <div className="space-y-2">
              {orchRuns.map(r => (
                <Card key={r.run_id} onClick={() => setSelectedOrch(r)} className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-slate-200 truncate">{r.task.slice(0, 100)}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-[10px] text-slate-500">{r.phases.length} phases</span>
                        <span className="text-[10px] text-slate-500 flex items-center gap-1">
                          <Timer className="w-3 h-3" /> {formatDuration(r.duration_ms)}
                        </span>
                        <span className="text-[10px] text-slate-500">{new Date(r.started_at * 1000).toLocaleDateString()}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 ml-2">
                      <PhaseStatusBadge status={r.status} />
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );

  return (
    <div className="p-6 space-y-6">
      <PageHeader icon={Crown} title="Multi-Agent System"
        description="CEO AI orchestrates specialists to tackle complex tasks" />

      <div className="flex items-center gap-1 bg-white/[0.02] rounded-xl p-1 border border-white/5 w-fit">
        {views.map(v => (
          <button key={v.id} onClick={() => setActiveView(v.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all ${
              activeView === v.id
                ? 'bg-amber-600/15 text-amber-300 border border-amber-500/20'
                : 'text-slate-400 hover:text-slate-200'
            }`}>
            <v.icon className="w-3.5 h-3.5" /> {v.label}
          </button>
        ))}
      </div>

      {activeView === 'overview' && renderOverview()}
      {activeView === 'orchestrate' && renderOrchestrate()}
      {activeView === 'agents' && renderAgentGrid()}
      {activeView === 'history' && renderHistory()}
    </div>
  );
}
