CREATE TABLE IF NOT EXISTS user_content_interactions (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Foreign key referencing the 'id' column in the 'users' table & automatically deletes related records if the referenced user is removed.
    content_id INTEGER NOT NULL REFERENCES content(id) ON DELETE CASCADE, -- Foreign key referencing the 'id' column in the 'content' table & automatically deletes related records if the referenced content is removed.
    is_read BOOLEAN DEFAULT FALSE, -- Automatically marked as read once user clicks the article title and opens it in new tab
    is_liked BOOLEAN DEFAULT FALSE, -- Will save article to favorites page once user likes it. 
    interaction_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Timestamp of the interaction
    PRIMARY KEY (user_id, content_id) -- Composite primary key to ensure unique interactions per user and content
);