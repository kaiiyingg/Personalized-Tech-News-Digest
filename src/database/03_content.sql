CREATE TABLE IF NOT EXISTS content (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE, -- Foreign key referencing the 'id' column in the 'sources' table & automatically deletes related records if the referenced source is removed.
    title VARCHAR(255) NOT NULL, -- Title of the content (e.g., article title, video title)
    summary TEXT NOT NULL, -- summary of the content
    article_url VARCHAR(255) UNIQUE NOT NULL, -- URL of the content
    published_at TIMESTAMP DEFAULT NULL, -- Timestamp of when the content was published, can be NULL if not available
    topic VARCHAR(100) -- e.g., 'AI & Machine Learning', 'Startups & Funding', etc.
);