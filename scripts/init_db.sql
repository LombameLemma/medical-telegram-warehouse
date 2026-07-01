-- Initialize database schemas
-- This script is run automatically by Docker on first startup

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA raw TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA staging TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA marts TO postgres;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a simple logging table (optional)
CREATE TABLE IF NOT EXISTS public.pipeline_logs (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255),
    status VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- Index on pipeline_logs
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_status ON public.pipeline_logs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_logs_started ON public.pipeline_logs(started_at);
