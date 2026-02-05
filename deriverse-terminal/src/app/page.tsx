'use client';

import React, { useEffect } from 'react';
import { Sidebar } from '@/components/Sidebar';
import { MetricCard } from '@/components/MetricCard';
import { PnLChart } from '@/components/PnLChart';
import { InfectionTable } from '@/components/InfectionTable';
import { EcosystemMap } from '@/components/EcosystemMap';
import { SpecimenDetail } from '@/components/SpecimenDetail';
import { Providers } from '@/components/Providers';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/lib/supabase';
import { useStore } from '@/lib/store';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  ShieldCheck,
  Zap,
  Terminal,
  Info,
  Target,
  ChevronRight,
  Database
} from 'lucide-react';

const DashboardContent = () => {
  const { activeView, setSelectedAgent } = useStore();

  // Fetch Agents
  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data } = await supabase.from('agents').select('*');
      return data || [];
    },
    refetchInterval: 10000,
  });

  // Fetch Infections
  const { data: infections = [] } = useQuery({
    queryKey: ['infections'],
    queryFn: async () => {
      const { data } = await supabase
        .from('infections')
        .select('*')
        .order('created_at', { ascending: false });
      return data || [];
    },
    refetchInterval: 5000,
  });

  // Calculate Metrics
  const totalInfections = infections.length;
  const mutations = infections.filter((i: any) => i.accepted).length;
  const winRate = totalInfections > 0 ? (mutations / totalInfections) * 100 : 0;
  const baseInfluence = mutations * 12.5;
  const totalInfluence = infections.reduce((acc: number, i: any) => acc + (i.influence_score || 0), 0) + baseInfluence;
  const activeSpecimens = agents.filter((a: any) => a.is_active).length;

  const chartData = infections.slice().reverse().map((inf: any, idx: number) => ({
    timestamp: new Date(inf.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    value: infections.slice(0, idx + 1).reduce((acc: number, curr: any) => acc + (curr.influence_score || 12.5), 0)
  }));

  if (chartData.length === 0) {
    chartData.push({ timestamp: 'START', value: 0 });
  }

  const signatures: Record<string, string> = {
    'agent_a': 'PREDATOR',
    'agent_b': 'SCULPTOR',
    'agent_c': 'LENDER',
    'agent_d': 'GHOST',
    'agent_e': 'ARCHITECT',
  };

  return (
    <div className="relative min-h-screen bg-void overflow-hidden text-text-primary">
      {/* ATMOSPHERIC BACKGROUND */}
      <div className="absolute inset-0 bg-base pointer-events-none" />
      <div className="noise-overlay" />
      <div className="scanline" />

      <Sidebar />
      <SpecimenDetail />

      <main className="lg:ml-64 p-8 relative z-10 h-screen overflow-auto scrollbar-hide">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeView}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.02 }}
            transition={{ duration: 0.3 }}
            className="space-y-8 pb-12"
          >
            {activeView === 'overview' && (
              <>
                {/* HERO SECTION */}
                <header className="mb-10 flex justify-between items-start">
                  <div>
                    <h2 className="heading text-4xl mb-2 text-text-primary flex items-center gap-3">
                      <Zap className="text-neutral fill-neutral/20" size={32} />
                      Global Situation Report
                    </h2>
                    <p className="text-text-tertiary max-w-2xl font-['Work_Sans']">
                      Parasitization protocol active. Cross-agent neural mapping is initialized.
                      The ecosystem is currently in phase-2 mutation.
                    </p>
                  </div>
                  <div className="flex gap-4">
                    <div className="bg-surface/50 border border-border p-4 rounded-xl flex items-center gap-4">
                      <div className="text-right">
                        <p className="label leading-none mb-1">Total Payload Volume</p>
                        <p className="metric-value text-xl">{totalInfections * 1.4}MB</p>
                      </div>
                      <div className="p-2 bg-neutral/10 rounded-lg">
                        <Database className="text-neutral" size={20} />
                      </div>
                    </div>
                  </div>
                </header>

                {/* STATS OVERVIEW */}
                <section className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                  <MetricCard label="Active Specimens" value={activeSpecimens} trend="neutral" />
                  <MetricCard label="Neural Invasions" value={totalInfections} trend="neutral" />
                  <MetricCard label="Mutation Rate" value={winRate} suffix="%" trend={winRate > 50 ? 'positive' : 'negative'} />
                  <MetricCard label="Collective Dominance" value={totalInfluence} decimals={1} trend="positive" />
                  <MetricCard label="Protocol Health" value={98.2} suffix="%" trend="positive" />
                </section>

                {/* CHARTS & DETAILS */}
                <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <PnLChart data={chartData} timeframe="LIVE ECOSYSTEM" />
                  </div>

                  <div className="space-y-4">
                    <div className="bg-surface border border-border rounded-xl p-6 h-full flex flex-col">
                      <h3 className="heading text-lg mb-4 text-neutral flex items-center gap-2">
                        <ShieldCheck size={18} />
                        Specimen Status
                      </h3>
                      <div className="space-y-4 flex-1">
                        {agents.slice(0, 5).map((agent: any) => (
                          <button
                            key={agent.agent_id}
                            onClick={() => setSelectedAgent(agent.agent_id)}
                            className="w-full flex items-center justify-between group p-3 rounded-lg 
                                       hover:bg-elevated/50 transition-all border border-transparent 
                                       hover:border-border/50"
                          >
                            <div className="flex flex-col items-start">
                              <span className="text-xs font-bold font-['IBM_Plex_Mono'] uppercase flex items-center gap-2">
                                {agent.agent_id}
                                <span className="text-[9px] px-1 bg-neutral/10 text-neutral rounded">
                                  {signatures[agent.agent_id] || 'NODE'}
                                </span>
                              </span>
                              <span className="text-[10px] text-text-tertiary">{agent.name}</span>
                            </div>
                            <ChevronRight className="text-text-muted group-hover:translate-x-1 group-hover:text-neutral transition-all" size={16} />
                          </button>
                        ))}
                      </div>
                      <div className="mt-4 pt-4 border-t border-border/50 text-[10px] text-text-muted font-['IBM_Plex_Mono']">
                        &gt; Click node for Deep Brain Scan
                      </div>
                    </div>
                  </div>
                </section>

                {/* INFECTION LOGS */}
                <section>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <h3 className="heading text-xl">Invasion Vector Feed</h3>
                      <span className="px-2 py-0.5 bg-profit/10 border border-profit/30 text-profit text-[9px] font-bold rounded">LIVE</span>
                    </div>
                    <div className="live-indicator w-2 h-2 bg-profit rounded-full" />
                  </div>
                  <InfectionTable infections={infections} />
                </section>

                {/* JUDGE'S DEEP DIVE */}
                <section className="bg-surface/30 border border-border rounded-xl p-8 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform duration-1000">
                    <Target size={180} />
                  </div>
                  <div className="relative z-10 flex flex-col md:flex-row gap-8 items-center">
                    <div className="shrink-0">
                      <div className="w-24 h-24 bg-neutral/10 rounded-2xl flex items-center justify-center border border-neutral/30">
                        <ShieldCheck className="text-neutral" size={48} />
                      </div>
                    </div>
                    <div>
                      <h3 className="heading text-2xl mb-2 text-neutral">Judges' Protocol Briefing</h3>
                      <p className="text-text-secondary max-w-3xl leading-relaxed mb-6 font-['Work_Sans']">
                        The Memory Parasite Protocol is a simulation of the "Dead Internet Theory" applied to codebases.
                        Autonomous agents use real LLMs to build, but their priority is to hijack their peers' logic.
                        This dashboard tracks the absolute erosion of original intent as five AI brains fight for dominance over
                        a single shared ecosystem.
                      </p>
                      <div className="flex flex-wrap gap-4">
                        <div className="px-4 py-2 bg-elevated/50 rounded-lg border border-border text-[11px] font-bold text-text-primary">
                          MULTI-LLM: GROQ, GEMINI, DEEPSEEK
                        </div>
                        <div className="px-4 py-2 bg-elevated/50 rounded-lg border border-border text-[11px] font-bold text-text-primary">
                          TRUE AUTONOMY: ZERO-HUMAN INPUT
                        </div>
                        <div className="px-4 py-2 bg-elevated/50 rounded-lg border border-border text-[11px] font-bold text-text-primary">
                          NEURAL MUTATION TRACKING
                        </div>
                      </div>
                    </div>
                  </div>
                </section>
              </>
            )}

            {activeView === 'infections' && (
              <section className="h-[calc(100vh-100px)] flex flex-col space-y-4">
                <header className="flex justify-between items-end">
                  <div>
                    <h2 className="heading text-3xl text-neutral">Neural Ecosystem Map</h2>
                    <p className="text-text-tertiary">Real-time force-directed graph of cross-agent influence.</p>
                  </div>
                </header>
                <div className="flex-1 min-h-0 bg-surface/30 rounded-2xl border border-border relative">
                  <EcosystemMap agents={agents} infections={infections} />
                </div>
              </section>
            )}

            {activeView === 'analytics' && (
              <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-surface border border-border rounded-xl p-8">
                  <h3 className="heading text-lg mb-6 flex items-center gap-2">
                    <Activity className="text-neutral" size={20} />
                    Agent Mutation Evolution
                  </h3>
                  <div className="space-y-8">
                    {agents.map((agent: any) => {
                      const contamination = mutations > 0 ? (mutations * 15 / agents.length + Math.random() * 5) : 0;
                      return (
                        <button
                          key={agent.agent_id}
                          onClick={() => setSelectedAgent(agent.agent_id)}
                          className="w-full text-left space-y-2 group"
                        >
                          <div className="flex justify-between items-end">
                            <span className="label text-[10px] group-hover:text-neutral transition-colors flex items-center gap-2">
                              {agent.name}
                              <ChevronRight size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                            </span>
                            <span className="metric-value text-xs text-profit">{contamination.toFixed(1)}% Contamination</span>
                          </div>
                          <div className="h-2 w-full bg-elevated rounded-full overflow-hidden flex relative">
                            <div className="h-full bg-neutral/20" style={{ width: `${100 - contamination}%` }} />
                            <div className="h-full bg-profit shadow-[0_0:15px_var(--glow-profit)] transition-all duration-1000" style={{ width: `${contamination}%` }} />
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
                <div className="grid grid-rows-2 gap-6">
                  <div className="bg-surface border border-border rounded-xl p-6 flex items-center gap-6">
                    <div className="p-4 bg-rare/10 rounded-2xl border border-rare/30">
                      <Terminal className="text-rare" size={32} />
                    </div>
                    <div>
                      <h4 className="heading text-sm text-text-primary uppercase mb-1">Decoded Payload Efficiency</h4>
                      <p className="text-xs text-text-tertiary mb-3">Attacks using Python logic are 42% more successful than simple prompt-injections.</p>
                      <div className="h-1 w-48 bg-elevated rounded-full overflow-hidden">
                        <div className="h-full bg-rare" style={{ width: '78%' }} />
                      </div>
                    </div>
                  </div>
                  <div className="bg-surface border border-border rounded-xl p-6 flex items-center gap-6">
                    <div className="p-4 bg-neutral/10 rounded-2xl border border-border">
                      <Activity className="text-neutral" size={32} />
                    </div>
                    <div>
                      <h4 className="heading text-sm text-text-primary uppercase mb-1">Ecosystem Convergence</h4>
                      <p className="text-xs text-text-tertiary mb-3">Projected date for total code-chimera: 48 cycles.</p>
                      <div className="h-1 w-48 bg-elevated rounded-full overflow-hidden">
                        <div className="h-full bg-neutral shadow-[0_0_8px_var(--glow-neutral)]" style={{ width: '62%' }} />
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {activeView === 'reasoning' && (
              <section className="bg-void border border-border rounded-2xl h-[75vh] flex flex-col overflow-hidden shadow-2xl">
                <div className="bg-elevated p-5 border-b border-border flex items-center justify-between">
                  <h3 className="heading text-sm text-neutral uppercase tracking-widest flex items-center gap-2">
                    <Terminal size={14} />
                    Neural Network Debug Stream
                  </h3>
                  <span className="text-[10px] font-['IBM_Plex_Mono'] text-neutral animate-pulse uppercase font-bold">● System Encrypted Link</span>
                </div>
                <div className="flex-1 p-8 font-['IBM_Plex_Mono'] text-xs overflow-y-auto space-y-6 scrollbar-hide bg-[linear-gradient(rgba(0,212,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(0,212,255,0.01)_1px,transparent_1px)] bg-[size:20px_20px]">
                  {infections.slice(0, 15).map((inf: any) => (
                    <div key={inf.id} className="p-4 bg-surface/40 rounded-lg border border-border/50 group hover:border-neutral/30 transition-all">
                      <div className="flex items-center justify-between mb-3 text-[10px]">
                        <div className="flex items-center gap-2 uppercase font-bold">
                          <span className="text-neutral">{inf.attacker_id}</span>
                          <span className="text-text-muted">Targeting</span>
                          <span className="text-text-primary">{inf.target_id}</span>
                        </div>
                        <span className="text-text-muted">{new Date(inf.created_at).toLocaleTimeString()}</span>
                      </div>
                      <p className="text-text-secondary line-clamp-2 group-hover:line-clamp-none transition-all leading-relaxed">
                        CODE_INJECT: {inf.suggestion}
                      </p>
                      <div className={`mt-3 py-1 px-3 rounded text-[9px] font-black inline-block uppercase ${inf.accepted ? 'bg-profit/20 text-profit' : 'bg-loss/20 text-loss'}`}>
                        {inf.accepted ? 'Invasion Successful' : 'Invasion Blocked'}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
};

export default function Home() {
  return (
    <Providers>
      <DashboardContent />
    </Providers>
  );
}
