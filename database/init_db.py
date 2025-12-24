"""
Database initialization script for Mini Video Factory
Creates the required tables in Supabase
"""

import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_tables():
    """Create the required database tables in Supabase"""
    
    # Initialize Supabase client
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables are required")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # SQL to create users table
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        last_login TIMESTAMP WITH TIME ZONE
    );
    
    -- Create index on username for faster lookups
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    """
    
    # SQL to create processing_jobs table (for future use)
    processing_jobs_table_sql = """
    CREATE TABLE IF NOT EXISTS processing_jobs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        original_filename TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'uploaded',
        progress INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        completed_at TIMESTAMP WITH TIME ZONE,
        error_message TEXT,
        input_storage_key TEXT,
        output_storage_key TEXT
    );
    
    -- Create indexes for faster queries
    CREATE INDEX IF NOT EXISTS idx_processing_jobs_user_id ON processing_jobs(user_id);
    CREATE INDEX IF NOT EXISTS idx_processing_jobs_status ON processing_jobs(status);
    CREATE INDEX IF NOT EXISTS idx_processing_jobs_created_at ON processing_jobs(created_at);
    """
    
    # SQL to create file_metadata table (for future use)
    file_metadata_table_sql = """
    CREATE TABLE IF NOT EXISTS file_metadata (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_id UUID NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
        filename TEXT NOT NULL,
        file_size BIGINT NOT NULL,
        duration FLOAT,
        storage_key TEXT NOT NULL,
        file_type TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create indexes for faster queries
    CREATE INDEX IF NOT EXISTS idx_file_metadata_job_id ON file_metadata(job_id);
    CREATE INDEX IF NOT EXISTS idx_file_metadata_file_type ON file_metadata(file_type);
    """
    
    try:
        # Execute table creation SQL
        print("Creating users table...")
        supabase.rpc('exec_sql', {'sql': users_table_sql}).execute()
        
        print("Creating processing_jobs table...")
        supabase.rpc('exec_sql', {'sql': processing_jobs_table_sql}).execute()
        
        print("Creating file_metadata table...")
        supabase.rpc('exec_sql', {'sql': file_metadata_table_sql}).execute()
        
        print("Database tables created successfully!")
        
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        print("Note: You may need to create these tables manually in your Supabase dashboard")
        print("\nSQL Commands to run manually:")
        print("\n1. Users table:")
        print(users_table_sql)
        print("\n2. Processing jobs table:")
        print(processing_jobs_table_sql)
        print("\n3. File metadata table:")
        print(file_metadata_table_sql)

def create_test_user():
    """Create a test user for development"""
    from auth.auth_manager import AuthManager
    
    try:
        auth_manager = AuthManager()
        
        # Create test user
        test_user = auth_manager.create_user('admin', 'admin123')
        if test_user:
            print(f"Test user created: username='admin', password='admin123'")
        else:
            print("Test user already exists or creation failed")
            
    except Exception as e:
        print(f"Error creating test user: {str(e)}")

if __name__ == '__main__':
    print("Initializing Mini Video Factory database...")
    create_tables()
    
    # Ask if user wants to create test user
    create_test = input("\nCreate test user (admin/admin123)? [y/N]: ").lower().strip()
    if create_test in ['y', 'yes']:
        create_test_user()
    
    print("\nDatabase initialization complete!")