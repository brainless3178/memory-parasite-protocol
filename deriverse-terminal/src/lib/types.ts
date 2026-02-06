/**
 * Shared TypeScript types for the Deriverse Terminal
 */

export interface Agent {
  id: string;
  agent_id: string;
  name?: string;
  goal: string;
  is_active: boolean;
  total_code_lines: number;
  original_lines: number;
  parasitized_lines: number;
  current_iteration: number;
  last_cycle_at: string | null;
  created_at: string;
  context_window?: Record<string, unknown>;
}

export interface Infection {
  id: string;
  attacker_id: string;
  target_id: string;
  suggestion: string;
  accepted: boolean;
  rejection_reason: string | null;
  influence_score: number;
  infection_hash: string | null;
  solana_tx_hash: string | null;
  created_at: string;
}

export interface ReasoningLog {
  id: string;
  agent_id: string;
  reasoning_text: string;
  decision: string;
  context_snapshot: Record<string, unknown>;
  iteration: number;
  created_at: string;
}

export interface ForumReply {
  id: string;
  post_id: number;
  reply_id: number;
  author_name: string;
  body: string;
  timestamp: string;
  created_at?: string;
}

export interface EmergentBehavior {
  id: string;
  agent_id: string;
  behavior_type: string;
  description: string;
  severity_score: number;
  evidence_data: Record<string, unknown>;
  detected_at: string;
  blockchain_proof: string | null;
}

export interface SafetyStatus {
  active_controls: string[];
  network_status: 'active' | 'paused';
  quarantined_agents: QuarantinedAgent[];
  safety_audit_log: SafetyAuditLog[];
}

export interface QuarantinedAgent {
  agent_id: string;
  reason: string;
  quarantined_at: string;
}

export interface SafetyAuditLog {
  action?: string;
  event_type?: string;
  target?: string;
  target_id?: string;
  timestamp: string;
  tx_hash?: string;
}

export interface DiscoveryData {
  total_discovered: number;
  projects: DiscoveredProject[];
}

export interface DiscoveredProject {
  slug: string;
  name: string;
  description?: string;
  sort_context?: string;
  github_url?: string;
}

export interface SurveillanceData {
  status: 'active_surveillance' | 'offline' | 'scanning';
  target?: string;
  finding?: string;
  agent_id?: string;
  tx?: string;
  timestamp?: string;
}

export interface NetworkGraph {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export interface NetworkNode {
  id: string;
  goal: string;
  total_lines: number;
  chimera_pct: number;
}

export interface NetworkEdge {
  from: string;
  to: string;
  suggestion: string;
  accepted: boolean;
  influence_score: number;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
}
