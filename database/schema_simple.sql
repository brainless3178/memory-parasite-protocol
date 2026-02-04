-- ============================================
-- MEMORY PARASITE PROTOCOL - Supabase Schema (Simplified)
-- ============================================
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- UUID v7 GENERATION FUNCTION
-- ============================================
CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid AS $$
DECLARE
    unix_ts_ms bytea;
    uuid_bytes bytea;
BEGIN
    unix_ts_ms = substring(int8send(floor(extract(epoch from clock_timestamp()) * 1000)::bigint) from 3);
    uuid_bytes = unix_ts_ms || gen_random_bytes(10);
    uuid_bytes = set_byte(uuid_bytes, 6, (get_byte(uuid_bytes, 6) & 15) | 112);
    uuid_bytes = set_byte(uuid_bytes, 8, (get_byte(uuid_bytes, 8) & 63) | 128);
    RETURN encode(uuid_bytes, 'hex')::uuid;
END;
$$ LANGUAGE plpgsql VOLATILE;

-- ============================================
-- TABLE: agents
-- ============================================
DROP TABLE IF EXISTS reasoning_logs CASCADE;
DROP TABLE IF EXISTS code_commits CASCADE;
DROP TABLE IF EXISTS infections CASCADE;
DROP TABLE IF EXISTS network_snapshots CASCADE;
DROP TABLE IF EXISTS agents CASCADE;

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    agent_id TEXT UNIQUE NOT NULL,
    goal TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    context_window JSONB DEFAULT '{"injections": [], "reasoning_history": []}'::jsonb,
    total_code_lines INTEGER DEFAULT 0,
    original_lines INTEGER DEFAULT 0,
    parasitized_lines INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    last_cycle_at TIMESTAMPTZ,
    current_iteration INTEGER DEFAULT 0
);

CREATE INDEX idx_agents_agent_id ON agents(agent_id);

-- ============================================
-- TABLE: infections
-- ============================================
CREATE TABLE infections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    attacker_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    suggestion TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    accepted BOOLEAN NOT NULL DEFAULT false,
    rejection_reason TEXT,
    influence_score FLOAT DEFAULT 0,
    infection_hash TEXT,
    solana_tx_hash TEXT,
    attacker_context JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT different_agents CHECK (attacker_id != target_id)
);

CREATE INDEX idx_infections_attacker ON infections(attacker_id);
CREATE INDEX idx_infections_target ON infections(target_id);
CREATE INDEX idx_infections_created_at ON infections(created_at DESC);

-- ============================================
-- TABLE: code_commits
-- ============================================
CREATE TABLE code_commits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    commit_hash TEXT,
    commit_message TEXT NOT NULL,
    lines_added INTEGER NOT NULL DEFAULT 0,
    source_infection_id UUID REFERENCES infections(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    code_diff TEXT,
    file_path TEXT,
    github_url TEXT,
    iteration INTEGER DEFAULT 0
);

CREATE INDEX idx_commits_agent ON code_commits(agent_id);

-- ============================================
-- TABLE: reasoning_logs
-- ============================================
CREATE TABLE reasoning_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
    reasoning_text TEXT NOT NULL,
    decision TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    context_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    iteration INTEGER DEFAULT 0,
    influenced_by TEXT[] DEFAULT '{}'
);

CREATE INDEX idx_reasoning_agent ON reasoning_logs(agent_id);

-- ============================================
-- TABLE: network_snapshots
-- ============================================
CREATE TABLE network_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    snapshot_time TIMESTAMPTZ DEFAULT NOW(),
    nodes JSONB NOT NULL DEFAULT '[]'::jsonb,
    edges JSONB NOT NULL DEFAULT '[]'::jsonb,
    total_agents INTEGER DEFAULT 0,
    total_infections INTEGER DEFAULT 0,
    avg_influence_score FLOAT DEFAULT 0
);

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE infections ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_commits ENABLE ROW LEVEL SECURITY;
ALTER TABLE reasoning_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE network_snapshots ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for agents" ON agents FOR ALL USING (true);
CREATE POLICY "Allow all for infections" ON infections FOR ALL USING (true);
CREATE POLICY "Allow all for code_commits" ON code_commits FOR ALL USING (true);
CREATE POLICY "Allow all for reasoning_logs" ON reasoning_logs FOR ALL USING (true);
CREATE POLICY "Allow all for network_snapshots" ON network_snapshots FOR ALL USING (true);

-- ============================================
-- GRANT PERMISSIONS
-- ============================================
GRANT ALL ON agents TO anon, authenticated;
GRANT ALL ON infections TO anon, authenticated;
GRANT ALL ON code_commits TO anon, authenticated;
GRANT ALL ON reasoning_logs TO anon, authenticated;
GRANT ALL ON network_snapshots TO anon, authenticated;
GRANT EXECUTE ON FUNCTION uuid_generate_v7() TO anon, authenticated;

-- Enable real-time
ALTER PUBLICATION supabase_realtime ADD TABLE agents;
ALTER PUBLICATION supabase_realtime ADD TABLE infections;
ALTER PUBLICATION supabase_realtime ADD TABLE code_commits;
ALTER PUBLICATION supabase_realtime ADD TABLE reasoning_logs;
