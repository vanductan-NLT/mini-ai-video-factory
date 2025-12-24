-- Add processed_video_info column to processing_jobs table
-- This column will store metadata about the processed video (duration, size, etc.)

ALTER TABLE processing_jobs 
ADD COLUMN processed_video_info TEXT;

-- Add comment to explain the column
COMMENT ON COLUMN processing_jobs.processed_video_info IS 'JSON metadata about the processed video including duration, size, compression ratio, etc.';