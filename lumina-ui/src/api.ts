const BASE = '/api';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path}: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`POST ${path}: ${res.status} — ${err.slice(0, 200)}`);
  }
  return res.json();
}

export const api = {
  health: () => get<import('./types').HealthStatus>('/system/health'),
  config: () => get<import('./types').AppConfig>('/system/config'),
  agents: () => get<{ agents: string[] }>('/agents'),
  agentCategories: () => get<Record<string, string[]>>('/agents/categories'),
  chat: (message: string) =>
    post<import('./types').ChatResponse>('/chat', { message }),
  codeGenerate: (description: string, language = 'python') =>
    post<import('./types').CodeResponse>('/code/generate', { description, language }),
  agentRun: (agent: string, task: string) =>
    post<import('./types').AgentResult>('/agents/run', { agent, task }),
  history: (limit = 10) =>
    get<{ conversations: import('./types').Conversation[] }>(`/chat/history?limit=${limit}`),
  healTask: (task: string) =>
    post<{ status: string; result: string; attempts: number }>('/automation/heal', { task }),
  desktopInfo: () => get<{ os: string; hostname: string; cwd: string }>('/desktop/info'),
  listFiles: (path = '.') => get<{ files: Array<{ name: string; type: string; size: number }>; count: number }>(`/desktop/files?path=${path}`),
  crmSummary: () => get<{ total_deals: number; total_contacts: number; total_value: number; won_value: number; pipeline_value: number; conversion_rate: string }>('/crm/summary'),
  listContacts: () => get<{ contacts: Array<{ id: string; name: string; email: string }> }>('/crm/contacts'),
  addContact: (name: string, email: string) => post('/crm/contacts', { name, email }),
  listDeals: () => get<{ deals: Array<{ id: string; title: string; value: number; stage: string }> }>('/crm/deals'),
  addDeal: (title: string, value: number, contactId: string) =>
    post('/crm/deals', { title, value, contact_id: contactId }),
  seoSites: () => get<{ sites: Array<{ id: string; url: string; name: string }> }>('/seo/sites'),
  addSite: (url: string, name = '') => post('/seo/sites', { url, name }),
  whatsappStatus: () => get<{ configured: boolean }>('/whatsapp/status'),
  androidDevices: () => get<{ devices: Array<{ serial: string }> }>('/android/devices'),
  kernelStatus: () => get<{ services: string[] }>('/kernel/status'),
  multiAgentList: () => get<{ agents: import('./types').AgentInfo[]; total: number }>('/multiagent/agents'),
  multiAgentTeams: () => get<{ teams: Record<string, import('./types').AgentInfo[]>; total_teams: number }>('/multiagent/teams'),
  multiAgentOrchestrate: (task: string) =>
    post<import('./types').OrchestrationRun>('/multiagent/orchestrate', { task }),
  multiAgentRuns: () => get<{ runs: import('./types').OrchestrationRun[]; total: number }>('/multiagent/orchestrate/runs'),
  multiAgentRun: (agent: string, task: string) =>
    post<import('./types').AgentResult>('/multiagent/run', { agent, task }),
};
