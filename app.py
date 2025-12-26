"""
Mini Video Factory - Main Flask Application

A self-hosted web application for automated video processing with auto-editing and subtitles.
"""

import os
import logging
import uuid
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
from config.logging import setup_logging
from config.storage import wasabi_config
from auth.auth_manager import AuthManager
from storage.storage_manager import StorageManager
from models.user import User
from models.processing_job import (
    ProcessingJob, ProcessingStatus, save_processing_job, 
    get_processing_job, get_user_jobs
)
from utils.file_validation import validate_video_file, ValidationError, SUPPORTED_EXTENSIONS
from processing.video_processor import VideoProcessor

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

# Initialize AuthManager and StorageManager
auth_manager = None
storage_manager = None
video_processor = None

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

# Initialize AuthManager and StorageManager
try:
    auth_manager = AuthManager()
    app.logger.info("AuthManager initialized successfully")
except Exception as e:
    app.logger.error(f"Failed to initialize AuthManager: {str(e)}")
    auth_manager = None

try:
    from storage.storage_manager import StorageManager
    storage_manager = StorageManager()
    if storage_manager.is_available:
        app.logger.info("StorageManager initialized successfully")
    else:
        app.logger.warning("StorageManager initialized but not available (check Wasabi config)")
except Exception as e:
    app.logger.error(f"Failed to initialize StorageManager: {str(e)}")
    storage_manager = None

try:
    video_processor = VideoProcessor(storage_manager)
    app.logger.info("VideoProcessor initialized successfully")
except Exception as e:
    app.logger.error(f"Failed to initialize VideoProcessor: {str(e)}")
    video_processor = None

# Validate Wasabi configuration
if wasabi_config.is_configured:
    app.logger.info(f"Wasabi storage configured - Bucket: {wasabi_config.get_bucket_name()}")
else:
    app.logger.warning("Wasabi storage not configured - check environment variables")

# File upload and processing routes
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle video file upload with validation and storage"""
    try:
        # Check if file was uploaded
        if 'video_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['video_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Create processing job
        job = ProcessingJob.create_new(current_user.get_id(), file.filename)
        save_processing_job(job)  # Save initial job to Supabase
        
        # Generate secure filename
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        unique_filename = f"{job.id}_{filename}"
        
        # Save file temporarily for validation
        temp_path = os.path.join(app.config['TEMP_FOLDER'], unique_filename)
        file.save(temp_path)
        
        # Update job status to validating
        job.update_status(ProcessingStatus.VALIDATING, progress=10)
        save_processing_job(job)  # Save validation status to Supabase
        
        try:
            # Validate file
            max_size = app.config['MAX_CONTENT_LENGTH']
            max_duration = int(os.environ.get('MAX_DURATION', 600))  # 10 minutes default
            
            video_info = validate_video_file(file, temp_path, max_size, max_duration)
            job.set_video_info(video_info)
            
            # Update job status to storing
            job.update_status(ProcessingStatus.STORING, progress=30)
            save_processing_job(job)  # Save storing status to Supabase
            
            # Try to upload to Wasabi storage if available
            storage_key = f"uploads/{current_user.get_id()}/{unique_filename}"
            
            if storage_manager and storage_manager.is_available:
                # Upload to Wasabi storage
                if storage_manager.upload_file(temp_path, storage_key):
                    job.set_input_paths(None, storage_key)  # Only storage key, no local path
                    app.logger.info(f"File uploaded to Wasabi storage: {storage_key}")
                    
                    # Clean up temp file after successful upload
                    os.remove(temp_path)
                else:
                    # Fallback to local storage if Wasabi upload fails
                    local_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    os.rename(temp_path, local_path)
                    job.set_input_paths(local_path, None)  # Only local path, no storage key
                    app.logger.warning(f"Wasabi upload failed, using local storage: {local_path}")
            else:
                # Use local storage if Wasabi is not available
                local_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                os.rename(temp_path, local_path)
                job.set_input_paths(local_path, None)  # Only local path, no storage key
                app.logger.info(f"Using local storage: {local_path}")
            
            # Update job status to uploaded and ready for processing
            job.update_status(ProcessingStatus.UPLOADED, progress=50)
            save_processing_job(job)  # This will now save to Supabase
            
            return jsonify({
                'success': True,
                'job_id': job.id,
                'message': 'File uploaded successfully',
                'video_info': video_info
            })
            
        except ValidationError as e:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            job.update_status(ProcessingStatus.FAILED, error_message=str(e))
            save_processing_job(job)  # Save failed status to Supabase
            
            return jsonify({'error': str(e)}), 400
            
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': 'Upload failed. Please try again.'}), 500

@app.route('/upload_progress/<job_id>')
@login_required
def upload_progress(job_id):
    """Get upload/processing progress for a job"""
    job = get_processing_job(job_id)
    
    if not job or job.user_id != current_user.get_id():
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'job_id': job.id,
        'status': job.status.value,
        'status_display': job.get_status_display(),
        'progress': job.progress,
        'error_message': job.error_message,
        'video_info': job.video_info,
        'completed': job.is_completed()
    })

@app.route('/user_jobs')
@login_required
def user_jobs():
    """Get all jobs for the current user"""
    try:
        user_id = current_user.get_id()
        app.logger.info(f"Loading jobs for user: {user_id}")
        
        jobs = get_user_jobs(user_id)
        app.logger.info(f"Found {len(jobs)} jobs for user {user_id}")
        
        jobs_data = []
        for job in jobs:
            try:
                job_dict = job.to_dict()
                jobs_data.append(job_dict)
                app.logger.info(f"Job {job.id}: {job.original_filename} - {job.status.value}")
            except Exception as e:
                app.logger.error(f"Error converting job {job.id} to dict: {e}")
                continue
        
        return jsonify({
            'jobs': jobs_data
        })
    except Exception as e:
        app.logger.error(f"Error in user_jobs route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to load jobs', 'jobs': []}), 500

@app.route('/debug/jobs')
@login_required
def debug_jobs():
    """Debug route to check jobs in database"""
    try:
        from models.processing_job import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return jsonify({'error': 'Supabase not available'})
        
        user_id = current_user.get_id()
        result = supabase.table('processing_jobs').select('*').eq('user_id', user_id).execute()
        
        return jsonify({
            'user_id': user_id,
            'raw_data': result.data,
            'count': len(result.data)
        })
    except Exception as e:
        app.logger.error(f"Debug jobs error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/process_video/<job_id>', methods=['POST'])
@login_required
def process_video(job_id):
    """Start video processing for a job"""
    try:
        job = get_processing_job(job_id)
        
        if not job or job.user_id != current_user.get_id():
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != ProcessingStatus.UPLOADED:
            return jsonify({'error': 'Job is not ready for processing'}), 400
        
        if video_processor is None:
            return jsonify({'error': 'Video processor not available'}), 503
        
        # Start processing in background (for now, synchronous)
        # In production, this should be done asynchronously with a task queue
        def progress_callback(message: str, progress: int):
            app.logger.info(f"Job {job_id} progress: {message} ({progress}%)")
        
        success = video_processor.process_video(job, progress_callback)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Video processing completed successfully',
                'job_id': job.id
            })
        else:
            return jsonify({
                'success': False,
                'error': job.error_message or 'Processing failed',
                'job_id': job.id
            }), 500
            
    except Exception as e:
        app.logger.error(f"Processing error for job {job_id}: {str(e)}")
        return jsonify({'error': 'Processing failed. Please try again.'}), 500

@app.route('/preview/<job_id>')
@login_required
def preview_video(job_id):
    """Preview processed video with embedded subtitles"""
    try:
        job = get_processing_job(job_id)
        
        if not job or job.user_id != current_user.get_id():
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != ProcessingStatus.COMPLETED:
            return jsonify({'error': 'Video processing not completed'}), 400
        
        return render_template('preview.html', job=job, user=current_user)
            
    except Exception as e:
        app.logger.error(f"Preview error for job {job_id}: {str(e)}")
        return jsonify({'error': 'Preview failed. Please try again.'}), 500

@app.route('/video_stream/<job_id>')
@login_required
def stream_video(job_id):
    """Stream processed video for preview"""
    try:
        job = get_processing_job(job_id)
        
        if not job or job.user_id != current_user.get_id():
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != ProcessingStatus.COMPLETED:
            return jsonify({'error': 'Video processing not completed'}), 400
        
        # Try to serve from local storage first
        if job.output_file_path and os.path.exists(job.output_file_path):
            from flask import send_file, Response
            import mimetypes
            
            # Get file size for range requests
            file_size = os.path.getsize(job.output_file_path)
            
            # Handle range requests for video streaming
            range_header = request.headers.get('Range', None)
            if range_header:
                byte_start = 0
                byte_end = file_size - 1
                
                if range_header:
                    match = re.search(r'bytes=(\d+)-(\d*)', range_header)
                    if match:
                        byte_start = int(match.group(1))
                        if match.group(2):
                            byte_end = int(match.group(2))
                
                # Ensure byte_end doesn't exceed file size
                byte_end = min(byte_end, file_size - 1)
                
                # Read the requested chunk
                with open(job.output_file_path, 'rb') as f:
                    f.seek(byte_start)
                    data = f.read(byte_end - byte_start + 1)
                
                response = Response(
                    data,
                    206,  # Partial Content
                    headers={
                        'Content-Range': f'bytes {byte_start}-{byte_end}/{file_size}',
                        'Accept-Ranges': 'bytes',
                        'Content-Length': str(len(data)),
                        'Content-Type': 'video/mp4',
                    }
                )
                return response
            else:
                # Serve full file
                return send_file(
                    job.output_file_path,
                    mimetype='video/mp4',
                    as_attachment=False
                )
        
        # Try to generate streaming URL from Wasabi storage
        elif job.output_storage_key and storage_manager and storage_manager.is_available:
            stream_url = storage_manager.generate_download_url(job.output_storage_key, expiration=7200)  # 2 hours
            if stream_url:
                return redirect(stream_url)
            else:
                return jsonify({'error': 'Failed to generate streaming URL'}), 500
        
        else:
            return jsonify({'error': 'Processed video not found'}), 404
            
    except Exception as e:
        app.logger.error(f"Video streaming error for job {job_id}: {str(e)}")
        return jsonify({'error': 'Video streaming failed. Please try again.'}), 500

@app.route('/download/<job_id>')
@login_required
def download_video(job_id):
    """Download processed video with progress tracking"""
    try:
        job = get_processing_job(job_id)
        
        if not job or job.user_id != current_user.get_id():
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != ProcessingStatus.COMPLETED:
            return jsonify({'error': 'Video processing not completed'}), 400
        
        if job.output_storage_key and storage_manager and storage_manager.is_available:
            # Generate download URL for Wasabi storage
            download_url = storage_manager.generate_download_url(job.output_storage_key)
            if download_url:
                return redirect(download_url)
            else:
                return jsonify({'error': 'Failed to generate download URL'}), 500
        
        elif job.output_file_path and os.path.exists(job.output_file_path):
            # Serve from local storage
            from flask import send_file
            return send_file(
                job.output_file_path,
                as_attachment=True,
                download_name=f"processed_{job.original_filename}"
            )
        
        else:
            return jsonify({'error': 'Processed video not found'}), 404
            
    except Exception as e:
        app.logger.error(f"Download error for job {job_id}: {str(e)}")
        return jsonify({'error': 'Download failed. Please try again.'}), 500

@app.route('/download_progress/<job_id>')
@login_required
def download_progress(job_id):
    """Track download progress for a job"""
    try:
        job = get_processing_job(job_id)
        
        if not job or job.user_id != current_user.get_id():
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != ProcessingStatus.COMPLETED:
            return jsonify({'error': 'Video processing not completed'}), 400
        
        # Get file metadata for progress tracking
        file_info = {}
        if job.output_storage_key and storage_manager and storage_manager.is_available:
            storage_info = storage_manager.get_file_info(job.output_storage_key)
            if storage_info:
                file_info = {
                    'size': storage_info['size'],
                    'last_modified': storage_info['last_modified'].isoformat() if storage_info['last_modified'] else None,
                    'content_type': storage_info['content_type']
                }
        elif job.output_file_path and os.path.exists(job.output_file_path):
            stat = os.stat(job.output_file_path)
            file_info = {
                'size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'content_type': 'video/mp4'
            }
        
        return jsonify({
            'job_id': job.id,
            'original_filename': job.original_filename,
            'file_info': file_info,
            'download_ready': True
        })
        
    except Exception as e:
        app.logger.error(f"Download progress error for job {job_id}: {str(e)}")
        return jsonify({'error': 'Download progress check failed'}), 500

@app.route('/processing_status/<job_id>')
@login_required
def processing_status(job_id):
    """Get detailed processing status for a job"""
    try:
        job = get_processing_job(job_id)
        
        if not job or job.user_id != current_user.get_id():
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'job_id': job.id,
            'status': job.status.value,
            'status_display': job.get_status_display(),
            'progress': job.progress,
            'error_message': job.error_message,
            'completed': job.is_completed(),
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'original_filename': job.original_filename,
            'video_info': job.video_info
        })
        
    except Exception as e:
        app.logger.error(f"Status check error for job {job_id}: {str(e)}")
        return jsonify({'error': 'Status check failed'}), 500

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if request.method == 'POST':
        email = request.form.get('email') or request.form.get('username')  # Support both
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html')
        
        if auth_manager is None:
            flash('Authentication system unavailable. Please try again later.', 'error')
            return render_template('login.html')
        
        user = auth_manager.authenticate_user(email, password)
        if user:
            flask_user = FlaskUser(user)
            login_user(flask_user)
            app.logger.info(f"User '{email}' logged in successfully")
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            app.logger.warning(f"Failed login attempt for email: {email}")
    
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
    try:
        # Basic health check
        return {
            'status': 'healthy', 
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected' if os.environ.get('DATABASE_URL') else 'not_configured'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, 500

@app.route('/')
def index():
    """Root endpoint"""
    return {
        'message': 'Mini Video Factory running',
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat()
    }

def run_migrations():
    """Run database migrations on startup"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Get database URL
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logging.warning("No DATABASE_URL found, skipping migrations")
            return
        
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
            
            for migration_file in migration_files:
                migration_path = os.path.join(migration_dir, migration_file)
                logging.info(f"Running migration: {migration_file}")
                
                with open(migration_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Execute migration
                cursor.execute(sql_content)
                conn.commit()
                logging.info(f"Migration completed: {migration_file}")
        
        cursor.close()
        conn.close()
        logging.info("All migrations completed successfully")
        
    except Exception as e:
        logging.error(f"Migration failed: {e}")
        # Don't fail app startup if migrations fail
        pass

if __name__ == '__main__':
    # Run migrations on startup
    run_migrations()
    
    # Development server configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    app.run(host=host, port=port, debug=debug_mode)