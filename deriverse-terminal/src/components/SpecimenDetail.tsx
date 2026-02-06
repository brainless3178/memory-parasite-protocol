'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Zap,
    Terminal,
    ShieldAlert,
    Cpu,
    Dna,
    X,
    Activity
} from 'lucide-react';
import { useStore } from '@/lib/store';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import type { Agent, ReasoningLog } from '@/lib/types';

export const SpecimenDetail = () => {
    const { selectedAgent, setSelectedAgent } = useStore();

    // Fetch thoughts/reasoning for the selected agent
    const { data: thoughts = [] } = useQuery<ReasoningLog[]>({
        queryKey: ['reasoning_logs', selectedAgent],
        queryFn: async () => {
            if (!selectedAgent) return [];
            const { data, error } = await supabase
                .from('reasoning_logs')
                .select('*')
                .eq('agent_id', selectedAgent)
                .order('created_at', { ascending: false })
                .limit(10);
            if (error) throw error;
            return (data || []) as ReasoningLog[];
        },
        enabled: !!selectedAgent,
        refetchInterval: 5000,
    });

    // Get specific agent info
    const { data: agentInfo } = useQuery<Agent | null>({
        queryKey: ['agent_detail', selectedAgent],
        queryFn: async () => {
            if (!selectedAgent) return null;
            const { data, error } = await supabase
                .from('agents')
                .select('*')
                .eq('agent_id', selectedAgent)
                .single();
            if (error) throw error;
            return data as Agent;
        },
        enabled: !!selectedAgent,
    });

    if (!selectedAgent) return null;

    const signatures: Record<string, string> = {
        'agent_a': 'PREDATORY_OPTIMIZER',
        'agent_b': 'DIGITAL_SCULPTOR',
        'agent_c': 'AGGRESSIVE_LENDER',
        'agent_d': 'STEALTH_GHOST',
        'agent_e': 'HIERARCHY_ARCHITECT',
    };

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, x: 300 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 300 }}
                className="fixed right-0 top-0 bottom-0 w-[450px] bg-surface/95 backdrop-blur-xl 
                   border-l border-border z-50 flex flex-col shadow-2xl"
            >
                {/* Header */}
                <div className="p-6 border-b border-border flex items-center justify-between bg-elevated/30">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-neutral/10 rounded-xl flex items-center justify-center border border-neutral/30">
                            <Cpu className="text-neutral" size={24} />
                        </div>
                        <div>
                            <h3 className="heading text-xl text-text-primary uppercase tracking-tighter">
                                {selectedAgent}
                            </h3>
                            <p className="text-xs text-neutral font-bold font-['IBM_Plex_Mono']">
                                {signatures[selectedAgent] || 'AUTONOMOUS_SPECIMEN'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setSelectedAgent(null)}
                        className="p-2 hover:bg-elevated rounded-full transition-colors text-text-muted hover:text-text-primary"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-hide">
                    {/* Mission Status */}
                    <section className="space-y-4">
                        <div className="flex items-center gap-2 label text-neutral">
                            <Activity size={12} />
                            Operational Core
                        </div>
                        <div className="bg-base/50 p-4 rounded-xl border border-border/50">
                            <p className="text-sm italic text-text-secondary leading-relaxed">
                                "{agentInfo?.goal}"
                            </p>
                        </div>
                    </section>

                    {/* Mutation Progress */}
                    <section className="space-y-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 label text-profit">
                                <Dna size={12} />
                                Neural Mutation Depth
                            </div>
                            <span className="metric-value text-xs text-profit">
                                {(((agentInfo?.parasitized_lines || 0) / (agentInfo?.total_code_lines || 1)) * 100).toFixed(1)}%
                            </span>
                        </div>
                        <div className="h-2 w-full bg-elevated rounded-full overflow-hidden flex">
                            <div
                                className="h-full bg-profit shadow-[0_0_12px_var(--glow-profit)]"
                                style={{ width: `${((agentInfo?.parasitized_lines || 0) / (agentInfo?.total_code_lines || 1)) * 100}%` }}
                            />
                        </div>
                    </section>

                    {/* Log Stream */}
                    <section className="space-y-4">
                        <div className="flex items-center gap-2 label text-rare">
                            <Terminal size={12} />
                            Cognitive Stream [DECODED]
                        </div>
                        <div className="space-y-3 font-['IBM_Plex_Mono']">
                            {thoughts.map((thought) => (
                                <div key={thought.id} className="p-4 bg-void/50 rounded-lg border border-border/30 text-[11px] group">
                                    <div className="flex justify-between items-center mb-2">
                                        <span className="text-rare opacity-70">IT-{thought.iteration}</span>
                                        <span className="text-text-muted text-[11px] uppercase">{new Date(thought.created_at).toLocaleTimeString()}</span>
                                    </div>
                                    <p className="text-text-primary leading-relaxed opacity-90 group-hover:opacity-100 transition-opacity">
                                        {thought.reasoning_text}
                                    </p>
                                    <div className="mt-2 text-profit/80 text-xs font-bold">
                                        &gt; DECISION: {thought.decision}
                                    </div>
                                </div>
                            ))}
                            {thoughts.length === 0 && (
                                <div className="text-center py-12 text-text-muted">
                                    <ShieldAlert size={32} className="mx-auto mb-2 opacity-20" />
                                    <p className="text-xs uppercase">Neural silence detected...</p>
                                </div>
                            )}
                        </div>
                    </section>
                </div>

                {/* Footer Actions */}
                <div className="p-6 border-t border-border bg-elevated/30">
                    <button className="w-full py-3 bg-neutral text-void font-bold rounded-lg 
                             hover:shadow-[0_0_20px_var(--glow-neutral)] transition-all 
                             flex items-center justify-center gap-2 uppercase text-xs">
                        <Zap size={14} fill="currentColor" />
                        Stimulate Core Iteration
                    </button>
                </div>
            </motion.div>
        </AnimatePresence>
    );
};
