-- Rollback: Recreate file_metadata table if needed
-- This recreates the table that was dropped in migration 004

-- Recreate file_metadata table
CREATE TABLE IF NOT EXISTS public.file_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL, -- Reference to processing_jobs.id (no foreign key constraint)
    filename TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    duration FLOAT,
    storage_key TEXT NOT NULL,
    file_type TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_file_metadata_job_id ON public.file_metadata(job_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_file_type ON public.file_metadata(file_type);

-- Comment
COMMENT ON TABLE public.file_metadata IS 'Metadata for uploaded and processed files';