"""
Job-based translation API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from typing import List, Optional
import uuid
import json
import hashlib
from datetime import datetime

from app.models.database import get_db
from app.models.jobs import (
    Job, JobFile, JobEvent, JobArtifact, Glossary,
    JobCreate, JobResponse, JobDetailResponse, JobEventResponse,
    JobStatus, Priority, MediaType, FileStatus
)
from app.services.queue_service import QueueService
from app.services.file_service import FileService

router = APIRouter(tags=["jobs"])

# Initialize services with fallback to mock storage
try:
    from app.services.storage_service import StorageService
    storage_service = StorageService()
except Exception as e:
    print(f"MinIO not available, using mock storage: {e}")
    from app.services.mock_storage_service import MockStorageService
    storage_service = MockStorageService()

# These will be initialized with dependencies in the endpoints
queue_service = None
file_service = None

@router.post("/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"  # Mock user for demo
):
    """Create a new translation job"""

    # Initialize services
    if not queue_service:
        globals()['queue_service'] = QueueService()
    if not file_service:
        globals()['file_service'] = FileService(db)

    # Check if project code already exists for this client
    existing_job = db.query(Job).filter(
        Job.project_code == job_data.project_code,
        Job.client_id == uuid.UUID(current_user_id)
    ).first()

    if existing_job:
        raise HTTPException(
            status_code=409,
            detail=f"Project code '{job_data.project_code}' already exists"
        )

    # Validate glossary if specified
    if job_data.settings.glossary_id:
        glossary = db.query(Glossary).filter(
            Glossary.id == uuid.UUID(job_data.settings.glossary_id)
        ).first()
        if not glossary:
            raise HTTPException(status_code=404, detail="Glossary not found")

    # Create job record
    job = Job(
        project_code=job_data.project_code,
        title=job_data.title or f"{job_data.project_code} - Translation Project",
        client_id=uuid.UUID(current_user_id),
        source_language=job_data.source_language,
        target_languages=job_data.target_languages,
        priority=job_data.priority,
        translation_style=job_data.settings.translation_style,
        glossary_id=uuid.UUID(job_data.settings.glossary_id) if job_data.settings.glossary_id else None,
        settings=job_data.settings.dict(),
        created_by=uuid.UUID(current_user_id)
    )

    db.add(job)
    db.flush()  # Get the job ID

    # Create job files
    for file_data in job_data.files:
        job_file = JobFile(
            job_id=job.id,
            filename=file_data.filename,
            object_key=file_data.object_key,
            mime_type=file_data.mime_type,
            size_bytes=file_data.size,
            checksum=file_data.checksum,
            media_type=file_data.media_type,
            pages=file_data.pages,
            duration_seconds=file_data.duration_seconds
        )
        db.add(job_file)

    # Create initial event
    initial_event = JobEvent(
        job_id=job.id,
        event_type="job.created",
        message=f"Job created with {len(job_data.files)} files",
        meta={
            "file_count": len(job_data.files),
            "total_size": sum(f.size for f in job_data.files),
            "target_languages": job_data.target_languages
        },
        created_by=uuid.UUID(current_user_id)
    )
    db.add(initial_event)

    db.commit()
    db.refresh(job)

    # Queue the job for processing
    background_tasks.add_task(queue_job_for_processing, job.id)

    # Return response
    return JobResponse(
        id=str(job.id),
        project_code=job.project_code,
        title=job.title,
        status=JobStatus(job.status),
        priority=Priority(job.priority),
        source_language=job.source_language,
        target_languages=job.target_languages,
        translation_style=job.translation_style,
        settings=job.settings,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        file_count=len(job_data.files)
    )

@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """List jobs for the current user"""

    query = db.query(Job).filter(Job.client_id == uuid.UUID(current_user_id))

    if status:
        query = query.filter(Job.status == status)
    if priority:
        query = query.filter(Job.priority == priority)

    # Get file count for each job
    query = query.outerjoin(JobFile).group_by(Job.id).add_columns(
        func.count(JobFile.id).label("file_count")
    )

    jobs = query.order_by(desc(Job.created_at)).offset(skip).limit(limit).all()

    return [
        JobResponse(
            id=str(job.Job.id),
            project_code=job.Job.project_code,
            title=job.Job.title,
            status=JobStatus(job.Job.status),
            priority=Priority(job.Job.priority),
            source_language=job.Job.source_language,
            target_languages=job.Job.target_languages,
            translation_style=job.Job.translation_style,
            settings=job.Job.settings,
            created_at=job.Job.created_at,
            updated_at=job.Job.updated_at,
            completed_at=job.Job.completed_at,
            file_count=job.file_count or 0
        )
        for job in jobs
    ]

@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """Get detailed job information"""

    job = db.query(Job).options(
        joinedload(Job.files),
        joinedload(Job.glossary)
    ).filter(
        Job.id == uuid.UUID(job_id),
        Job.client_id == uuid.UUID(current_user_id)
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobDetailResponse(
        id=str(job.id),
        project_code=job.project_code,
        title=job.title,
        status=JobStatus(job.status),
        priority=Priority(job.priority),
        source_language=job.source_language,
        target_languages=job.target_languages,
        translation_style=job.translation_style,
        settings=job.settings,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
        file_count=len(job.files),
        files=[
            {
                "id": str(f.id),
                "filename": f.filename,
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "media_type": MediaType(f.media_type),
                "status": FileStatus(f.status),
                "pages": f.pages,
                "duration_seconds": float(f.duration_seconds) if f.duration_seconds else None,
                "created_at": f.created_at
            }
            for f in job.files
        ]
    )

@router.get("/jobs/{job_id}/events", response_model=List[JobEventResponse])
async def get_job_events(
    job_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """Get events for a job"""

    # Verify job ownership
    job = db.query(Job).filter(
        Job.id == uuid.UUID(job_id),
        Job.client_id == uuid.UUID(current_user_id)
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    events = db.query(JobEvent).filter(
        JobEvent.job_id == uuid.UUID(job_id)
    ).order_by(desc(JobEvent.created_at)).offset(skip).limit(limit).all()

    return [
        JobEventResponse(
            id=str(event.id),
            event_type=event.event_type,
            message=event.message,
            meta=event.meta or {},
            created_at=event.created_at,
            created_by=str(event.created_by) if event.created_by else None
        )
        for event in events
    ]

@router.post("/jobs/{job_id}/upload")
async def upload_job_files(
    job_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """Upload files to a job"""

    # Verify job ownership and status
    job = db.query(Job).filter(
        Job.id == uuid.UUID(job_id),
        Job.client_id == uuid.UUID(current_user_id)
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in [JobStatus.CREATED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail="Cannot upload files to a job that is already processing"
        )

    uploaded_files = []

    for file in files:
        # Validate file
        file_info = await file_service.validate_file(file)

        # Generate object key
        object_key = f"jobs/{job.project_code}/{file.filename}"

        # Upload to storage
        await storage_service.upload_file(file, object_key)

        # Create file record
        job_file = JobFile(
            job_id=job.id,
            filename=file.filename,
            object_key=object_key,
            mime_type=file.content_type,
            size_bytes=file_info['size'],
            checksum=file_info['checksum'],
            media_type=file_info['media_type'],
            pages=file_info.get('pages'),
            duration_seconds=file_info.get('duration_seconds')
        )

        db.add(job_file)
        uploaded_files.append({
            "filename": file.filename,
            "object_key": object_key,
            "size_bytes": file_info['size'],
            "media_type": file_info['media_type']
        })

    # Add upload event
    upload_event = JobEvent(
        job_id=job.id,
        event_type="files.uploaded",
        message=f"Uploaded {len(files)} files",
        meta={"files": uploaded_files},
        created_by=uuid.UUID(current_user_id)
    )
    db.add(upload_event)

    db.commit()

    return {"message": f"Successfully uploaded {len(files)} files", "files": uploaded_files}

@router.post("/jobs/{job_id}/start")
async def start_job_processing(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """Start processing a job"""

    job = db.query(Job).filter(
        Job.id == uuid.UUID(job_id),
        Job.client_id == uuid.UUID(current_user_id)
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.CREATED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start job in status '{job.status}'"
        )

    # Check if job has files
    file_count = db.query(func.count(JobFile.id)).filter(JobFile.job_id == job.id).scalar()
    if file_count == 0:
        raise HTTPException(status_code=400, detail="Job has no files to process")

    # Update job status
    job.status = JobStatus.QUEUED

    # Add start event
    start_event = JobEvent(
        job_id=job.id,
        event_type="job.started",
        message="Job queued for processing",
        created_by=uuid.UUID(current_user_id)
    )
    db.add(start_event)

    db.commit()

    # Queue for processing
    background_tasks.add_task(queue_job_for_processing, job.id)

    return {"message": "Job started successfully", "status": job.status}

@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """Delete a job and all its files"""

    job = db.query(Job).filter(
        Job.id == uuid.UUID(job_id),
        Job.client_id == uuid.UUID(current_user_id)
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in [JobStatus.PARSING, JobStatus.TRANSCRIBING, JobStatus.TRANSLATING]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete job while processing"
        )

    # Delete files from storage
    files = db.query(JobFile).filter(JobFile.job_id == job.id).all()
    for file in files:
        await storage_service.delete_file(file.object_key)

    # Delete artifacts from storage
    artifacts = db.query(JobArtifact).filter(JobArtifact.job_id == job.id).all()
    for artifact in artifacts:
        await storage_service.delete_file(artifact.object_key)

    # Delete job (cascade will handle related records)
    db.delete(job)
    db.commit()

    return {"message": "Job deleted successfully"}

# Helper functions
async def queue_job_for_processing(job_id: uuid.UUID):
    """Queue a job for processing pipeline"""

    message = {
        "event": "job.created",
        "job_id": str(job_id),
        "timestamp": datetime.utcnow().isoformat()
    }

    await queue_service.publish("jobs.events", message)

# Glossary endpoints
@router.post("/glossaries")
async def create_glossary(
    name: str = Form(...),
    language_pair: str = Form(...),  # e.g., "en-es"
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """Upload a glossary file (CSV format)"""

    if file.content_type not in ["text/csv", "application/json"]:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and JSON files are supported"
        )

    # Parse glossary data
    content = await file.read()

    if file.content_type == "text/csv":
        import csv
        import io

        csv_content = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_content))
        glossary_data = {}

        for row in reader:
            if 'term' in row and 'translation' in row:
                glossary_data[row['term']] = row['translation']
    else:
        glossary_data = json.loads(content.decode('utf-8'))

    # Create glossary
    glossary = Glossary(
        client_id=uuid.UUID(current_user_id),
        name=name,
        data=glossary_data,
        language_pair=language_pair
    )

    db.add(glossary)
    db.commit()
    db.refresh(glossary)

    return {
        "id": str(glossary.id),
        "name": glossary.name,
        "language_pair": glossary.language_pair,
        "term_count": len(glossary_data)
    }

@router.get("/glossaries")
async def list_glossaries(
    db: Session = Depends(get_db),
    current_user_id: str = "00000000-0000-0000-0000-000000000001"
):
    """List glossaries for the current user"""

    glossaries = db.query(Glossary).filter(
        Glossary.client_id == uuid.UUID(current_user_id)
    ).order_by(desc(Glossary.created_at)).all()

    return [
        {
            "id": str(g.id),
            "name": g.name,
            "language_pair": g.language_pair,
            "term_count": len(g.data),
            "created_at": g.created_at
        }
        for g in glossaries
    ]

# File upload endpoint
from pydantic import BaseModel

class UploadUrlRequest(BaseModel):
    filename: str
    contentType: str

@router.post("/files/upload-url")
async def get_upload_url(
    request: UploadUrlRequest,
    current_user_id: str = "00000000-0000-0000-0000-000000000001"  # Mock user for demo
):
    """Get presigned URL for file upload"""

    # Force reload

    # Generate object key for the file
    import time
    timestamp = int(time.time())
    object_key = f"uploads/{current_user_id}/{timestamp}_{request.filename}"

    try:
        # Get presigned URL from storage service
        upload_url = storage_service.get_presigned_upload_url(object_key)

        return {
            "uploadUrl": upload_url,
            "objectKey": object_key
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate upload URL: {str(e)}"
        )

# Mock upload endpoint for when using mock storage
@router.put("/mock-upload/{object_key:path}")
async def mock_upload_file(
    object_key: str,
    file: UploadFile = File(...)
):
    """Handle file upload to mock storage"""
    try:
        # Use the mock storage service to handle the upload
        upload_result = await storage_service.upload_file(file, object_key)

        return {
            "message": "File uploaded successfully",
            "object_key": object_key,
            "size": file.size,
            "content_type": file.content_type
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )