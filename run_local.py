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
    
    print("🚀 Starting Mini Video Factory (Local Development)")
    print("📁 Using local SQLite database")
    print("🌐 Access: http://localhost:5000")
    print("🔧 Debug mode: ON")
    
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )