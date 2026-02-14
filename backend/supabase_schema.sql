-- ============================================
-- AI Voice Orchestration System - Supabase Schema
-- ============================================
-- Run this SQL in Supabase SQL Editor to create all necessary tables
-- This schema mirrors the Django models for compatibility

-- ============================================
-- 1. Enable UUID Extension
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 2. User Authentication Table
-- ============================================
-- Django uses auth_user table - we'll create a compatible version
CREATE TABLE IF NOT EXISTS auth_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) UNIQUE NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for faster username lookups
CREATE INDEX IF NOT EXISTS auth_user_username_idx ON auth_user(username);
CREATE INDEX IF NOT EXISTS auth_user_email_idx ON auth_user(email);

-- ============================================
-- 3. Agent Configuration Table
-- ============================================
CREATE TABLE IF NOT EXISTS agents_agentconfiguration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    system_prompt TEXT NOT NULL,
    conversation_model VARCHAR(50) NOT NULL DEFAULT 'llama3.2:1b',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Index for faster user-specific queries
CREATE INDEX IF NOT EXISTS agents_agentconfig_user_id_idx ON agents_agentconfiguration(user_id);
CREATE INDEX IF NOT EXISTS agents_agentconfig_created_at_idx ON agents_agentconfiguration(created_at DESC);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_agents_agentconfiguration_updated_at 
    BEFORE UPDATE ON agents_agentconfiguration 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. Conversation Session Table
-- ============================================
CREATE TABLE IF NOT EXISTS agents_conversationsession (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents_agentconfiguration(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    total_turns INTEGER NOT NULL DEFAULT 0,
    average_latency_ms INTEGER,
    CONSTRAINT valid_status CHECK (status IN ('active', 'ended', 'error'))
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS agents_session_user_id_idx ON agents_conversationsession(user_id);
CREATE INDEX IF NOT EXISTS agents_session_agent_id_idx ON agents_conversationsession(agent_id);
CREATE INDEX IF NOT EXISTS agents_session_status_idx ON agents_conversationsession(status);
CREATE INDEX IF NOT EXISTS agents_session_started_at_idx ON agents_conversationsession(started_at DESC);

-- ============================================
-- 5. Conversation Log Table
-- ============================================
CREATE TABLE IF NOT EXISTS agents_conversationlog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES agents_conversationsession(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    speaker VARCHAR(10) NOT NULL,
    transcript TEXT NOT NULL,
    intent VARCHAR(100),
    latency_ms INTEGER,
    CONSTRAINT valid_speaker CHECK (speaker IN ('user', 'agent'))
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS agents_log_session_id_idx ON agents_conversationlog(session_id);
CREATE INDEX IF NOT EXISTS agents_log_timestamp_idx ON agents_conversationlog(timestamp);

-- ============================================
-- 6. Row Level Security (RLS) Policies
-- ============================================
-- Enable RLS on all tables for user isolation

-- Enable RLS
ALTER TABLE agents_agentconfiguration ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents_conversationsession ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents_conversationlog ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own agents
CREATE POLICY agents_user_isolation ON agents_agentconfiguration
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::INTEGER);

-- Policy: Users can only see their own sessions
CREATE POLICY sessions_user_isolation ON agents_conversationsession
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::INTEGER);

-- Policy: Users can only see logs from their own sessions
CREATE POLICY logs_user_isolation ON agents_conversationlog
    FOR ALL
    USING (
        session_id IN (
            SELECT id FROM agents_conversationsession 
            WHERE user_id = current_setting('app.current_user_id')::INTEGER
        )
    );

-- ============================================
-- 7. Useful Views for Analytics
-- ============================================

-- View: User Statistics
CREATE OR REPLACE VIEW user_statistics AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    COUNT(DISTINCT a.id) as total_agents,
    COUNT(DISTINCT s.id) as total_sessions,
    COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.id END) as active_sessions,
    MAX(s.started_at) as last_session_date
FROM auth_user u
LEFT JOIN agents_agentconfiguration a ON u.id = a.user_id
LEFT JOIN agents_conversationsession s ON u.id = s.user_id
GROUP BY u.id, u.username, u.email;

-- View: Agent Performance
CREATE OR REPLACE VIEW agent_performance AS
SELECT 
    a.id as agent_id,
    a.name as agent_name,
    a.user_id,
    u.username,
    COUNT(s.id) as total_sessions,
    AVG(s.total_turns) as avg_turns_per_session,
    AVG(s.average_latency_ms) as avg_latency_ms,
    MAX(s.started_at) as last_used
FROM agents_agentconfiguration a
LEFT JOIN agents_conversationsession s ON a.id = s.agent_id
LEFT JOIN auth_user u ON a.user_id = u.id
GROUP BY a.id, a.name, a.user_id, u.username;

-- ============================================
-- 8. Sample Data (Optional - for testing)
-- ============================================

-- Uncomment below to insert sample test user
/*
INSERT INTO auth_user (username, email, password, is_superuser, is_staff, is_active)
VALUES (
    'testuser',
    'test@example.com',
    'pbkdf2_sha256$600000$testsalt$testhash', -- This is not a real password
    FALSE,
    FALSE,
    TRUE
) ON CONFLICT (username) DO NOTHING;
*/

-- ============================================
-- 9. Utility Functions
-- ============================================

-- Function to get agent count for a user
CREATE OR REPLACE FUNCTION get_user_agent_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM agents_agentconfiguration WHERE user_id = p_user_id);
END;
$$ LANGUAGE plpgsql;

-- Function to get active sessions count
CREATE OR REPLACE FUNCTION get_active_sessions_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*) 
        FROM agents_conversationsession 
        WHERE user_id = p_user_id AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 10. Verification Queries
-- ============================================

-- Run these to verify tables were created successfully
/*
-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;

-- Count records in each table
SELECT 'auth_user' as table_name, COUNT(*) as count FROM auth_user
UNION ALL
SELECT 'agents_agentconfiguration', COUNT(*) FROM agents_agentconfiguration
UNION ALL
SELECT 'agents_conversationsession', COUNT(*) FROM agents_conversationsession
UNION ALL
SELECT 'agents_conversationlog', COUNT(*) FROM agents_conversationlog;

-- Check indexes
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY tablename;
*/

-- ============================================
-- SETUP COMPLETE!
-- ============================================
-- Your Supabase database is now ready for the AI Voice Orchestration System
-- Next steps:
-- 1. Update backend/.env with your Supabase password
-- 2. Run: cd backend/django_app && python manage.py migrate
-- 3. Django will sync with these tables automatically
