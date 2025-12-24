-- Migration: Drop file_metadata table as it's not needed
-- All file metadata is now stored in processing_jobs.video_info column

-- Drop indexes first
DROP INDEX IF EXISTS public.idx_file_metadata_job_id;
DROP INDEX IF EXISTS public.idx_file_metadata_file_type;

-- Drop the file_metadata table
DROP TABLE IF EXISTS public.file_metadata;

-- Comment
-- File metadata is now stored as JSON in processing_jobs.video_info column