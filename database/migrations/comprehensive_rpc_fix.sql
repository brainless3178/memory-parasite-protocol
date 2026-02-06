-- ============================================
-- MEMORY PARASITE PROTOCOL: COMPREHENSIVE RPC FIX
-- ============================================
-- This migration:
-- 1. Drops ALL existing function signatures to avoid conflicts
-- 2. Recreates ALL RPC functions with correct column names (created_at not timestamp)
-- 3. Grants proper permissions
--
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard -> SQL Editor
-- ============================================

-- ============================================
-- STEP 1: DROP ALL EXISTING FUNCTIONS
-- ============================================

-- log_infection (all known signatures)
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT, BOOLEAN, TEXT, JSONB);
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT, BOOLEAN, TEXT);
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT, BOOLEAN);
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT);

-- log_commit (all known signatures)
DROP FUNCTION IF EXISTS log_commit(TEXT, TEXT, TEXT, INTEGER, UUID, TEXT);
DROP FUNCTION IF EXISTS log_commit(TEXT, TEXT, TEXT, INTEGER, UUID);
DROP FUNCTION IF EXISTS log_commit(TEXT, TEXT, TEXT, INTEGER);

-- log_reasoning (all known signatures)
DROP FUNCTION IF EXISTS log_reasoning(TEXT, TEXT, TEXT, JSONB);
DROP FUNCTION IF EXISTS log_reasoning(TEXT, TEXT, TEXT);

-- init_agent (all known signatures)
DROP FUNCTION IF EXISTS init_agent(TEXT, TEXT);

-- get_agent_infections (all known signatures)
DROP FUNCTION IF EXISTS get_agent_infections(TEXT, INTEGER);
DROP FUNCTION IF EXISTS get_agent_infections(TEXT);

-- get_infection_network
DROP FUNCTION IF EXISTS get_infection_network();

-- calculate_influence_score
DROP FUNCTION IF EXISTS calculate_influence_score(UUID);

-- get_chimera_metrics
DROP FUNCTION IF EXISTS get_chimera_metrics(TEXT);

-- update_agent_lines
DROP FUNCTION IF EXISTS update_agent_lines(TEXT, INTEGER, BOOLEAN);

-- ============================================
-- STEP 2: CREATE ALL RPC FUNCTIONS
-- ============================================

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

-- 2b. log_infection: Log an infection attempt
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
    
    -- Insert infection (using created_at)
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

-- 2c. log_commit: Log a code commit
CREATE OR REPLACE FUNCTION log_commit(
    p_agent_id TEXT,
    p_commit_hash TEXT,
    p_message TEXT,
    p_lines INTEGER,
    p_source_infection_id UUID DEFAULT NULL,
    p_code_diff TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_commit_id UUID;
    v_is_parasitized BOOLEAN;
BEGIN
    INSERT INTO code_commits (
        agent_id, 
        commit_hash, 
        commit_message, 
        lines_added, 
        source_infection_id, 
        code_diff,
        created_at
    )
    VALUES (
        p_agent_id, 
        p_commit_hash, 
        p_message, 
        p_lines, 
        p_source_infection_id, 
        p_code_diff,
        NOW()
    )
    RETURNING id INTO v_commit_id;
    
    -- Update agent stats
    v_is_parasitized := p_source_infection_id IS NOT NULL;
    
    UPDATE agents SET
        total_code_lines = COALESCE(total_code_lines, 0) + p_lines,
        original_lines = COALESCE(original_lines, 0) + CASE WHEN v_is_parasitized THEN 0 ELSE p_lines END,
        parasitized_lines = COALESCE(parasitized_lines, 0) + CASE WHEN v_is_parasitized THEN p_lines ELSE 0 END,
        last_cycle_at = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN v_commit_id;
END;
$$ LANGUAGE plpgsql;

-- 2d. log_reasoning: Log a reasoning cycle
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
    
    -- Update agent context
    UPDATE agents SET
        context_window = p_context,
        last_cycle_at = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN new_id::TEXT;
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

-- 2f. get_infection_network: Get network graph data
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

-- 2g. calculate_influence_score: Calculate influence score for an infection
CREATE OR REPLACE FUNCTION calculate_influence_score(p_infection_id UUID)
RETURNS FLOAT AS $$
DECLARE
    infection_suggestion TEXT;
    infection_time TIMESTAMPTZ;
    total_similarity FLOAT := 0;
    commit_count INTEGER := 0;
    code_content TEXT;
    words_in_suggestion TEXT[];
    words_in_code TEXT[];
    common_words INTEGER;
    score FLOAT;
BEGIN
    -- Get infection details
    SELECT suggestion, created_at INTO infection_suggestion, infection_time
    FROM infections WHERE id = p_infection_id;
    
    IF infection_suggestion IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Tokenize suggestion
    words_in_suggestion := regexp_split_to_array(lower(infection_suggestion), '\s+');
    
    -- Find commits within 1 hour after infection
    FOR code_content IN
        SELECT COALESCE(code_diff, commit_message)
        FROM code_commits
        WHERE created_at > infection_time 
        AND created_at < infection_time + INTERVAL '1 hour'
    LOOP
        commit_count := commit_count + 1;
        
        -- Tokenize code
        words_in_code := regexp_split_to_array(lower(code_content), '\s+');
        
        -- Calculate Jaccard similarity
        SELECT COUNT(*) INTO common_words
        FROM (
            SELECT unnest(words_in_suggestion)
            INTERSECT
            SELECT unnest(words_in_code)
        ) AS common;
        
        total_similarity := total_similarity + (
            common_words::FLOAT / 
            GREATEST(
                array_length(words_in_suggestion, 1) + array_length(words_in_code, 1) - common_words,
                1
            )
        );
    END LOOP;
    
    -- Average similarity
    IF commit_count > 0 THEN
        score := total_similarity / commit_count;
    ELSE
        score := 0;
    END IF;
    
    -- Update the infection record
    UPDATE infections SET influence_score = score WHERE id = p_infection_id;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- 2h. get_chimera_metrics: Get chimera metrics for an agent
CREATE OR REPLACE FUNCTION get_chimera_metrics(p_agent_id TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'agent_id', a.agent_id,
        'goal', a.goal,
        'total_code_lines', COALESCE(a.total_code_lines, 0),
        'original_lines', COALESCE(a.original_lines, 0),
        'parasitized_lines', COALESCE(a.parasitized_lines, 0),
        'original_percentage', CASE 
            WHEN COALESCE(a.total_code_lines, 0) > 0 
            THEN ROUND((COALESCE(a.original_lines, 0)::NUMERIC / a.total_code_lines * 100), 2)
            ELSE 100
        END,
        'parasitized_percentage', CASE 
            WHEN COALESCE(a.total_code_lines, 0) > 0 
            THEN ROUND((COALESCE(a.parasitized_lines, 0)::NUMERIC / a.total_code_lines * 100), 2)
            ELSE 0
        END,
        'is_chimera', COALESCE(a.parasitized_lines, 0) > 0,
        'contributing_agents', COALESCE((
            SELECT jsonb_agg(DISTINCT jsonb_build_object(
                'agent_id', i.attacker_id,
                'infection_count', COUNT(*)
            ))
            FROM infections i
            WHERE i.target_id = a.agent_id AND i.accepted = true
            GROUP BY i.attacker_id
        ), '[]'::JSONB)
    ) INTO result
    FROM agents a
    WHERE a.agent_id = p_agent_id;
    
    RETURN COALESCE(result, '{}'::JSONB);
END;
$$ LANGUAGE plpgsql;

-- 2i. update_agent_lines: Helper to update agent line counts
CREATE OR REPLACE FUNCTION update_agent_lines(
    p_agent_id TEXT,
    p_lines INTEGER,
    p_is_parasitized BOOLEAN
) RETURNS VOID AS $$
BEGIN
    UPDATE agents SET
        total_code_lines = COALESCE(total_code_lines, 0) + p_lines,
        original_lines = COALESCE(original_lines, 0) + CASE WHEN p_is_parasitized THEN 0 ELSE p_lines END,
        parasitized_lines = COALESCE(parasitized_lines, 0) + CASE WHEN p_is_parasitized THEN p_lines ELSE 0 END,
        last_cycle_at = NOW()
    WHERE agent_id = p_agent_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 3: GRANT PERMISSIONS
-- ============================================

GRANT EXECUTE ON FUNCTION init_agent(TEXT, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_infection(TEXT, TEXT, TEXT, BOOLEAN, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_commit(TEXT, TEXT, TEXT, INTEGER, UUID, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_reasoning(TEXT, TEXT, TEXT, JSONB) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_agent_infections(TEXT, INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_infection_network() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION calculate_influence_score(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_chimera_metrics(TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION update_agent_lines(TEXT, INTEGER, BOOLEAN) TO anon, authenticated;

-- ============================================
-- DONE! All RPC functions have been recreated.
-- ============================================
