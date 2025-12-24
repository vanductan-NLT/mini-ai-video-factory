-- Rollback: Drop user trigger and function

-- Drop trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Drop function
DROP FUNCTION IF EXISTS public.handle_new_user();