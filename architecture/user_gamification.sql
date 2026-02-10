-- Gamification and Retention Schema (The Hook)

-- User Stats (HUD)
CREATE TABLE IF NOT EXISTS user_gamification_stats (
    user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, -- Matches users.id (Clerk ID)
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    last_activity_date DATE,
    total_xp INT DEFAULT 0,
    current_level INT DEFAULT 1,
    streak_freeze_count INT DEFAULT 0,
    last_freeze_use_date DATE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Event Log (Audit Trail & History)
CREATE TABLE IF NOT EXISTS gamification_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL, -- 'categorize', 'rule_create', 'inbox_zero', 'daily_bonus'
    xp_earned INT NOT NULL,
    metadata JSONB, -- store specific transaction_id, rule_id, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_gamification_events_user_id ON gamification_events(user_id);
CREATE INDEX IF NOT EXISTS idx_gamification_events_created_at ON gamification_events(created_at);
