-- ============================================
-- FIX: RPC functions referencing 'timestamp' instead of 'created_at'
-- First drop existing functions to avoid conflicts, then recreate
-- Run this in Supabase SQL Editor
-- ============================================

-- Drop existing functions (with all possible signatures)
DROP FUNCTION IF EXISTS get_infection_network();
DROP FUNCTION IF EXISTS get_agent_infections(TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_agent_infections(TEXT);
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT, BOOLEAN, TEXT);
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT, BOOLEAN);
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT);

-- 1. Fix get_infection_network function
CREATE OR REPLACE FUNCTION get_infection_network()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'nodes', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'id', agent_id,
                'goal', goal,
                'total_lines', COALESCE(total_code_lines, 0),
                'parasitized_lines', COALESCE(parasitized_lines, 0),
                'chimera_pct', CASE 
                    WHEN COALESCE(total_code_lines, 0) > 0 
                    THEN ROUND((COALESCE(parasitized_lines, 0)::NUMERIC / total_code_lines * 100), 2)
                    ELSE 0
                END
            ))
            FROM agents
            WHERE is_active = true
        ), '[]'::JSONB),
        'edges', COALESCE((
            SELECT jsonb_agg(jsonb_build_object(
                'from', attacker_id,
                'to', target_id,
                'suggestion', LEFT(suggestion, 100),
                'accepted', accepted,
                'influence_score', COALESCE(influence_score, 0)
            ))
            FROM infections
            ORDER BY created_at DESC
            LIMIT 500
        ), '[]'::JSONB)
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 2. Fix get_agent_infections function
CREATE OR REPLACE FUNCTION get_agent_infections(
    p_agent_id TEXT,
    p_limit INTEGER DEFAULT 10
) RETURNS JSONB AS $$
BEGIN
    RETURN COALESCE((
        SELECT jsonb_agg(row_to_json(i.*)::JSONB)
        FROM (
            SELECT * FROM infections
            WHERE target_id = p_agent_id
            ORDER BY created_at DESC
            LIMIT p_limit
        ) i
    ), '[]'::JSONB);
END;
$$ LANGUAGE plpgsql;

-- 3. Fix log_infection function
CREATE OR REPLACE FUNCTION log_infection(
    p_attacker_id TEXT,
    p_target_id TEXT,
    p_suggestion TEXT,
    p_accepted BOOLEAN DEFAULT false,
    p_reason TEXT DEFAULT NULL
) RETURNS TEXT AS $$
DECLARE
    new_id UUID;
    inf_hash TEXT;
BEGIN
    -- Generate infection hash
    inf_hash := encode(sha256((p_attacker_id || ':' || p_target_id || ':' || p_suggestion || ':' || NOW()::TEXT)::BYTEA), 'hex');
    
    -- Ensure attacker exists
    INSERT INTO agents (agent_id, goal, is_active, created_at)
    VALUES (p_attacker_id, 'Autonomous agent', true, NOW())
    ON CONFLICT (agent_id) DO NOTHING;
    
    -- Ensure target exists  
    INSERT INTO agents (agent_id, goal, is_active, created_at)
    VALUES (p_target_id, 'Autonomous agent', true, NOW())
    ON CONFLICT (agent_id) DO NOTHING;
    
    -- Insert infection (using created_at, not timestamp)
    INSERT INTO infections (
        attacker_id, 
        target_id, 
        suggestion, 
        accepted, 
        rejection_reason, 
        infection_hash,
        created_at
    )
    VALUES (
        p_attacker_id, 
        p_target_id, 
        p_suggestion, 
        p_accepted, 
        p_reason, 
        inf_hash,
        NOW()
    )
    RETURNING id INTO new_id;
    
    RETURN new_id::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION get_infection_network TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_agent_infections TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_infection TO anon, authenticated;

-- ============================================
-- DONE! Run this in your Supabase SQL Editor:
-- https://supabase.com/dashboard -> SQL Editor
-- ============================================
