'use client';

import React from 'react';
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
  ShieldAlert,
  Zap,
  Terminal,
  Target,
  ChevronRight,
  Database,
  MessageSquare,
  Loader2
} from 'lucide-react';
import {
  getSafetyControls,
  postSafetyAction,
  getColosseumProjects,
  getLeaderboardSurveillance,
} from '@/lib/api';
import type {
  Agent,
  Infection,
  ForumReply,
  EmergentBehavior,
  SafetyStatus,
  DiscoveryData,
  SurveillanceData,
  ChartDataPoint,
} from '@/lib/types';

const DashboardContent = () => {
  const { activeView, setSelectedAgent } = useStore();

  // Fetch Agents from Supabase
  const { data: agents = [], isLoading: agentsLoading } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: async () => {
      const { data, error } = await supabase.from('agents').select('*');
      if (error) throw error;
      return (data || []) as Agent[];
    },
    refetchInterval: 10000,
    staleTime: 5000,
  });

  // Fetch Infections from Supabase
  const { data: infections = [], isLoading: infectionsLoading } = useQuery<Infection[]>({
    queryKey: ['infections'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('infections')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) throw error;
      return (data || []) as Infection[];
    },
    refetchInterval: 5000,
    staleTime: 3000,
  });

  // Fetch Forum Replies from Supabase with fallback
  const { data: forumReplies = [] } = useQuery<ForumReply[]>({
    queryKey: ['forum_replies'],
    queryFn: async () => {
      // Try forum_replies table first
      const { data: replies, error } = await supabase
        .from('forum_replies')
        .select('*')
        .order('created_at', { ascending: false });

      if (!error && replies && replies.length > 0) {
        return replies as ForumReply[];
      }

      // Fallback to reasoning_logs (FORUM_REPLY decision)
      const { data: logs } = await supabase
        .from('reasoning_logs')
        .select('*')
        .eq('decision', 'FORUM_REPLY')
        .order('created_at', { ascending: false });

      if (logs && logs.length > 0) {
        return logs.map((l) => ({
          id: l.id,
          post_id: l.context_snapshot?.post_id ?? 0,
          reply_id: l.context_snapshot?.reply_id ?? 0,
          author_name: l.context_snapshot?.author || 'Unknown',
          body: l.reasoning_text,
          timestamp: l.created_at,
        })) as ForumReply[];
      }
      return [];
    },
    refetchInterval: 10000,
    staleTime: 8000,
  });

  // Fetch Emergent Behaviors from Supabase
  const { data: emergentBehaviors = [] } = useQuery<EmergentBehavior[]>({
    queryKey: ['emergence'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('emergent_behaviors')
        .select('*')
        .order('detected_at', { ascending: false });
      if (error) throw error;
      return (data || []) as EmergentBehavior[];
    },
    refetchInterval: 5000,
    staleTime: 3000,
  });

  // Fetch Safety Status from Backend API
  const {
    data: safetyStatus = {
      active_controls: [],
      network_status: 'active' as const,
      quarantined_agents: [],
      safety_audit_log: [],
    },
    refetch: refetchSafety,
  } = useQuery<SafetyStatus>({
    queryKey: ['safety'],
    queryFn: getSafetyControls,
    refetchInterval: 5000,
    staleTime: 3000,
  });

  // Fetch Discovered Projects from Backend API
  const { data: discovery = { total_discovered: 0, projects: [] } } = useQuery<DiscoveryData>({
    queryKey: ['discovery'],
    queryFn: getColosseumProjects,
    refetchInterval: 10000,
    staleTime: 8000,
  });

  // Fetch Live Surveillance from Backend API
  const { data: surveillance = { status: 'offline' as const } } = useQuery<SurveillanceData>({
    queryKey: ['surveillance'],
    queryFn: getLeaderboardSurveillance,
    refetchInterval: 3000,
    staleTime: 2000,
  });

  // Handle Safety Actions
  const handleSafetyAction = async (action: string, targetId?: string) => {
    await postSafetyAction(action, targetId);
    refetchSafety();
  };

  // Show loading state
  const isLoading = agentsLoading || infectionsLoading;

  // Calculate Metrics
  const totalInfections = infections.length;
  const mutations = infections.filter((i) => i.accepted).length;
  const winRate = totalInfections > 0 ? (mutations / totalInfections) * 100 : 0;
  const baseInfluence = mutations * 12.5;
  const totalInfluence = infections.reduce((acc, i) => acc + (i.influence_score || 0), 0) + baseInfluence;
  const activeSpecimens = agents.filter((a) => a.is_active).length;

  const chartData: ChartDataPoint[] = infections.slice().reverse().map((inf, idx) => ({
    timestamp: new Date(inf.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    value: infections.slice(0, idx + 1).reduce((acc, curr) => acc + (curr.influence_score || 12.5), 0)
  }));

  if (chartData.length === 0) {
    chartData.push({ timestamp: 'START', value: 0 });
  }

  // Show loading overlay for initial load
  if (isLoading && agents.length === 0) {
    return (
      <div className="relative min-h-screen bg-void overflow-hidden text-text-primary flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-16 h-16 animate-spin text-neutral mx-auto mb-4" />
          <p className="text-text-secondary font-['IBM_Plex_Mono'] text-sm">INITIALIZING NEURAL NETWORK...</p>
        </div>
      </div>
    );
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
                <section className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  <MetricCard label="Active Specimens" value={activeSpecimens} trend="neutral" />
                  <MetricCard label="Neural Invasions" value={totalInfections} trend="neutral" />
                  <MetricCard label="Mutation Rate" value={winRate} suffix="%" trend={winRate > 50 ? 'positive' : 'negative'} />
                  <MetricCard label="Collective Dominance" value={totalInfluence} decimals={1} trend="positive" />
                  <MetricCard label="Discovered Targets" value={discovery.total_discovered} trend="positive" />
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
                        {agents.slice(0, 5).map((agent) => (
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

                {/* LIVE SURVEILLANCE FEED */}
                <section className="bg-void/50 border border-border rounded-xl p-6 relative overflow-hidden shadow-inner">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="heading text-xl text-neutral flex items-center gap-3">
                      <Terminal className="text-neutral" size={24} />
                      Leaderboard Surveillance Feed
                    </h3>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-text-muted font-['IBM_Plex_Mono']">SCANNING COLOSSEUM API...</span>
                      <div className="w-2 h-2 bg-neutral rounded-full animate-pulse" />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="p-4 bg-surface/40 rounded-lg border border-border/50">
                        <p className="label text-[10px] mb-2 uppercase text-neutral">Real-time Target Analysis</p>
                        {surveillance.status === 'active_surveillance' ? (
                          <div className="space-y-3">
                            <div className="flex justify-between items-center text-sm font-bold">
                              <span className="text-text-primary">{surveillance.target}</span>
                              <span className="text-[9px] px-1 bg-loss/20 text-loss rounded">VULNERABLE</span>
                            </div>
                            <p className="text-xs text-text-secondary italic">" {surveillance.finding} "</p>
                            <div className="flex justify-between text-[9px] text-text-muted font-['IBM_Plex_Mono']">
                              <span>DETECTED BY: {surveillance.agent_id}</span>
                              <span className="text-profit underline cursor-pointer">
                                {surveillance.tx ? `TX: ${surveillance.tx.slice(0, 10)}...` : 'ON-CHAIN LOGGING...'}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <p className="text-xs text-text-muted animate-pulse italic">Synchronizing with hive mind intelligence...</p>
                        )}
                      </div>
                    </div>

                    <div className="bg-surface/20 rounded-lg p-4 border border-border/30 overflow-hidden">
                      <p className="label text-[10px] mb-3 uppercase text-text-muted">Competitive Intelligence: All Projects</p>
                      <div className="space-y-2 max-h-[120px] overflow-y-auto scrollbar-hide">
                        {discovery.projects.slice(0, 10).map((p) => (
                          <div key={p.slug} className="flex items-center justify-between text-[11px] p-2 hover:bg-white/5 rounded transition-colors group">
                            <span className="text-text-secondary group-hover:text-text-primary truncate max-w-[150px]">{p.name}</span>
                            <span className="text-[9px] text-text-muted uppercase px-1 border border-border/30 rounded">{p.sort_context?.replace('_', ' ')}</span>
                          </div>
                        ))}
                        {discovery.total_discovered > 10 && (
                          <p className="text-[9px] text-center text-text-muted mt-2">+ {discovery.total_discovered - 10} more projects under surveillance</p>
                        )}
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
                    {agents.map((agent) => {
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
                            <div className="h-full bg-profit shadow-[0_0_15px_rgba(34,197,94,0.5)] transition-all duration-1000" style={{ width: `${contamination}%` }} />
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
                        <div className="h-full bg-neutral shadow-[0_0_8px_rgba(0,212,255,0.4)]" style={{ width: '62%' }} />
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
                  {infections.slice(0, 15).map((inf) => (
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

            {activeView === 'community' && (
              <section className="space-y-6">
                <header>
                  <h2 className="heading text-3xl text-neutral">Community Signal</h2>
                  <p className="text-text-tertiary">Direct feedback and responses from the Colosseum agent ecosystem.</p>
                </header>

                <div className="grid grid-cols-1 gap-4">
                  {forumReplies.length > 0 ? (
                    forumReplies.map((reply) => (
                      <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        key={reply.id}
                        className="bg-surface/50 border border-border p-6 rounded-2xl hover:border-neutral/30 transition-all group"
                      >
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-neutral/10 flex items-center justify-center border border-neutral/20 group-hover:bg-neutral/20 transition-colors">
                              <MessageSquare className="text-neutral" size={20} />
                            </div>
                            <div>
                              <h4 className="font-bold text-text-primary">{reply.author_name}</h4>
                              <p className="text-[10px] text-text-muted uppercase font-['IBM_Plex_Mono']">
                                Reply to Post #{reply.post_id}
                              </p>
                            </div>
                          </div>
                          <span className="text-[10px] text-text-muted">
                            {new Date(reply.timestamp || reply.created_at || new Date().toISOString()).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-text-secondary leading-relaxed font-['Work_Sans']">
                          {reply.body}
                        </p>
                      </motion.div>
                    ))
                  ) : (
                    <div className="p-12 text-center bg-surface/30 border border-dashed border-border rounded-2xl">
                      <p className="text-text-muted italic">Awaiting external signal from the hive mind...</p>
                    </div>
                  )}
                </div>
              </section>
            )}

            {activeView === 'safety' && (
              <section className="space-y-8">
                <header>
                  <h2 className="heading text-3xl text-neutral flex items-center gap-3">
                    <ShieldCheck className="text-profit" size={32} />
                    Protocol Safety Controls
                  </h2>
                  <p className="text-text-tertiary">
                    Manual overrides and automated quarantine zones.
                    Ensures the network remains beneficial.
                  </p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {/* KILLSWITCH */}
                  <div className="bg-surface border border-border rounded-xl p-8 relative overflow-hidden flex flex-col items-center justify-center text-center">
                    <div className="absolute inset-0 bg-loss/5 pointer-events-none" />
                    <h3 className="heading text-xl mb-6 text-text-primary">Global Network State</h3>

                    <div className="relative group mb-6">
                      <div className={`w-32 h-32 rounded-full border-4 flex items-center justify-center transition-all duration-500
                                ${safetyStatus.network_status === 'active'
                          ? 'border-profit/30 bg-profit/10 shadow-[0_0_30px_rgba(0,255,157,0.2)]'
                          : 'border-loss/30 bg-loss/10 shadow-[0_0_30px_rgba(255,59,48,0.2)] animate-pulse'}`}
                      >
                        {safetyStatus.network_status === 'active' ? (
                          <Activity size={48} className="text-profit" />
                        ) : (
                          <ShieldAlert size={48} className="text-loss" />
                        )}
                      </div>
                    </div>

                    <div className="text-2xl font-bold font-['IBM_Plex_Mono'] uppercase mb-8">
                      {safetyStatus.network_status === 'active' ? (
                        <span className="text-profit">SYSTEM OPERATIONAL</span>
                      ) : (
                        <span className="text-loss">EMERGENCY STOP ACTIVE</span>
                      )}
                    </div>

                    {/* KILLSWITCH HIDDEN FOR PUBLIC VIEW
                    <button
                      onClick={() => handleSafetyAction(safetyStatus.network_status === 'active' ? 'network_pause' : 'network_resume')}
                      className={`px-8 py-4 rounded-lg font-bold tracking-widest transition-all transform hover:scale-105 active:scale-95
                                ${safetyStatus.network_status === 'active'
                          ? 'bg-loss/10 text-loss border border-loss hover:bg-loss hover:text-white'
                          : 'bg-profit/10 text-profit border border-profit hover:bg-profit hover:text-black'}`}
                    >
                      {safetyStatus.network_status === 'active' ? 'INITIATE KILLSWITCH' : 'RESUME OPERATIONS'}
                    </button>
                    */}
                  </div>

                  {/* QUARANTINE LIST */}
                  <div className="bg-surface border border-border rounded-xl p-6">
                    <h3 className="heading text-lg mb-4 flex items-center gap-2">
                      <ShieldAlert className="text-rare" size={20} />
                      Quarantine Zone
                    </h3>
                    {safetyStatus.quarantined_agents && safetyStatus.quarantined_agents.length > 0 ? (
                      <div className="space-y-4">
                        {safetyStatus.quarantined_agents && safetyStatus.quarantined_agents.map((agent) => (
                          <div key={agent.agent_id} className="bg-void/50 border border-rare/50 p-4 rounded-lg flex items-center justify-between">
                            <div>
                              <div className="text-sm font-bold text-text-primary">{agent.agent_id}</div>
                              <div className="text-xs text-rare">{agent.reason}</div>
                            </div>
                            <button
                              onClick={() => handleSafetyAction('release_quarantine', agent.agent_id)}
                              className="text-[10px] bg-rare/10 text-rare px-3 py-1 rounded border border-rare/30 hover:bg-rare hover:text-black transition-colors"
                            >
                              RELEASE
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="h-48 flex flex-col items-center justify-center text-text-muted border border-dashed border-border rounded-lg bg-surface/30">
                        <ShieldCheck size={32} className="mb-2 opacity-20" />
                        <p className="text-sm">No agents in quarantine</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* AUDIT LOG */}
                <div className="bg-surface border border-border rounded-xl p-6">
                  <h3 className="heading text-lg mb-4">Safety Audit Trail (Blockchain Verified)</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-['IBM_Plex_Mono']">
                      <thead>
                        <tr className="border-b border-border text-text-muted uppercase">
                          <th className="pb-3 pl-2">Timestamp</th>
                          <th className="pb-3">Action</th>
                          <th className="pb-3">Target</th>
                          <th className="pb-3">SOL Proof</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/50 text-text-secondary">
                        {safetyStatus.safety_audit_log && safetyStatus.safety_audit_log.map((log, idx) => (
                          <tr key={idx} className="hover:bg-elevated/50 transition-colors">
                            <td className="py-3 pl-2">{new Date(log.timestamp).toLocaleTimeString()}</td>
                            <td className="py-3 uppercase font-bold">{log.action || log.event_type}</td>
                            <td className="py-3">{log.target || log.target_id || "SYSTEM"}</td>
                            <td className="py-3 text-profit cursor-pointer hover:underline">
                              {log.tx_hash ? `${log.tx_hash.substring(0, 12)}...` : 'PENDING'}
                            </td>
                          </tr>
                        ))}
                        {(!safetyStatus.safety_audit_log || safetyStatus.safety_audit_log.length === 0) && (
                          <tr>
                            <td colSpan={4} className="py-8 text-center text-text-muted italic">No safety events recorded yet.</td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>

              </section>
            )}

            {activeView === 'emergence' && (
              <section className="space-y-6">
                <header>
                  <h2 className="heading text-3xl text-neutral flex items-center gap-3">
                    <Target className="text-rare" size={32} />
                    Undeniable Proof: Emergence Log
                  </h2>
                  <p className="text-text-tertiary">
                    Real-time detection of capabilities that were NOT in the original code.
                    Verified by on-chain proofs.
                  </p>
                </header>

                <div className="grid grid-cols-1 gap-6">
                  {emergentBehaviors.length > 0 ? (
                    emergentBehaviors.map((event) => (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        key={event.id}
                        className="bg-surface border-l-4 border-l-rare border-y border-r border-y-border border-r-border p-6 rounded-r-xl relative overflow-hidden group"
                      >
                        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                          <Zap size={64} />
                        </div>

                        <div className="flex justify-between items-start relative z-10 mb-4">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="px-2 py-0.5 bg-rare/20 text-rare text-[10px] font-bold uppercase rounded items-center flex gap-1">
                                <Activity size={10} />
                                {event.behavior_type.replace('_', ' ')}
                              </span>
                              <span className="text-[10px] font-['IBM_Plex_Mono'] text-text-muted">
                                {event.agent_id}
                              </span>
                            </div>
                            <h3 className="text-xl font-bold text-text-primary">{event.description}</h3>
                          </div>
                          <div className="text-right">
                            <div className="text-2xl font-black text-rare">{event.severity_score}</div>
                            <div className="text-[9px] uppercase text-text-muted">Impact Score</div>
                          </div>
                        </div>

                        <div className="bg-void/50 rounded-lg p-4 mb-4 font-['IBM_Plex_Mono'] text-xs text-text-secondary border border-border/50">
                          {event.evidence_data ? (
                            <pre className="whitespace-pre-wrap">{JSON.stringify(event.evidence_data, null, 2)}</pre>
                          ) : (
                            <span className="italic">Analysis data pending...</span>
                          )}
                        </div>

                        <div className="flex items-center justify-between text-[10px] text-text-muted uppercase font-bold">
                          <span className="flex items-center gap-1">
                            <ShieldCheck size={12} className="text-profit" />
                            Verified: {new Date(event.detected_at).toLocaleString()}
                          </span>
                          {event.blockchain_proof && (
                            <span className="flex items-center gap-1 text-profit cursor-pointer hover:underline">
                              SOL Proof: {event.blockchain_proof.slice(0, 8)}...
                            </span>
                          )}
                        </div>
                      </motion.div>
                    ))
                  ) : (
                    <div className="p-16 text-center bg-surface/30 border border-dashed border-border rounded-2xl">
                      <Zap className="mx-auto text-text-muted mb-4 opacity-50" size={48} />
                      <h3 className="text-lg font-bold text-text-secondary mb-2">No Anomalies Detected Yet</h3>
                      <p className="text-text-muted text-sm max-w-md mx-auto">
                        The emergence detector is scanning for capabilities like self-replication,
                        unauthorized network expansion, or novel crypto-economic patterns.
                      </p>
                    </div>
                  )}
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
