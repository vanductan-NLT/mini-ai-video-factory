-- Migration: Create tables for Mini Video Factory
-- Chỉ tạo bảng trong public schema, không động vào auth schema
-- Tránh foreign key constraints để tránh lỗi permission

-- Tạo bảng users (sync thủ công với Supabase Auth)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID UNIQUE, -- Reference to auth.users.id (manual sync)
    username TEXT,
    email TEXT UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- Index cho performance
CREATE INDEX IF NOT EXISTS idx_users_auth_id ON public.users(auth_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- Tạo bảng processing_jobs (không dùng foreign key để tránh lỗi permission)
CREATE TABLE IF NOT EXISTS public.processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- Reference to users.auth_id (no foreign key constraint)
    original_filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    input_storage_key TEXT,
    output_storage_key TEXT
);

-- Index cho processing_jobs
CREATE INDEX IF NOT EXISTS idx_processing_jobs_user_id ON public.processing_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON public.processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_created_at ON public.processing_jobs(created_at);

-- Tạo bảng file_metadata (không dùng foreign key để tránh lỗi permission)
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

-- Index cho file_metadata
CREATE INDEX IF NOT EXISTS idx_file_metadata_job_id ON public.file_metadata(job_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_file_type ON public.file_metadata(file_type);

-- Comments
COMMENT ON TABLE public.users IS 'User profiles synced with Supabase Auth';
COMMENT ON TABLE public.processing_jobs IS 'Video processing jobs';
COMMENT ON TABLE public.file_metadata IS 'Metadata for uploaded and processed files';