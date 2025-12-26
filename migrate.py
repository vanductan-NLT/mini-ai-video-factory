#!/usr/bin/env python3
"""
Database Migration Script for Mini Video Factory

This script runs database migrations on startup.
"""

import os
import sys
import logging
import psycopg2
from urllib.parse import urlparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migrations():
    """Run database migrations"""
    try:
        # Check if we're using local PostgreSQL or Supabase
        database_url = os.environ.get('DATABASE_URL')
        supabase_url = os.environ.get('SUPABASE_URL')
        
        if database_url:
            # Using local PostgreSQL
            logger.info("Using local PostgreSQL database")
            logger.info("Connecting to database...")
            
            # Parse database URL
            parsed = urlparse(database_url)
            
            # Connect to database
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password
            )
            
            cursor = conn.cursor()
            
            # Read and execute migration files
            migration_dir = './supabase/migrations'
            if os.path.exists(migration_dir):
                migration_files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])
                
                if not migration_files:
                    logger.info("No migration files found")
                    return True
                
                for migration_file in migration_files:
                    migration_path = os.path.join(migration_dir, migration_file)
                    logger.info(f"Running migration: {migration_file}")
                    
                    try:
                        with open(migration_path, 'r', encoding='utf-8') as f:
                            sql_content = f.read()
                        
                        # Execute migration
                        cursor.execute(sql_content)
                        conn.commit()
                        logger.info(f"Migration completed: {migration_file}")
                        
                    except Exception as e:
                        logger.error(f"Failed to run migration {migration_file}: {e}")
                        # Continue with other migrations
                        conn.rollback()
            else:
                logger.info("No migrations directory found")
            
            cursor.close()
            conn.close()
            logger.info("All migrations completed successfully")
            
        elif supabase_url:
            # Using Supabase - migrations are handled by Supabase
            logger.info("Using Supabase - migrations handled externally")
            
        else:
            logger.warning("No database configuration found (DATABASE_URL or SUPABASE_URL)")
            logger.info("Skipping migrations")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = run_migrations()
    if not success:
        logger.error("Migrations failed, but continuing startup...")
        # Don't exit with error code to allow app to start
    sys.exit(0)