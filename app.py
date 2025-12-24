"""
Mini Video Factory - Main Flask Application

A self-hosted web application for automated video processing with auto-editing and subtitles.
"""

import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
from config.logging import setup_logging
from config.storage import wasabi_config
from auth.auth_manager import AuthManager
from models.user import User

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

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Initialize AuthManager
auth_manager = None

class FlaskUser(UserMixin):
    """Flask-Login user wrapper for our User model"""
    def __init__(self, user: User):
        self.user = user
    
    def get_id(self):
        return self.user.id
    
    @property
    def username(self):
        return self.user.username

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    global auth_manager
    if auth_manager is None:
        return None
    
    user = auth_manager.get_user_by_id(user_id)
    if user:
        return FlaskUser(user)
    return None

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

# Initialize AuthManager
try:
    auth_manager = AuthManager()
    app.logger.info("AuthManager initialized successfully")
except Exception as e:
    app.logger.error(f"Failed to initialize AuthManager: {str(e)}")
    auth_manager = None

# Validate Wasabi configuration
if wasabi_config.is_configured:
    app.logger.info(f"Wasabi storage configured - Bucket: {wasabi_config.get_bucket_name()}")
else:
    app.logger.warning("Wasabi storage not configured - check environment variables")

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')
        
        if auth_manager is None:
            flash('Authentication system unavailable. Please try again later.', 'error')
            return render_template('login.html')
        
        user = auth_manager.authenticate_user(username, password)
        if user:
            flask_user = FlaskUser(user)
            login_user(flask_user)
            app.logger.info(f"User '{username}' logged in successfully")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            app.logger.warning(f"Failed login attempt for username: {username}")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    username = current_user.username if current_user.is_authenticated else 'Unknown'
    logout_user()
    app.logger.info(f"User '{username}' logged out")
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - protected route"""
    return render_template('dashboard.html', user=current_user)

# Basic route for testing
@app.route('/')
def index():
    """Main application route - redirect to dashboard if logged in, otherwise login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

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