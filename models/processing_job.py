from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

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
    
    def set_input_paths(self, local_path: str, storage_key: str):
        self.input_file_path = local_path
        self.input_storage_key = storage_key
    
    def set_video_info(self, video_info: Dict[str, Any]):
        self.video_info = video_info
    
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

def save_processing_job(job: ProcessingJob):
    _processing_jobs[job.id] = job

def get_processing_job(job_id: str) -> Optional[ProcessingJob]:
    return _processing_jobs.get(job_id)

def get_user_jobs(user_id: str) -> List[ProcessingJob]:
    return [job for job in _processing_jobs.values() if job.user_id == user_id]