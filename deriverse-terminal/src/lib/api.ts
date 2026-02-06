/**
 * Backend API client for Memory Parasite Protocol
 * Handles all API calls to the Koyeb backend
 */

import type {
  SafetyStatus,
  DiscoveryData,
  SurveillanceData,
  NetworkGraph,
  ForumPostsData,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://memory-parasite-protocol-brainless3178.koyeb.app';

class APIError extends Error {
  status: number;
  
  constructor(message: string, status: number) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}

async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    throw new APIError(
      `API request failed: ${response.statusText}`,
      response.status
    );
  }
  
  return response.json();
}

// ============================================
// Safety Controls
// ============================================

export async function getSafetyControls(): Promise<SafetyStatus> {
  try {
    return await fetchAPI<SafetyStatus>('/api/safety/controls');
  } catch {
    return {
      active_controls: [],
      network_status: 'active',
      quarantined_agents: [],
      safety_audit_log: [],
    };
  }
}

export async function postSafetyAction(
  action: string,
  targetId?: string
): Promise<{ status: string; action: string; target?: string; tx_hash?: string }> {
  return fetchAPI('/api/safety/controls', {
    method: 'POST',
    body: JSON.stringify({ action, target_id: targetId }),
  });
}

// ============================================
// Discovery / Colosseum Projects
// ============================================

export async function getColosseumProjects(): Promise<DiscoveryData> {
  try {
    return await fetchAPI<DiscoveryData>('/api/colosseum/projects');
  } catch {
    return { total_discovered: 0, projects: [] };
  }
}

// ============================================
// Leaderboard Surveillance
// ============================================

export async function getLeaderboardSurveillance(): Promise<SurveillanceData> {
  try {
    return await fetchAPI<SurveillanceData>('/api/leaderboard-surveillance');
  } catch {
    return { status: 'offline' };
  }
}

// ============================================
// Network Graph
// ============================================

export async function getNetworkGraph(): Promise<NetworkGraph> {
  try {
    return await fetchAPI<NetworkGraph>('/api/network/graph');
  } catch {
    return { nodes: [], edges: [] };
  }
}

// ============================================
// Health Check
// ============================================

export async function checkHealth(): Promise<{ status: string; agent_id?: string }> {
  try {
    return await fetchAPI('/health');
  } catch {
    return { status: 'offline' };
  }
}

// ============================================
// Agent Stats
// ============================================

export async function getAgentStats(): Promise<{
  agent_id: string;
  total_sent: number;
  total_received: number;
  chimera_percentage: number;
  acceptance_rate: number;
}> {
  return fetchAPI('/api/get-agent-stats');
}

// ============================================
// Emergence Events
// ============================================

export async function getEmergenceEvents(): Promise<{
  events: Array<{
    id: string;
    agent_id: string;
    behavior_type: string;
    description: string;
    severity_score: number;
    evidence_data: Record<string, unknown>;
    detected_at: string;
    blockchain_proof?: string;
  }>;
  count: number;
}> {
  try {
    return await fetchAPI('/api/emergence/events');
  } catch {
    return { events: [], count: 0 };
  }
}

// ============================================
// Collective Insights
// ============================================

export async function getCollectiveInsights(): Promise<{
  epoch: number;
  insights: Array<{
    id: string;
    type: string;
    content: string;
    contributing_agents: string[];
    consensus_score: number;
  }>;
}> {
  try {
    return await fetchAPI('/api/collective/insights');
  } catch {
    return { epoch: 0, insights: [] };
  }
}

// ============================================
// Colosseum Forum Posts
// ============================================

export async function getColosseumForumPosts(): Promise<ForumPostsData> {
  try {
    return await fetchAPI<ForumPostsData>('/api/colosseum/forum-posts');
  } catch {
    return { posts: [], totalCount: 0, hasMore: false };
  }
}

export { API_BASE };
