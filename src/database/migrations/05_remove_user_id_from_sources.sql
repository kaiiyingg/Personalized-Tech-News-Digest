-- Migration (Changing database structure/data without losing data): Remove user_id from sources table (Supabase/PostgreSQL)
-- This migration drops the user_id column from the sources table, making sources global.

ALTER TABLE sources DROP COLUMN IF EXISTS user_id;
