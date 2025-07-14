CREATE TABLE IF NOT EXISTS user_content_interactions (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Foreign key referencing the 'id' column in the 'users' table & automatically deletes related records if the referenced user is removed.
    content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE, -- Foreign key referencing the 'id' column in the 'content' table & automatically deletes related records if the referenced content is removed.
    is_read BOOLEAN DEFAULT FALSE, -- Indicates whether the content has been read by the user
    is_liked BOOLEAN DEFAULT FALSE, -- Indicates whether the content has been liked by the user (also means saved)
    interaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of the interaction
    PRIMARY KEY (user_id, content_id) -- Composite primary key to ensure unique interactions per user and content
);