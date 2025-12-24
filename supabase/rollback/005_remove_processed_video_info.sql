-- Remove processed_video_info column from processing_jobs table

ALTER TABLE processing_jobs 
DROP COLUMN IF EXISTS processed_video_info;