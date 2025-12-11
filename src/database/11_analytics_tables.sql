-- Analytics tables for trend tracking and AI briefing

-- Topic trends aggregation table
CREATE TABLE IF NOT EXISTS topic_trends (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    topic VARCHAR(100) NOT NULL,
    article_count INTEGER DEFAULT 0,
    view_count INTEGER DEFAULT 0,
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(date, topic)
);

-- Daily AI-generated briefings
CREATE TABLE IF NOT EXISTS daily_digests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    summary TEXT NOT NULL,
    article_ids INTEGER[] DEFAULT '{}',
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_topic_trends_date ON topic_trends(date DESC);
CREATE INDEX IF NOT EXISTS idx_topic_trends_topic ON topic_trends(topic);
CREATE INDEX IF NOT EXISTS idx_daily_digests_user ON daily_digests(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_digests_date ON daily_digests(date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_digests_sent ON daily_digests(sent_at);
