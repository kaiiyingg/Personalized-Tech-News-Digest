-- Fix password reset codes constraint
-- Drop the problematic constraint and create the correct one

-- Drop the old constraint that prevents multiple used codes
ALTER TABLE password_reset_codes DROP CONSTRAINT IF EXISTS password_reset_codes_user_id_used_key;

-- Create the correct unique index that only prevents multiple unused codes
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_unused_code_per_user 
ON password_reset_codes(user_id) WHERE used = FALSE;

-- Clean up any existing duplicate used codes to prevent future issues
DELETE FROM password_reset_codes 
WHERE id NOT IN (
    SELECT MIN(id) 
    FROM password_reset_codes 
    WHERE used = TRUE 
    GROUP BY user_id, used
);