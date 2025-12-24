-- Migration: Add missing columns to processing_jobs table
-- Add columns for file paths and video metadata

-- Add input_file_path column for local file storage path
ALTER TABLE public.processing_jobs 
ADD COLUMN IF NOT EXISTS input_file_path TEXT;

-- Add output_file_path column for processed file path  
ALTER TABLE public.processing_jobs 
ADD COLUMN IF NOT EXISTS output_file_path TEXT;

-- Add video_info column for storing video metadata as JSON
ALTER TABLE public.processing_jobs 
ADD COLUMN IF NOT EXISTS video_info JSONB;

-- Add index for video_info queries (GIN index for JSONB)
CREATE INDEX IF NOT EXISTS idx_processing_jobs_video_info ON public.processing_jobs USING GIN (video_info);

-- Comments for documentation
COMMENT ON COLUMN public.processing_jobs.input_file_path IS 'Local file path for input video (when stored locally)';
COMMENT ON COLUMN public.processing_jobs.output_file_path IS 'Local file path for processed video output';
COMMENT ON COLUMN public.processing_jobs.video_info IS 'Video metadata JSON (duration, size, format, etc.)';