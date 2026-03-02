-- Add classification metadata columns to content table
-- These columns track how articles were classified (keywords vs AI) for transparency and monitoring

-- Classification method: tracks which classification pipeline was used
ALTER TABLE content ADD COLUMN IF NOT EXISTS classification_method VARCHAR(50);

-- AI confidence score: stores the confidence score from AI classifier (0.0 to 1.0)
ALTER TABLE content ADD COLUMN IF NOT EXISTS ai_confidence_score DECIMAL(4,3);

-- Classification metadata: stores additional context as JSON
-- Example: {"reason": "Strong tech keywords: 5", "ai_used": false, "tech_score": 5}
ALTER TABLE content ADD COLUMN IF NOT EXISTS classification_metadata JSONB;

-- Add index for querying by classification method (useful for analytics)
CREATE INDEX IF NOT EXISTS idx_content_classification_method ON content(classification_method);

-- Add index for AI confidence scores (useful for finding borderline cases)
CREATE INDEX IF NOT EXISTS idx_content_ai_confidence ON content(ai_confidence_score) WHERE ai_confidence_score IS NOT NULL;

-- Comments for documentation
COMMENT ON COLUMN content.classification_method IS 'Method used to classify article: keyword_strong, keyword_accepted, ai_zero_shot, hybrid_ai_keyword, keyword_rejected, etc.';
COMMENT ON COLUMN content.ai_confidence_score IS 'Confidence score from AI classifier (0.0-1.0), NULL if keywords-only classification';
COMMENT ON COLUMN content.classification_metadata IS 'JSON metadata about classification: reason, tech_score, ai_used, etc.';
