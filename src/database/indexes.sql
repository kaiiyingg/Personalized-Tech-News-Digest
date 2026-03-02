-- Performance Optimization SQL Indexes for TechPulse
-- WHEN TO USE: Run these when deploying to production (Render) for better performance
-- FOR DEVELOPMENT: Optional - your app works fine without these
-- 
-- HOW TO APPLY: 
-- 1. Connect to your PostgreSQL database
-- 2. Run each CREATE INDEX command
-- 3. Indexes will build in background (CONCURRENTLY)
--
-- Run these in your database to improve query performance

-- Index for content table - most important for fast lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_published_topic 
ON content(published_at DESC, topic);

-- Index for user interactions - speeds up user-specific queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_content_interactions_user_content 
ON user_content_interactions(user_id, content_id);

-- Index for user topics - essential for topic filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_topics_user_id 
ON user_topics(user_id);

-- Index for content by source and date - helps with source filtering
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_content_source_date 
ON content(source_id, published_at DESC);



-- Index for liked articles - speeds up cleanup operations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_interactions_liked 
ON user_content_interactions(content_id) 
WHERE is_liked = true;
