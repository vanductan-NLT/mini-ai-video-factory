from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
import os
import json
from supabase import create_client, Client

class ProcessingStatus(Enum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    STORING = "storing"
    AUTO_EDITING = "auto_editing"
    TRANSCRIBING = "transcribing"
    ADDING_SUBTITLES = "adding_subtitles"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcessingJob:
    id: str
    user_id: str
    original_filename: str
    status: ProcessingStatus
    progress: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    input_file_path: Optional[str] = None
    output_file_path: Optional[str] = None
    input_storage_key: Optional[str] = None
    output_storage_key: Optional[str] = None
    video_info: Optional[Dict[str, Any]] = None
    processed_video_info: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create_new(cls, user_id: str, original_filename: str):
        job_id = str(uuid.uuid4())
        return cls(
            id=job_id,
            user_id=user_id,
            original_filename=original_filename,
            status=ProcessingStatus.UPLOADED,
            progress=0,
            created_at=datetime.utcnow()
        )
    
    def update_status(self, status: ProcessingStatus, progress: Optional[int] = None, error_message: Optional[str] = None):
        self.status = status
        if progress is not None:
            self.progress = max(0, min(100, progress))
        if error_message:
            self.error_message = error_message
        if status == ProcessingStatus.COMPLETED:
            self.completed_at = datetime.utcnow()
            self.progress = 100
        elif status == ProcessingStatus.FAILED:
            self.completed_at = datetime.utcnow()
    
    def set_input_paths(self, local_path: Optional[str], storage_key: Optional[str]):
        self.input_file_path = local_path
        self.input_storage_key = storage_key
    
    def set_output_paths(self, local_path: Optional[str], storage_key: Optional[str]):
        self.output_file_path = local_path
        self.output_storage_key = storage_key
    
    def set_video_info(self, video_info: Dict[str, Any]):
        self.video_info = video_info
    
    def set_processed_video_info(self, processed_info: Dict[str, Any]):
        """Set metadata about the processed video"""
        self.processed_video_info = processed_info
    
    def get_file_size_mb(self) -> Optional[float]:
        """Get original file size in MB"""
        if self.video_info and 'size' in self.video_info:
            return self.video_info['size'] / (1024 * 1024)
        return None
    
    def get_processed_file_size_mb(self) -> Optional[float]:
        """Get processed file size in MB"""
        if self.processed_video_info and 'size' in self.processed_video_info:
            return self.processed_video_info['size'] / (1024 * 1024)
        return None
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get original video duration in seconds"""
        if self.video_info and 'duration' in self.video_info:
            return self.video_info['duration']
        return None
    
    def get_processed_duration_seconds(self) -> Optional[float]:
        """Get processed video duration in seconds"""
        if self.processed_video_info and 'duration' in self.processed_video_info:
            return self.processed_video_info['duration']
        return None
    
    def get_compression_ratio(self) -> Optional[float]:
        """Get compression ratio (processed size / original size)"""
        original_size = self.get_file_size_mb()
        processed_size = self.get_processed_file_size_mb()
        if original_size and processed_size and original_size > 0:
            return processed_size / original_size
        return None
    
    def get_time_saved_seconds(self) -> Optional[float]:
        """Get time saved by auto-editing in seconds"""
        original_duration = self.get_duration_seconds()
        processed_duration = self.get_processed_duration_seconds()
        if original_duration and processed_duration:
            return max(0, original_duration - processed_duration)
        return None
    
    def is_completed(self) -> bool:
        return self.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
    
    def get_status_display(self) -> str:
        status_display = {
            ProcessingStatus.UPLOADED: "Uploaded",
            ProcessingStatus.VALIDATING: "Validating file...",
            ProcessingStatus.STORING: "Storing file...",
            ProcessingStatus.AUTO_EDITING: "Auto-editing video...",
            ProcessingStatus.TRANSCRIBING: "Generating subtitles...",
            ProcessingStatus.ADDING_SUBTITLES: "Adding subtitles...",
            ProcessingStatus.COMPLETED: "Completed",
            ProcessingStatus.FAILED: "Failed"
        }
        return status_display.get(self.status, self.status.value)
    
    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

_processing_jobs: Dict[str, ProcessingJob] = {}

# Initialize Supabase client
def get_supabase_client() -> Optional[Client]:
    """Get Supabase client for database operations"""
    try:
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')  # Changed from SUPABASE_ANON_KEY to SUPABASE_KEY
        
        if not url or not key:
            print(f"Missing Supabase config - URL: {bool(url)}, KEY: {bool(key)}")
            return None
            
        client = create_client(url, key)
        print("Supabase client created successfully")
        return client
    except Exception as e:
        print(f"Error creating Supabase client: {e}")
        return None

def save_processing_job(job: ProcessingJob):
    """Save processing job to both memory and Supabase database"""
    # Save to memory for backward compatibility
    _processing_jobs[job.id] = job
    print(f"Saved job {job.id} to memory")
    
    # Save to Supabase database
    supabase = get_supabase_client()
    if supabase:
        try:
            job_data = {
                'id': job.id,
                'user_id': job.user_id,
                'original_filename': job.original_filename,
                'status': job.status.value,
                'progress': job.progress,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message,
                'input_file_path': job.input_file_path,
                'output_file_path': job.output_file_path,
                'input_storage_key': job.input_storage_key,
                'output_storage_key': job.output_storage_key,
                'video_info': json.dumps(job.video_info) if job.video_info else None,
                'processed_video_info': json.dumps(job.processed_video_info) if job.processed_video_info else None
            }
            
            print(f"Attempting to save job {job.id} to Supabase...")
            print(f"Job data: {job_data}")
            
            # Try to update first, if not exists then insert
            result = supabase.table('processing_jobs').select('id').eq('id', job.id).execute()
            
            if result.data:
                # Update existing job
                print(f"Updating existing job {job.id}")
                update_result = supabase.table('processing_jobs').update(job_data).eq('id', job.id).execute()
                print(f"Update result: {update_result}")
            else:
                # Insert new job
                print(f"Inserting new job {job.id}")
                insert_result = supabase.table('processing_jobs').insert(job_data).execute()
                print(f"Insert result: {insert_result}")
                
            print(f"Successfully saved job {job.id} to Supabase")
                    
        except Exception as e:
            print(f"Error saving job to Supabase: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Supabase client not available")

def get_processing_job(job_id: str) -> Optional[ProcessingJob]:
    """Get processing job from memory first, then from Supabase if not found"""
    # Try memory first
    if job_id in _processing_jobs:
        return _processing_jobs[job_id]
    
    # Try Supabase database
    supabase = get_supabase_client()
    if supabase:
        try:
            result = supabase.table('processing_jobs').select('*').eq('id', job_id).execute()
            
            if result.data:
                job_data = result.data[0]
                job = ProcessingJob(
                    id=job_data['id'],
                    user_id=job_data['user_id'],
                    original_filename=job_data['original_filename'],
                    status=ProcessingStatus(job_data['status']),
                    progress=job_data['progress'],
                    created_at=datetime.fromisoformat(job_data['created_at'].replace('Z', '+00:00')) if job_data['created_at'] else None,
                    completed_at=datetime.fromisoformat(job_data['completed_at'].replace('Z', '+00:00')) if job_data['completed_at'] else None,
                    error_message=job_data['error_message'],
                    input_file_path=job_data.get('input_file_path'),
                    output_file_path=job_data.get('output_file_path'),
                    input_storage_key=job_data['input_storage_key'],
                    output_storage_key=job_data['output_storage_key'],
                    video_info=json.loads(job_data['video_info']) if job_data.get('video_info') else None,
                    processed_video_info=json.loads(job_data['processed_video_info']) if job_data.get('processed_video_info') else None
                )
                
                # Cache in memory
                _processing_jobs[job_id] = job
                return job
                
        except Exception as e:
            print(f"Error loading job from Supabase: {e}")
    
    return None

def get_user_jobs(user_id: str) -> List[ProcessingJob]:
    """Get all jobs for a user from Supabase database"""
    jobs = []
    
    # Get from memory first
    memory_jobs = [job for job in _processing_jobs.values() if job.user_id == user_id]
    jobs.extend(memory_jobs)
    
    # Get from Supabase database
    supabase = get_supabase_client()
    if supabase:
        try:
            result = supabase.table('processing_jobs').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            
            for job_data in result.data:
                job_id = job_data['id']
                
                # Skip if already in memory
                if job_id in _processing_jobs:
                    continue
                    
                job = ProcessingJob(
                    id=job_data['id'],
                    user_id=job_data['user_id'],
                    original_filename=job_data['original_filename'],
                    status=ProcessingStatus(job_data['status']),
                    progress=job_data['progress'],
                    created_at=datetime.fromisoformat(job_data['created_at'].replace('Z', '+00:00')) if job_data['created_at'] else None,
                    completed_at=datetime.fromisoformat(job_data['completed_at'].replace('Z', '+00:00')) if job_data['completed_at'] else None,
                    error_message=job_data['error_message'],
                    input_file_path=job_data.get('input_file_path'),
                    output_file_path=job_data.get('output_file_path'),
                    input_storage_key=job_data['input_storage_key'],
                    output_storage_key=job_data['output_storage_key'],
                    video_info=json.loads(job_data['video_info']) if job_data.get('video_info') else None,
                    processed_video_info=json.loads(job_data['processed_video_info']) if job_data.get('processed_video_info') else None
                )
                
                jobs.append(job)
                # Cache in memory
                _processing_jobs[job_id] = job
                
        except Exception as e:
            print(f"Error loading user jobs from Supabase: {e}")
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x.created_at.replace(tzinfo=None) if x.created_at else datetime.min, reverse=True)
    return jobs