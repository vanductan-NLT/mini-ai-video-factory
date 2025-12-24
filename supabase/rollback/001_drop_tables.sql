-- Rollback: Drop tables for Mini Video Factory
-- Xóa các bảng theo thứ tự ngược lại để tránh lỗi dependency

-- Drop file_metadata table
DROP TABLE IF EXISTS public.file_metadata;

-- Drop processing_jobs table  
DROP TABLE IF EXISTS public.processing_jobs;

-- Drop users table
DROP TABLE IF EXISTS public.users;