-- Rollback: Remove columns added in migration 003_add_missing_columns.sql
-- This will remove the columns that were added to processing_jobs table

-- Drop the GIN index first
DROP INDEX IF EXISTS public.idx_processing_jobs_video_info;

-- Remove the added columns from processing_jobs table
ALTER TABLE public.processing_jobs 
DROP COLUMN IF EXISTS input_file_path,
DROP COLUMN IF EXISTS output_file_path,
DROP COLUMN IF EXISTS video_info;

-- Note: Comments are automatically removed when columns are dropped