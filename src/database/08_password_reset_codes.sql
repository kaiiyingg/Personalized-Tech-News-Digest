-- Create password reset codes table
-- This table stores temporary verification codes sent via email for password resets
-- Codes should expire after a reasonable time (e.g., 15 minutes)

CREATE TABLE IF NOT EXISTS password_reset_codes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL DEFAULT (NOW() + INTERVAL '2 minutes'),
    used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient lookup
CREATE INDEX IF NOT EXISTS idx_password_reset_codes_user_code ON password_reset_codes(user_id, code);
CREATE INDEX IF NOT EXISTS idx_password_reset_codes_expires ON password_reset_codes(expires_at);

-- Ensure only one unused code per user (allows multiple used codes for history)
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_unused_code_per_user 
ON password_reset_codes(user_id) WHERE used = FALSE;

-- Clean up expired codes (can be run periodically)
-- DELETE FROM password_reset_codes WHERE expires_at < NOW() OR used = TRUE;