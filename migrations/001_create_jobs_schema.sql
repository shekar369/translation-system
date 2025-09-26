-- Migration: Create Job-based translation schema
-- Version: 001
-- Description: Add support for grouped course translation jobs

-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Glossaries table
CREATE TABLE glossaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    name TEXT NOT NULL,
    data JSONB NOT NULL DEFAULT '{}', -- {term: translation, ...}
    language_pair TEXT NOT NULL, -- e.g., "en-es"
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Jobs table - core entity for course translation projects
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code TEXT NOT NULL, -- e.g., CS101-2025
    title TEXT,
    client_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    -- Possible statuses: created, queued, parsing, transcribing, translating, postprocessing, review, completed, failed
    priority TEXT DEFAULT 'normal', -- normal, fast, immediate
    source_language TEXT DEFAULT 'auto',
    target_languages TEXT[] NOT NULL, -- array of language codes
    translation_style TEXT DEFAULT 'neutral', -- formal, neutral, casual
    glossary_id UUID REFERENCES glossaries(id),
    settings JSONB NOT NULL DEFAULT '{}', -- full job settings
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_status CHECK (status IN ('created', 'queued', 'parsing', 'transcribing', 'translating', 'postprocessing', 'review', 'completed', 'failed')),
    CONSTRAINT valid_priority CHECK (priority IN ('normal', 'fast', 'immediate')),
    CONSTRAINT valid_style CHECK (translation_style IN ('formal', 'neutral', 'casual'))
);

-- Job files table - individual files within a job
CREATE TABLE job_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    object_key TEXT NOT NULL, -- MinIO storage key
    mime_type TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    checksum TEXT NOT NULL,
    media_type TEXT NOT NULL, -- document, audio, video, image
    pages INTEGER, -- for documents
    duration_seconds NUMERIC(10,3), -- for audio/video
    status TEXT DEFAULT 'uploaded', -- uploaded, parsing, transcribing, translating, completed, failed
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT valid_media_type CHECK (media_type IN ('document', 'audio', 'video', 'image')),
    CONSTRAINT valid_file_status CHECK (status IN ('uploaded', 'parsing', 'transcribing', 'translating', 'completed', 'failed'))
);

-- Job events table - audit log for job processing
CREATE TABLE job_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    message TEXT,
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    created_by UUID -- optional, for human-initiated events
);

-- Job artifacts table - processed outputs
CREATE TABLE job_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    job_file_id UUID REFERENCES job_files(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL, -- parsed, transcript, translation, subtitle, audio, final
    language_code TEXT, -- target language for translations
    object_key TEXT NOT NULL, -- MinIO storage key
    version INTEGER DEFAULT 1,
    review_status TEXT DEFAULT 'pending', -- pending, reviewed, accepted, rejected
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT valid_artifact_type CHECK (artifact_type IN ('parsed', 'transcript', 'translation', 'subtitle', 'audio', 'final')),
    CONSTRAINT valid_review_status CHECK (review_status IN ('pending', 'reviewed', 'accepted', 'rejected'))
);

-- Indexes for performance
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_client_id ON jobs(client_id);
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_job_files_job_id ON job_files(job_id);
CREATE INDEX idx_job_files_status ON job_files(status);
CREATE INDEX idx_job_events_job_id ON job_events(job_id);
CREATE INDEX idx_job_events_created_at ON job_events(created_at);
CREATE INDEX idx_job_artifacts_job_id ON job_artifacts(job_id);
CREATE INDEX idx_job_artifacts_type ON job_artifacts(artifact_type);
CREATE INDEX idx_glossaries_client_id ON glossaries(client_id);

-- Add some constraints and triggers for data integrity
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Update triggers
CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_job_files_updated_at BEFORE UPDATE ON job_files FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_glossaries_updated_at BEFORE UPDATE ON glossaries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO glossaries (client_id, name, data, language_pair) VALUES
(gen_random_uuid(), 'CS Terms EN-ES',
 '{"algorithm": "algoritmo", "database": "base de datos", "function": "función", "variable": "variable", "loop": "bucle"}',
 'en-es');

COMMENT ON TABLE jobs IS 'Course translation jobs that group multiple files';
COMMENT ON TABLE job_files IS 'Individual files within a translation job';
COMMENT ON TABLE job_events IS 'Audit log for job processing events';
COMMENT ON TABLE job_artifacts IS 'Processed outputs from translation pipeline';
COMMENT ON TABLE glossaries IS 'Translation glossaries for term consistency';