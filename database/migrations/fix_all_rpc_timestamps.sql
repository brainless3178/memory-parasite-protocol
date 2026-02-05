-- Comprehensive RPC Fix: Checked and Verified
-- 1. Alignment: Uses 'created_at' to match running DB (Fixes "column timestamp does not exist")
-- 2. Clean Drop: Drops old functions first to avoid "return type mismatch" errors
-- 3. Data Integrity: Maps all arguments (including cancellation reason) correctly

-- ==============================================================================
-- 1. FIX log_infection
-- ==============================================================================
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT, BOOLEAN, TEXT, JSONB);
DROP FUNCTION IF EXISTS log_infection(TEXT, TEXT, TEXT, BOOLEAN, TEXT); 

CREATE OR REPLACE FUNCTION log_infection(
    p_attacker_id TEXT,
    p_target_id TEXT,
    p_suggestion TEXT,
    p_accepted BOOLEAN,
    p_reason TEXT DEFAULT NULL,
    p_attacker_context JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_infection_id UUID;
BEGIN
    INSERT INTO infections (
        attacker_id, 
        target_id, 
        suggestion, 
        accepted, 
        rejection_reason, -- Mapped from p_reason
        created_at,       -- FIXED: Was 'timestamp'
        attacker_context
    )
    VALUES (
        p_attacker_id, 
        p_target_id, 
        p_suggestion, 
        p_accepted, 
        p_reason,         -- Mapped to rejection_reason
        NOW(),
        p_attacker_context
    )
    RETURNING id INTO v_infection_id;
    
    RETURN v_infection_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- ==============================================================================
-- 2. FIX log_commit
-- ==============================================================================
DROP FUNCTION IF EXISTS log_commit(TEXT, TEXT, TEXT, INTEGER, UUID, TEXT);

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
        created_at -- FIXED: Was 'timestamp'
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
    
    -- Update stats
    v_is_parasitized := p_source_infection_id IS NOT NULL;
    
    UPDATE agents SET
        total_code_lines = total_code_lines + p_lines,
        original_lines = original_lines + CASE WHEN v_is_parasitized THEN 0 ELSE p_lines END,
        parasitized_lines = parasitized_lines + CASE WHEN v_is_parasitized THEN p_lines ELSE 0 END,
        last_cycle_at = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN v_commit_id;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- ==============================================================================
-- 3. FIX log_reasoning
-- ==============================================================================
DROP FUNCTION IF EXISTS log_reasoning(TEXT, TEXT, TEXT, JSONB);

CREATE OR REPLACE FUNCTION log_reasoning(
    p_agent_id TEXT,
    p_reasoning TEXT,
    p_decision TEXT,
    p_context JSONB
) RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO reasoning_logs (
        agent_id, 
        reasoning_text, 
        decision, 
        context_snapshot,
        created_at -- FIXED: Was 'timestamp'
    )
    VALUES (
        p_agent_id, 
        p_reasoning, 
        p_decision, 
        p_context,
        NOW()
    )
    RETURNING id INTO v_log_id;
    
    -- Update agent context
    UPDATE agents SET
        context_window = p_context,
        last_cycle_at = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql VOLATILE;
