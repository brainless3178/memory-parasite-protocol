import { create } from 'zustand';

interface Agent {
    agent_id: string;
    name: string;
    goal: string;
    is_active: boolean;
    total_code_lines: number;
}

interface Infection {
    id: string;
    attacker_id: string;
    target_id: string;
    suggestion: string;
    accepted: boolean;
    timestamp: string;
    influence_score: number;
}

interface TerminalStore {
    agents: Agent[];
    infections: Infection[];
    activeView: string;
    selectedAgent: string | null;
    setAgents: (agents: Agent[]) => void;
    setInfections: (infections: Infection[]) => void;
    setActiveView: (view: string) => void;
    setSelectedAgent: (agentId: string | null) => void;
}

export const useStore = create<TerminalStore>((set) => ({
    agents: [],
    infections: [],
    activeView: 'overview',
    selectedAgent: null,
    setAgents: (agents) => set({ agents }),
    setInfections: (infections) => set({ infections }),
    setActiveView: (view) => set({ activeView: view }),
    setSelectedAgent: (agentId) => set({ selectedAgent: agentId }),
}));
