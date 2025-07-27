-- Migration: Add image_url column to content table (Supabase/PostgreSQL)
-- This migration adds a column to store the image URL for each article.

ALTER TABLE content ADD COLUMN IF NOT EXISTS image_url TEXT;
