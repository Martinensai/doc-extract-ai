-- schema.sql
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  title VARCHAR(512),
  metadata JSONB,
  content TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
