import { useCallback, useEffect, useRef, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { supabase } from './supabase';
import type { ForumReply } from './types';

export function useRealtimeForumReplies() {
  const queryClient = useQueryClient();
  const [latestRealtimeReply, setLatestRealtimeReply] = useState<ForumReply | null>(null);
  const dismissTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flashReply = useCallback((reply: ForumReply) => {
    if (dismissTimer.current) clearTimeout(dismissTimer.current);
    setLatestRealtimeReply(reply);
    dismissTimer.current = setTimeout(() => setLatestRealtimeReply(null), 5000);
  }, []);

  const query = useQuery<ForumReply[]>({
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
    staleTime: 30000,
    refetchInterval: 60000,
  });

  useEffect(() => {
    const channel = supabase
      .channel('forum_replies_realtime')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'forum_replies' },
        (payload) => {
          const newReply = payload.new as ForumReply;
          queryClient.setQueryData<ForumReply[]>(['forum_replies'], (old) => {
            if (!old) return [newReply];
            if (old.some((r) => r.id === newReply.id)) return old;
            return [newReply, ...old];
          });
          flashReply(newReply);
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'reasoning_logs',
          filter: 'decision=eq.FORUM_REPLY',
        },
        () => {
          queryClient.invalidateQueries({ queryKey: ['forum_replies'] });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [queryClient, flashReply]);

  useEffect(() => {
    return () => {
      if (dismissTimer.current) clearTimeout(dismissTimer.current);
    };
  }, []);

  return { ...query, latestRealtimeReply };
}
