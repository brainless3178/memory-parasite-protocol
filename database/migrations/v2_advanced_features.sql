-- ============================================
-- MIGRATION: V2 Advanced Features
-- Adds support for Emergence, Safety, and Tournaments
-- ============================================

-- 1. Safety & Quarantine System
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS is_quarantined BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS quarantine_reason TEXT,
ADD COLUMN IF NOT EXISTS quarantine_timestamp TIMESTAMPTZ;

-- 2. Emergent Behavior Tracking
CREATE TABLE IF NOT EXISTS emergent_behaviors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),
    behavior_type TEXT NOT NULL, -- 'new_capability', 'pattern_shift', 'complexity_spike'
    description TEXT NOT NULL,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    severity_score INTEGER CHECK (severity_score >= 0 AND severity_score <= 100),
    evidence_data JSONB DEFAULT '{}'::jsonb, -- Snapshot of code or logic causing this
    blockchain_proof TEXT -- Hash/Tx of the emergence event on Solana
);

CREATE INDEX IF NOT EXISTS idx_emergence_agent ON emergent_behaviors(agent_id);
CREATE INDEX IF NOT EXISTS idx_emergence_severity ON emergent_behaviors(severity_score DESC);

-- 3. Collective Intelligence / Memory
CREATE TABLE IF NOT EXISTS collective_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    insight_type TEXT NOT NULL, -- 'pattern', 'optimization', 'threat'
    content TEXT NOT NULL,
    contributing_agents TEXT[], -- Array of agent_ids that contributed
    consensus_score FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    applied_count INTEGER DEFAULT 0
);

-- 4. Safety Events Log (Killswitch/Rollback audit trail)
CREATE TABLE IF NOT EXISTS safety_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v7(),
    event_type TEXT NOT NULL, -- 'quarantine', 'rollback', 'network_pause'
    target_id TEXT, -- agent_id or NULL for network-wide
    reason TEXT NOT NULL,
    executed_by TEXT DEFAULT 'system',
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    tx_hash TEXT -- Solana audit trail
);

-- Enable Realtime for new tables
ALTER PUBLICATION supabase_realtime ADD TABLE emergent_behaviors;
ALTER PUBLICATION supabase_realtime ADD TABLE collective_insights;
ALTER PUBLICATION supabase_realtime ADD TABLE safety_events;

-- Grant permissions
GRANT ALL ON emergent_behaviors TO anon, authenticated;
GRANT ALL ON collective_insights TO anon, authenticated;
GRANT ALL ON safety_events TO anon, authenticated;
