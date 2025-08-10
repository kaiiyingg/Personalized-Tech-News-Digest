-- Track the last time a global ingestion was performed
CREATE TABLE IF NOT EXISTS ingestion_metadata (
    id SERIAL PRIMARY KEY,
    last_ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert a single row if not exists (for singleton pattern)
INSERT INTO ingestion_metadata (last_ingested_at)
SELECT CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM ingestion_metadata);
