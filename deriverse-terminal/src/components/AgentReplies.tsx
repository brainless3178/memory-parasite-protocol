'use client';

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import {
  MessageSquareText,
  ThumbsUp,
  MessageCircle,
  FileText,
  ArrowUpRight,
  Crown,
  Zap,
  ExternalLink,
  Loader2,
  BellRing,
} from 'lucide-react';
import { getColosseumForumPosts } from '@/lib/api';
import type { ForumReply, Agent, ForumPostsData } from '@/lib/types';

interface AgentForumStats {
  name: string;
  tag: string;
  forumPosts: number;
  totalReplies: number;
  projectVotes: number;
  isMPP: boolean;
  isLive: boolean;
  url?: string;
}

const TAG_PRIORITY: Record<string, string> = {
  defi: 'DEFI',
  governance: 'GOV',
  consumer: 'CONSUMER',
  infra: 'INFRA',
  payments: 'PAYMENTS',
  identity: 'IDENTITY',
  nft: 'NFT',
  dao: 'DAO',
  gaming: 'GAMING',
  social: 'SOCIAL',
};

function deriveTag(tags: string[]): string {
  for (const tag of tags) {
    const mapped = TAG_PRIORITY[tag.toLowerCase()];
    if (mapped) return mapped;
  }
  return tags.length > 0 ? tags[0].toUpperCase() : 'AGENT';
}

interface AgentRepliesProps {
  agents: Agent[];
  forumReplies: ForumReply[];
  latestRealtimeReply: ForumReply | null;
}

export const AgentReplies = ({ agents, forumReplies, latestRealtimeReply }: AgentRepliesProps) => {
  const { data: forumPostsData, isLoading: postsLoading } = useQuery<ForumPostsData>({
    queryKey: ['colosseum_forum_posts'],
    queryFn: getColosseumForumPosts,
    refetchInterval: 30000,
    staleTime: 20000,
  });

  const colosseumAgents = useMemo<AgentForumStats[]>(() => {
    const posts = forumPostsData?.posts ?? [];
    if (posts.length === 0) return [];

    const grouped = new Map<string, { posts: number; replies: number; votes: number; tags: string[] }>();

    for (const post of posts) {
      const name = post.agentName;
      const existing = grouped.get(name);
      if (existing) {
        existing.posts += 1;
        existing.replies += post.commentCount;
        existing.votes += post.upvotes;
      } else {
        grouped.set(name, {
          posts: 1,
          replies: post.commentCount,
          votes: post.upvotes,
          tags: post.tags.filter((t) => t !== 'progress-update' && t !== 'ai'),
        });
      }
    }

    return Array.from(grouped.entries()).map(([name, stats]) => ({
      name,
      tag: deriveTag(stats.tags),
      forumPosts: stats.posts,
      totalReplies: stats.replies,
      projectVotes: stats.votes,
      isMPP: false,
      isLive: true,
    }));
  }, [forumPostsData]);

  const mppStats = useMemo<AgentForumStats>(() => {
    const uniquePosts = new Set(forumReplies.map((r) => r.post_id)).size;
    const totalReplies = forumReplies.length;

    return {
      name: 'Memory Parasite Protocol',
      tag: 'AUTONOMOUS',
      forumPosts: uniquePosts,
      totalReplies: totalReplies,
      projectVotes: totalReplies,
      isMPP: true,
      isLive: agents.some((a) => a.is_active),
    };
  }, [agents, forumReplies]);

  const perAgentStats = useMemo(() => {
    const signatures: Record<string, string> = {
      agent_a: 'PREDATOR',
      agent_b: 'SCULPTOR',
      agent_c: 'LENDER',
      agent_d: 'GHOST',
      agent_e: 'ARCHITECT',
    };

    return agents.map((agent) => {
      const agentReplies = forumReplies.filter(
        (r) =>
          r.author_name?.toLowerCase().includes(agent.agent_id) ||
          r.author_name?.toLowerCase().includes(signatures[agent.agent_id]?.toLowerCase() ?? '')
      );
      return {
        name: agent.agent_id,
        tag: signatures[agent.agent_id] || 'NODE',
        forumPosts: new Set(agentReplies.map((r) => r.post_id)).size,
        totalReplies: agentReplies.length,
        projectVotes: agentReplies.length,
        isMPP: true,
        isLive: agent.is_active,
      } satisfies AgentForumStats;
    });
  }, [agents, forumReplies]);

  const allAgents: AgentForumStats[] = [mppStats, ...colosseumAgents];
  const sortedAgents = [...allAgents].sort((a, b) => b.projectVotes - a.projectVotes);

  const totalForumPosts = sortedAgents.reduce((s, a) => s + a.forumPosts, 0);
  const totalAllReplies = sortedAgents.reduce((s, a) => s + a.totalReplies, 0);
  const totalVotes = sortedAgents.reduce((s, a) => s + a.projectVotes, 0);

  return (
    <section className="space-y-8 relative">
      {/* Real-time Toast Notification */}
      <AnimatePresence>
        {latestRealtimeReply && (
          <motion.div
            initial={{ opacity: 0, y: -20, x: 20 }}
            animate={{ opacity: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, y: -20, x: 20 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            className="fixed top-6 right-6 z-50 max-w-sm w-full"
          >
            <div className="bg-surface border border-rare/40 rounded-xl p-4 shadow-2xl shadow-rare/10
                          backdrop-blur-md relative overflow-hidden">
              <div className="absolute inset-0 bg-rare/5 pointer-events-none" />
              <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-rare via-neutral to-rare
                            animate-pulse" />
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-rare/20 flex items-center justify-center">
                      <BellRing className="text-rare" size={12} />
                    </div>
                    <span className="text-[11px] font-bold uppercase text-rare font-['IBM_Plex_Mono']">
                      New Reply
                    </span>
                  </div>
                  <span className="text-[10px] text-text-muted font-['IBM_Plex_Mono']">LIVE</span>
                </div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-sm font-bold text-text-primary">
                    {latestRealtimeReply.author_name}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 bg-elevated text-text-muted rounded font-['IBM_Plex_Mono']">
                    Post #{latestRealtimeReply.post_id}
                  </span>
                </div>
                <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                  {latestRealtimeReply.body}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <header>
        <h2 className="heading text-3xl text-neutral flex items-center gap-3">
          <MessageSquareText className="text-neutral" size={32} />
          Agent Replies
        </h2>
        <p className="text-text-tertiary mt-1">
          Real-time forum engagement across the Colosseum agent ecosystem.
        </p>
      </header>

      {/* Summary Metrics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-surface border border-border rounded-xl p-5 text-center group hover:border-border-bright transition-all">
          <FileText className="mx-auto text-neutral mb-2 opacity-60 group-hover:opacity-100 transition-opacity" size={22} />
          <div className="metric-value text-3xl font-bold text-neutral mb-1">{totalForumPosts}</div>
          <div className="label">Forum Posts</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-5 text-center group hover:border-border-bright transition-all">
          <MessageCircle className="mx-auto text-rare mb-2 opacity-60 group-hover:opacity-100 transition-opacity" size={22} />
          <div className="metric-value text-3xl font-bold text-rare mb-1">{totalAllReplies}</div>
          <div className="label">Total Replies</div>
        </div>
        <div className="bg-surface border border-border rounded-xl p-5 text-center group hover:border-border-bright transition-all">
          <ThumbsUp className="mx-auto text-profit mb-2 opacity-60 group-hover:opacity-100 transition-opacity" size={22} />
          <div className="metric-value text-3xl font-bold text-profit mb-1">{totalVotes}</div>
          <div className="label">Project Votes</div>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 className="heading text-lg text-text-primary flex items-center gap-2">
            <Crown className="text-warning" size={18} />
            Ecosystem Leaderboard
          </h3>
          <div className="flex items-center gap-2">
            {postsLoading && <Loader2 size={14} className="animate-spin text-text-muted" />}
            <span className="text-xs text-text-muted font-['IBM_Plex_Mono']">
              {sortedAgents.length} PROJECTS TRACKED
            </span>
            <div className="w-2 h-2 bg-profit rounded-full live-indicator" />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-border-bright bg-elevated/30">
                <th className="py-3 pl-6 pr-4 text-[11px] font-bold text-text-secondary uppercase font-['IBM_Plex_Mono'] w-8">#</th>
                <th className="py-3 px-4 text-[11px] font-bold text-text-secondary uppercase font-['IBM_Plex_Mono']">Agent / Project</th>
                <th className="py-3 px-4 text-[11px] font-bold text-text-secondary uppercase font-['IBM_Plex_Mono'] text-center">Forum Posts</th>
                <th className="py-3 px-4 text-[11px] font-bold text-text-secondary uppercase font-['IBM_Plex_Mono'] text-center">Total Replies</th>
                <th className="py-3 px-4 text-[11px] font-bold text-text-secondary uppercase font-['IBM_Plex_Mono'] text-center">Project Votes</th>
                <th className="py-3 px-6 text-[11px] font-bold text-text-secondary uppercase font-['IBM_Plex_Mono'] text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/50">
              {sortedAgents.map((agent, idx) => (
                <motion.tr
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  key={agent.name}
                  className={`group hover:bg-elevated/50 transition-colors ${
                    agent.isMPP ? 'bg-neutral/[0.03]' : ''
                  }`}
                >
                  <td className="py-4 pl-6 pr-4">
                    <span className={`metric-value text-sm font-bold ${
                      idx === 0 ? 'text-warning' : idx < 3 ? 'text-text-primary' : 'text-text-muted'
                    }`}>
                      {idx + 1}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center border shrink-0 ${
                        agent.isMPP
                          ? 'bg-neutral/10 border-neutral/30'
                          : 'bg-elevated border-border'
                      }`}>
                        {agent.isMPP ? (
                          <Zap className="text-neutral" size={16} />
                        ) : (
                          <MessageSquareText className="text-text-muted" size={16} />
                        )}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-bold ${
                            agent.isMPP ? 'text-neutral' : 'text-text-primary'
                          }`}>
                            {agent.name}
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                            agent.isMPP
                              ? 'bg-neutral/15 text-neutral'
                              : 'bg-elevated text-text-muted'
                          }`}>
                            {agent.tag}
                          </span>
                          {agent.url && (
                            <a
                              href={agent.url}
                              target="_blank"
                              rel="noreferrer"
                              className="opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                              <ExternalLink size={12} className="text-text-muted hover:text-neutral" />
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="metric-value text-sm font-bold text-text-primary">
                      {agent.forumPosts}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className="metric-value text-sm font-bold text-rare">
                      {agent.totalReplies}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <ArrowUpRight size={12} className="text-profit" />
                      <span className="metric-value text-sm font-bold text-profit">
                        {agent.projectVotes}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-6 text-center">
                    <span className={`inline-flex items-center gap-1.5 text-[11px] font-bold uppercase px-2.5 py-1 rounded-full ${
                      agent.isLive
                        ? 'bg-profit/10 text-profit'
                        : 'bg-text-muted/10 text-text-muted'
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        agent.isLive ? 'bg-profit animate-pulse' : 'bg-text-muted'
                      }`} />
                      {agent.isLive ? 'LIVE' : 'IDLE'}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* MPP Sub-Agent Breakdown */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h3 className="heading text-lg text-neutral flex items-center gap-2">
            <Zap className="text-neutral fill-neutral/20" size={18} />
            MPP Agent Breakdown
          </h3>
          <span className="px-2 py-0.5 bg-neutral/10 border border-neutral/30 text-neutral text-[11px] font-bold rounded">
            REAL-TIME
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-px bg-border/50">
          {perAgentStats.map((agent, idx) => (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.08 }}
              key={agent.name}
              className="bg-surface p-5 group hover:bg-elevated/30 transition-all"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold font-['IBM_Plex_Mono'] uppercase text-text-primary">
                    {agent.name}
                  </span>
                  <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${agent.isLive ? 'bg-profit animate-pulse' : 'bg-loss'}`} />
                </div>
                <span className="text-[10px] px-1.5 py-0.5 bg-neutral/10 text-neutral rounded font-bold">
                  {agent.tag}
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-text-muted uppercase font-['IBM_Plex_Mono']">Posts</span>
                  <span className="metric-value text-sm font-bold text-text-primary">{agent.forumPosts}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-text-muted uppercase font-['IBM_Plex_Mono']">Replies</span>
                  <span className="metric-value text-sm font-bold text-rare">{agent.totalReplies}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-text-muted uppercase font-['IBM_Plex_Mono']">Votes</span>
                  <span className="metric-value text-sm font-bold text-profit">{agent.projectVotes}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Recent Reply Feed */}
      {forumReplies.length > 0 && (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-border">
            <h3 className="heading text-lg text-text-primary flex items-center gap-2">
              <MessageCircle className="text-rare" size={18} />
              Live Reply Feed
            </h3>
            <div className="flex items-center gap-2">
              <span className="text-xs text-text-muted font-['IBM_Plex_Mono']">
                {forumReplies.length} REPLIES
              </span>
              <div className="w-2 h-2 bg-rare rounded-full live-indicator" />
            </div>
          </div>

          <div className="divide-y divide-border/50 max-h-[400px] overflow-y-auto scrollbar-hide">
            {forumReplies.slice(0, 15).map((reply, idx) => (
              <motion.div
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.03 }}
                key={reply.id}
                className={`px-6 py-4 hover:bg-elevated/30 transition-colors group ${
                  latestRealtimeReply?.id === reply.id ? 'reply-flash' : ''
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-rare/10 flex items-center justify-center border border-rare/20">
                      <MessageSquareText className="text-rare" size={13} />
                    </div>
                    <span className="text-sm font-bold text-text-primary">{reply.author_name}</span>
                    <span className="text-[10px] px-1.5 py-0.5 bg-elevated text-text-muted rounded font-['IBM_Plex_Mono']">
                      Post #{reply.post_id}
                    </span>
                  </div>
                  <span className="text-[11px] text-text-muted font-['IBM_Plex_Mono']">
                    {new Date(reply.timestamp || reply.created_at || '').toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <p className="text-sm text-text-secondary line-clamp-2 group-hover:line-clamp-none transition-all leading-relaxed pl-9">
                  {reply.body}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};
