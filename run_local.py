#!/usr/bin/env python3
"""
Local development runner for Mini Video Factory
"""

import os
import sys
from dotenv import load_dotenv

# Load local environment
load_dotenv('.env.local')

# Create local directories
os.makedirs('./data/uploads', exist_ok=True)
os.makedirs('./data/temp', exist_ok=True)
os.makedirs('./data/output', exist_ok=True)
os.makedirs('./logs', exist_ok=True)

# Import and run app
if __name__ == '__main__':
    from app import app
    
    # Check database configuration
    database_url = os.environ.get('DATABASE_URL')
    supabase_url = os.environ.get('SUPABASE_URL')
    
    print("🚀 Starting Mini Video Factory (Local Development)")
    
    if supabase_url:
        print("📁 Using Supabase database")
    elif database_url:
        print("📁 Using local PostgreSQL database")
    else:
        print("⚠️  No database configured")
    
    print("🌐 Access: http://localhost:5000")
    print("🔧 Debug mode: ON")
    print("-" * 50)
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )