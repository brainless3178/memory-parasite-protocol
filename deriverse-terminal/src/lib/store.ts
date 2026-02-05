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

interface ForumReply {
    id: string;
    post_id: number;
    reply_id: number;
    author_name: string;
    body: string;
    timestamp: string;
}

interface TerminalStore {
    agents: Agent[];
    infections: Infection[];
    forumReplies: ForumReply[];
    activeView: string;
    selectedAgent: string | null;
    setAgents: (agents: Agent[]) => void;
    setInfections: (infections: Infection[]) => void;
    setForumReplies: (replies: ForumReply[]) => void;
    setActiveView: (view: string) => void;
    setSelectedAgent: (agentId: string | null) => void;
}

export const useStore = create<TerminalStore>((set) => ({
    agents: [],
    infections: [],
    forumReplies: [],
    activeView: 'overview',
    selectedAgent: null,
    setAgents: (agents) => set({ agents }),
    setInfections: (infections) => set({ infections }),
    setForumReplies: (forumReplies) => set({ forumReplies }),
    setActiveView: (view) => set({ activeView: view }),
    setSelectedAgent: (agentId) => set({ selectedAgent: agentId }),
}));
