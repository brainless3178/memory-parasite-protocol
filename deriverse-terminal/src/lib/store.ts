import { create } from 'zustand';
import type { Agent, Infection, ForumReply } from './types';

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
