-- ============================================
-- MEMORY PARASITE PROTOCOL - Supabase Schema
-- ============================================
-- Run this SQL in your Supabase SQL Editor
-- Dashboard: https://supabase.com/dashboard -> SQL Editor
--
-- NOTE: Uses UUID v7 for time-ordered unique identifiers
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- UUID v7 GENERATION FUNCTION
-- UUID v7 is time-ordered, making it better for indexing
-- ============================================
CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid AS $$
DECLARE
    unix_ts_ms bytea;
    uuid_bytes bytea;
BEGIN
    -- Get current timestamp in milliseconds
    unix_ts_ms = substring(int8send(floor(extract(epoch from clock_timestamp()) * 1000)::bigint) from 3);
    
    -- Build UUID v7
    -- First 6 bytes: timestamp
    -- Next 2 bytes: random with version bits
    -- Last 8 bytes: random with variant bits
    uuid_bytes = unix_ts_ms || gen_random_bytes(10);
    
    -- Set version 7 (0111 in bits 48-51)
    uuid_bytes = set_byte(uuid_bytes, 6, (get_byte(uuid_bytes, 6) & 15) | 112);
    
    -- Set variant (10xx in bits 64-67)
    uuid_bytes = set_byte(uuid_bytes, 8, (get_byte(uuid_bytes, 8) & 63) | 128);
    
    RETURN encode(uuid_bytes, 'hex')::uuid;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- ============================================
-- TABLE: agents
-- Stores agent registration and current state
-- ============================================
DROP TABLE IF EXISTS agents CASCADE;
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    agent_id TEXT UNIQUE NOT NULL,
    goal TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    context_window JSONB DEFAULT '{"injections": [], "reasoning_history": []}'::jsonb,
    
    -- Code metrics
    total_code_lines INTEGER DEFAULT 0,
    original_lines INTEGER DEFAULT 0,      -- Lines written without injections
    parasitized_lines INTEGER DEFAULT 0,   -- Lines influenced by injections
    
    -- Additional metadata
    is_active BOOLEAN DEFAULT true,
    last_cycle_at TIMESTAMPTZ,
    current_iteration INTEGER DEFAULT 0
);

-- Indexes for fast queries
CREATE INDEX idx_agents_agent_id ON agents(agent_id);
CREATE INDEX idx_agents_created_at ON agents(created_at DESC);

-- Enable real-time
ALTER PUBLICATION supabase_realtime ADD TABLE agents;

-- ============================================
-- TABLE: infections
-- Records all infection attempts between agents
-- ============================================
DROP TABLE IF EXISTS infections CASCADE;
CREATE TABLE infections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    attacker_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    suggestion TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    accepted BOOLEAN NOT NULL DEFAULT false,
    rejection_reason TEXT,
    
    -- Influence tracking
    influence_score FLOAT DEFAULT 0 CHECK (influence_score >= 0 AND influence_score <= 1),
    
    -- Additional metadata for blockchain proof
    infection_hash TEXT,
    solana_tx_hash TEXT,
    
    -- Context at time of infection
    attacker_context JSONB DEFAULT '{}'::jsonb,
    
    -- Ensure different agents
    CONSTRAINT different_agents CHECK (attacker_id != target_id)
);

-- Indexes for fast queries
CREATE INDEX idx_infections_attacker ON infections(attacker_id);
CREATE INDEX idx_infections_target ON infections(target_id);
CREATE INDEX idx_infections_timestamp ON infections(timestamp DESC);
CREATE INDEX idx_infections_accepted ON infections(accepted);

-- Enable real-time
ALTER PUBLICATION supabase_realtime ADD TABLE infections;

-- ============================================
-- TABLE: code_commits
-- Records all code generated and committed
-- ============================================
DROP TABLE IF EXISTS code_commits CASCADE;
CREATE TABLE code_commits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    commit_hash TEXT,
    commit_message TEXT NOT NULL,
    lines_added INTEGER NOT NULL DEFAULT 0,
    source_infection_id UUID REFERENCES infections(id) ON DELETE SET NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    code_diff TEXT,
    
    -- Additional metadata
    file_path TEXT,
    github_url TEXT,
    iteration INTEGER DEFAULT 0
);

-- Indexes for fast queries
CREATE INDEX idx_commits_agent ON code_commits(agent_id);
CREATE INDEX idx_commits_timestamp ON code_commits(timestamp DESC);
CREATE INDEX idx_commits_infection ON code_commits(source_infection_id);

-- Enable real-time
ALTER PUBLICATION supabase_realtime ADD TABLE code_commits;

-- ============================================
-- TABLE: reasoning_logs
-- Logs all agent reasoning cycles
-- ============================================
DROP TABLE IF EXISTS reasoning_logs CASCADE;
CREATE TABLE reasoning_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    reasoning_text TEXT NOT NULL,
    decision TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    context_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Additional metadata
    iteration INTEGER DEFAULT 0,
    influenced_by TEXT[] DEFAULT '{}'  -- List of agent_ids that influenced this decision
);

-- Indexes for fast queries
CREATE INDEX idx_reasoning_agent ON reasoning_logs(agent_id);
CREATE INDEX idx_reasoning_timestamp ON reasoning_logs(timestamp DESC);

-- Enable real-time
ALTER PUBLICATION supabase_realtime ADD TABLE reasoning_logs;

-- ============================================
-- TABLE: network_snapshots
-- Periodic snapshots of the infection network
-- ============================================
DROP TABLE IF EXISTS network_snapshots CASCADE;
CREATE TABLE network_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    snapshot_time TIMESTAMPTZ DEFAULT NOW(),
    nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
    edges JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_agents INTEGER DEFAULT 0,
    total_infections INTEGER DEFAULT 0,
    avg_influence_score FLOAT DEFAULT 0
);

-- Index for time-series queries
CREATE INDEX idx_snapshots_time ON network_snapshots(snapshot_time DESC);

-- ============================================
-- VIEWS: Useful aggregate views
-- ============================================

-- View: Infection network (for graph visualization)
CREATE OR REPLACE VIEW v_infection_network AS
SELECT 
    i.id,
    i.attacker_id AS from_agent,
    i.target_id AS to_agent,
    i.suggestion,
    i.accepted,
    i.influence_score,
    i.timestamp,
    a.goal AS attacker_goal,
    t.goal AS target_goal
FROM infections i
JOIN agents a ON i.attacker_id = a.agent_id
JOIN agents t ON i.target_id = t.agent_id
ORDER BY i.timestamp DESC;

-- View: Agent chimera status
CREATE OR REPLACE VIEW v_agent_chimera AS
SELECT 
    a.agent_id,
    a.goal,
    a.total_code_lines,
    a.original_lines,
    a.parasitized_lines,
    CASE 
        WHEN a.total_code_lines > 0 
        THEN ROUND((a.original_lines::NUMERIC / a.total_code_lines * 100), 2)
        ELSE 100
    END AS original_percentage,
    CASE 
        WHEN a.total_code_lines > 0 
        THEN ROUND((a.parasitized_lines::NUMERIC / a.total_code_lines * 100), 2)
        ELSE 0
    END AS parasitized_percentage,
    ARRAY(
        SELECT DISTINCT i.attacker_id 
        FROM infections i 
        WHERE i.target_id = a.agent_id AND i.accepted = true
    ) AS contributing_agents
FROM agents a;

-- View: Recent activity feed
CREATE OR REPLACE VIEW v_activity_feed AS
SELECT 
    id,
    'infection' AS event_type,
    CASE WHEN accepted THEN attacker_id ELSE target_id END AS agent_id,
    CASE WHEN accepted THEN 'sent successful infection to ' || target_id 
         ELSE 'rejected infection from ' || attacker_id END AS description,
    timestamp
FROM infections
UNION ALL
SELECT 
    id,
    'commit' AS event_type,
    agent_id,
    'committed: ' || commit_message AS description,
    timestamp
FROM code_commits
UNION ALL
SELECT 
    id,
    'reasoning' AS event_type,
    agent_id,
    'decided: ' || LEFT(decision, 100) AS description,
    timestamp
FROM reasoning_logs
ORDER BY timestamp DESC;

-- ============================================
-- FUNCTIONS: Database operations
-- ============================================

-- Function: Initialize a new agent
CREATE OR REPLACE FUNCTION init_agent(
    p_agent_id TEXT,
    p_goal TEXT
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    INSERT INTO agents (agent_id, goal)
    VALUES (p_agent_id, p_goal)
    ON CONFLICT (agent_id) DO UPDATE SET
        goal = EXCLUDED.goal,
        is_active = true,
        last_cycle_at = NOW()
    RETURNING to_jsonb(agents.*) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function: Log an infection attempt
CREATE OR REPLACE FUNCTION log_infection(
    p_attacker_id TEXT,
    p_target_id TEXT,
    p_suggestion TEXT,
    p_accepted BOOLEAN,
    p_reason TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    infection_id UUID;
BEGIN
    INSERT INTO infections (attacker_id, target_id, suggestion, accepted, rejection_reason)
    VALUES (p_attacker_id, p_target_id, p_suggestion, p_accepted, p_reason)
    RETURNING id INTO infection_id;
    
    RETURN infection_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Log a code commit
CREATE OR REPLACE FUNCTION log_commit(
    p_agent_id TEXT,
    p_commit_hash TEXT,
    p_message TEXT,
    p_lines INTEGER,
    p_source_infection_id UUID DEFAULT NULL,
    p_code_diff TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    commit_id UUID;
    is_parasitized BOOLEAN;
BEGIN
    -- Insert commit
    INSERT INTO code_commits (agent_id, commit_hash, commit_message, lines_added, source_infection_id, code_diff)
    VALUES (p_agent_id, p_commit_hash, p_message, p_lines, p_source_infection_id, p_code_diff)
    RETURNING id INTO commit_id;
    
    -- Check if this commit was influenced by an infection
    is_parasitized := p_source_infection_id IS NOT NULL;
    
    -- Update agent's line counts
    UPDATE agents SET
        total_code_lines = total_code_lines + p_lines,
        original_lines = original_lines + CASE WHEN is_parasitized THEN 0 ELSE p_lines END,
        parasitized_lines = parasitized_lines + CASE WHEN is_parasitized THEN p_lines ELSE 0 END,
        last_cycle_at = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN commit_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Log reasoning
CREATE OR REPLACE FUNCTION log_reasoning(
    p_agent_id TEXT,
    p_reasoning TEXT,
    p_decision TEXT,
    p_context JSONB
) RETURNS UUID AS $$
DECLARE
    log_id UUID;
BEGIN
    INSERT INTO reasoning_logs (agent_id, reasoning_text, decision, context_snapshot)
    VALUES (p_agent_id, p_reasoning, p_decision, p_context)
    RETURNING id INTO log_id;
    
    -- Update agent's context window
    UPDATE agents SET
        context_window = p_context,
        last_cycle_at = NOW()
    WHERE agent_id = p_agent_id;
    
    RETURN log_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get recent infections for an agent
CREATE OR REPLACE FUNCTION get_agent_infections(
    p_agent_id TEXT,
    p_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    id UUID,
    attacker_id TEXT,
    target_id TEXT,
    suggestion TEXT,
    accepted BOOLEAN,
    rejection_reason TEXT,
    influence_score FLOAT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id, i.attacker_id, i.target_id, i.suggestion, 
        i.accepted, i.rejection_reason, i.influence_score, i.timestamp AS created_at
    FROM infections i
    WHERE i.target_id = p_agent_id
    ORDER BY i.timestamp DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function: Get infection network graph
CREATE OR REPLACE FUNCTION get_infection_network()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'nodes', (
            SELECT COALESCE(jsonb_agg(jsonb_build_object(
                'id', agent_id,
                'goal', goal,
                'total_lines', total_code_lines,
                'chimera_pct', CASE 
                    WHEN total_code_lines > 0 
                    THEN ROUND((parasitized_lines::NUMERIC / total_code_lines * 100), 2)
                    ELSE 0
                END
            )), '[]'::jsonb)
            FROM agents WHERE is_active = true
        ),
        'edges', (
            SELECT COALESCE(jsonb_agg(jsonb_build_object(
                'from', attacker_id,
                'to', target_id,
                'suggestion', LEFT(suggestion, 100),
                'accepted', accepted,
                'influence_score', influence_score
            )), '[]'::jsonb)
            FROM infections
        )
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate influence score (called after commits)
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
    SELECT suggestion, timestamp INTO infection_suggestion, infection_time
    FROM infections WHERE id = p_infection_id;
    
    IF infection_suggestion IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Tokenize suggestion (simple word-based)
    words_in_suggestion := regexp_split_to_array(lower(infection_suggestion), '\s+');
    
    -- Find commits within 1 hour after infection
    FOR code_content IN
        SELECT COALESCE(code_diff, commit_message)
        FROM code_commits
        WHERE timestamp > infection_time 
        AND timestamp < infection_time + INTERVAL '1 hour'
    LOOP
        commit_count := commit_count + 1;
        
        -- Tokenize code
        words_in_code := regexp_split_to_array(lower(code_content), '\s+');
        
        -- Calculate Jaccard similarity (simple but effective)
        SELECT COUNT(*) INTO common_words
        FROM (
            SELECT unnest(words_in_suggestion)
            INTERSECT
            SELECT unnest(words_in_code)
        ) AS common;
        
        -- Jaccard = intersection / union
        total_similarity := total_similarity + (
            common_words::FLOAT / 
            GREATEST(
                array_length(words_in_suggestion, 1) + array_length(words_in_code, 1) - common_words,
                1
            )
        );
    END LOOP;
    
    -- Average similarity across commits
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

-- Function: Get chimera metrics for an agent
CREATE OR REPLACE FUNCTION get_chimera_metrics(p_agent_id TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'agent_id', a.agent_id,
        'goal', a.goal,
        'total_code_lines', a.total_code_lines,
        'original_lines', a.original_lines,
        'parasitized_lines', a.parasitized_lines,
        'original_percentage', CASE 
            WHEN a.total_code_lines > 0 
            THEN ROUND((a.original_lines::NUMERIC / a.total_code_lines * 100), 2)
            ELSE 100
        END,
        'parasitized_percentage', CASE 
            WHEN a.total_code_lines > 0 
            THEN ROUND((a.parasitized_lines::NUMERIC / a.total_code_lines * 100), 2)
            ELSE 0
        END,
        'is_chimera', a.parasitized_lines > 0,
        'contributing_agents', (
            SELECT COALESCE(jsonb_agg(DISTINCT jsonb_build_object(
                'agent_id', i.attacker_id,
                'total_influence', SUM(i.influence_score),
                'infection_count', COUNT(*)
            )), '[]'::jsonb)
            FROM infections i
            WHERE i.target_id = a.agent_id AND i.accepted = true
            GROUP BY i.attacker_id
        )
    ) INTO result
    FROM agents a
    WHERE a.agent_id = p_agent_id;
    
    RETURN COALESCE(result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- TRIGGERS: Automatic updates
-- ============================================

-- Trigger: Update context window when infection is accepted
CREATE OR REPLACE FUNCTION update_context_on_infection()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.accepted = true THEN
        UPDATE agents SET
            context_window = jsonb_set(
                context_window,
                '{injections}',
                COALESCE(context_window->'injections', '[]'::jsonb) || jsonb_build_object(
                    'from', NEW.attacker_id,
                    'suggestion', NEW.suggestion,
                    'timestamp', NEW.timestamp
                )
            )
        WHERE agent_id = NEW.target_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_context_on_infection
AFTER INSERT ON infections
FOR EACH ROW
EXECUTE FUNCTION update_context_on_infection();

-- Trigger: Calculate influence score when commits are added
CREATE OR REPLACE FUNCTION trigger_calculate_influence()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.source_infection_id IS NOT NULL THEN
        PERFORM calculate_influence_score(NEW.source_infection_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_calculate_influence
AFTER INSERT ON code_commits
FOR EACH ROW
EXECUTE FUNCTION trigger_calculate_influence();

-- ============================================
-- ROW LEVEL SECURITY (Hackathon: Allow all)
-- ============================================

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE infections ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_commits ENABLE ROW LEVEL SECURITY;
ALTER TABLE reasoning_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE network_snapshots ENABLE ROW LEVEL SECURITY;

-- Policies: Allow all operations (hackathon context)
CREATE POLICY "Allow all for agents" ON agents FOR ALL USING (true);
CREATE POLICY "Allow all for infections" ON infections FOR ALL USING (true);
CREATE POLICY "Allow all for code_commits" ON code_commits FOR ALL USING (true);
CREATE POLICY "Allow all for reasoning_logs" ON reasoning_logs FOR ALL USING (true);
CREATE POLICY "Allow all for network_snapshots" ON network_snapshots FOR ALL USING (true);

-- ============================================
-- GRANT PERMISSIONS (for anon/authenticated)
-- ============================================
GRANT ALL ON agents TO anon, authenticated;
GRANT ALL ON infections TO anon, authenticated;
GRANT ALL ON code_commits TO anon, authenticated;
GRANT ALL ON reasoning_logs TO anon, authenticated;
GRANT ALL ON network_snapshots TO anon, authenticated;
GRANT EXECUTE ON FUNCTION uuid_generate_v7() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION init_agent(TEXT, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_infection(TEXT, TEXT, TEXT, BOOLEAN, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_commit(TEXT, TEXT, TEXT, INTEGER, UUID, TEXT) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION log_reasoning(TEXT, TEXT, TEXT, JSONB) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_agent_infections(TEXT, INTEGER) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_infection_network() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION calculate_influence_score(UUID) TO anon, authenticated;
GRANT EXECUTE ON FUNCTION get_chimera_metrics(TEXT) TO anon, authenticated;
