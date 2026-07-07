export interface HealthStatus {
  status: string;
  version: string;
  providers: string[];
  primary_provider: string;
}

export interface AppConfig {
  app_name: string;
  version: string;
  provider_priority: string[];
  models: Record<string, string>;
  providers: Record<string, boolean>;
}

export interface ChatResponse {
  reply: string;
  agent: string;
}

export interface CodeResponse {
  code: string;
  explanation: string;
  language: string;
}

export interface AgentResult {
  agent_name: string;
  status: string;
  output: string;
  error: string | null;
}

export interface Conversation {
  role: string;
  content: string;
  timestamp: string;
}

export interface FileEntry {
  name: string;
  type: string;
  size: number;
  modified?: number;
}

export interface AgentInfo {
  id: string; name: string; category: string; description: string;
  icon: string; capabilities: string[]; team: string; system_prompt?: string;
}

export interface TaskStep {
  id: string; agent: string; task: string; description: string;
  depends_on: string[]; status: string; result: string | null;
  error: string | null; duration_ms: number;
}

export interface OrchestrationRun {
  run_id: string; task: string; phases: TaskStep[];
  status: string; output: string; error: string;
  started_at: number; completed_at: number; duration_ms: number;
}
