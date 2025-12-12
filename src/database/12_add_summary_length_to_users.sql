-- Add AI summary preferences columns to users table
-- Migration: 12_add_summary_preferences_to_users.sql

ALTER TABLE users 
ADD COLUMN summary_type VARCHAR(20) DEFAULT 'tldr' 
CHECK (summary_type IN ('tldr', 'key-points'));

ALTER TABLE users 
ADD COLUMN summary_length VARCHAR(10) DEFAULT 'short' 
CHECK (summary_length IN ('short', 'medium', 'long'));