"""
Mini Video Factory - Main Flask Application

A self-hosted web application for automated video processing with auto-editing and subtitles.
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
from config.logging import setup_logging
from config.storage import wasabi_config

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_FILE_SIZE', 104857600))  # 100MB default
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', './data/uploads')
app.config['TEMP_FOLDER'] = os.environ.get('TEMP_FOLDER', './data/temp')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', './data/output')

# Ensure data directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Setup logging
setup_logging(app)
app.logger.info("Mini Video Factory starting up...")
app.logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
app.logger.info(f"Temp folder: {app.config['TEMP_FOLDER']}")
app.logger.info(f"Output folder: {app.config['OUTPUT_FOLDER']}")

# Validate Wasabi configuration
if wasabi_config.is_configured:
    app.logger.info(f"Wasabi storage configured - Bucket: {wasabi_config.get_bucket_name()}")
else:
    app.logger.warning("Wasabi storage not configured - check environment variables")

# Basic route for testing
@app.route('/')
def index():
    """Main application route - will be expanded in later tasks"""
    return "Mini Video Factory - Coming Soon"

@app.route('/health')
def health_check():
    """Health check endpoint for Docker deployment"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}

if __name__ == '__main__':
    # Development server configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.run(host=host, port=port, debug=debug_mode)