CREATE sources TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Foreign key referencing the 'id' column in the 'users' table & automatically deletes related records if the referenced user is removed.
    source_name VARCHAR(100) NOT NULL, -- Name of the source (e.g., title of the article or video)
    type VARCHAR(50) NOT NULL, -- Type of source (e.g., 'article', 'video', etc.)
    feed_url VARCHAR(255) UNIQUE NOT NULL, -- URL of the feed (e.g., RSS or Atom feed)
    last_fetched_at TIMESTAMP, -- Timestamp of the last time the source was fetched or updated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);