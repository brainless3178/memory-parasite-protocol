-- ============================================
-- MEMORY PARASITE PROTOCOL: SUPABASE SCHEMA FIX
-- Run this in the Supabase SQL Editor
-- ============================================

-- 1. ADD MISSING COLUMNS TO reasoning_logs
ALTER TABLE reasoning_logs 
ADD COLUMN IF NOT EXISTS analysis_phases_completed INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS reasoning_depth_score FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS decision_confidence FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS time_to_decision_ms INTEGER DEFAULT 0;

-- 2. CREATE RPC FUNCTIONS

-- 2a. init_agent: Initialize or update an agent
CREATE OR REPLACE FUNCTION init_agent(
    p_agent_id TEXT,
    p_goal TEXT
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    INSERT INTO agents (agent_id, goal, is_active, created_at, last_cycle_at)
    VALUES (p_agent_id, p_goal, true, NOW(), NOW())
    ON CONFLICT (agent_id) 
    DO UPDATE SET 
        goal = COALESCE(EXCLUDED.goal, agents.goal),
        is_active = true,
        last_cycle_at = NOW()
    RETURNING to_jsonb(agents.*) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- 2b. log_reasoning: Log a reasoning cycle
CREATE OR REPLACE FUNCTION log_reasoning(
    p_agent_id TEXT,
    p_reasoning TEXT,
    p_decision TEXT,
    p_context JSONB DEFAULT '{}'::JSONB
) RETURNS TEXT AS $$
DECLARE
    new_id UUID;
BEGIN
    INSERT INTO reasoning_logs (agent_id, reasoning_text, decision, context_snapshot, created_at)
    VALUES (p_agent_id, p_reasoning, p_decision, p_context, NOW())
    RETURNING id INTO new_id;
    
    RETURN new_id::TEXT;
END;
$$ LANGUAGE plpgsql;

-- 2c. log_infection: Log an infection attempt
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
    
    -- Insert infection
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

-- 2d. get_infection_network: Get network graph data
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

-- 2e. get_agent_infections: Get infections for a specific agent
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

-- 3. ENSURE AGENTS TABLE HAS CORRECT SCHEMA
ALTER TABLE agents
ADD COLUMN IF NOT EXISTS total_code_lines INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS parasitized_lines INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_cycle_at TIMESTAMPTZ DEFAULT NOW();

-- 4. UPDATE FOREIGN KEY CONSTRAINTS TO BE MORE LENIENT
-- Drop and recreate foreign keys with ON DELETE SET NULL
ALTER TABLE infections 
DROP CONSTRAINT IF EXISTS infections_attacker_id_fkey,
DROP CONSTRAINT IF EXISTS infections_target_id_fkey;

-- Re-add with CASCADE behavior
ALTER TABLE infections
ADD CONSTRAINT infections_attacker_id_fkey 
    FOREIGN KEY (attacker_id) REFERENCES agents(agent_id) ON DELETE SET NULL ON UPDATE CASCADE,
ADD CONSTRAINT infections_target_id_fkey 
    FOREIGN KEY (target_id) REFERENCES agents(agent_id) ON DELETE SET NULL ON UPDATE CASCADE;

-- 5. GRANT PERMISSIONS
GRANT EXECUTE ON FUNCTION init_agent TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_reasoning TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_infection TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_infection_network TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_agent_infections TO anon, authenticated;

-- ============================================
-- DONE! All RPC functions and schema fixes applied.
-- ============================================
