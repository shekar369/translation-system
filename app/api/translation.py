from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.models.database import get_db, TranslationJob, Document
from app.services.translation_service import TranslationService
from app.workers.translation_worker import translate_document_task
from pydantic import BaseModel
from typing import List, Dict, Any
import os

router = APIRouter()

class TranslationRequest(BaseModel):
    document_id: int
    source_language: str
    target_language: str

class TranslationResponse(BaseModel):
    job_id: int
    status: str
    message: str

class JobStatus(BaseModel):
    id: int
    document_id: int
    source_language: str
    target_language: str
    status: str
    created_at: str
    completed_at: str = None
    processing_time: float = None
    result_path: str = None
    error_message: str = None

    class Config:
        from_attributes = True

@router.post("/", response_model=TranslationResponse)
async def translate_document(
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from app.workers.translation_worker import translate_document_sync

    translation_service = TranslationService(db)

    # Create translation job
    job = translation_service.create_translation_job(
        document_id=request.document_id,
        source_language=request.source_language,
        target_language=request.target_language,
        user_id=1  # TODO: Get from authenticated user
    )

    # Process translation synchronously for demo (without Celery/Redis)
    background_tasks.add_task(
        translate_document_sync,
        job.id,
        request.document_id,
        request.source_language,
        request.target_language
    )

    return TranslationResponse(
        job_id=job.id,
        status="processing",
        message="Translation job started successfully"
    )

@router.get("/jobs")
async def get_translation_jobs(db: Session = Depends(get_db)):
    jobs = db.query(TranslationJob).order_by(TranslationJob.created_at.desc()).all()

    # Convert to dict format with string dates
    jobs_data = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "document_id": job.document_id,
            "source_language": job.source_language,
            "target_language": job.target_language,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "processing_time": job.processing_time,
            "result_path": job.result_path,
            "error_message": job.error_message
        }
        jobs_data.append(job_dict)

    return jobs_data

@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_translation_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")
    return job

@router.get("/languages")
async def get_supported_languages():
    return {
        "languages": {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi"
        }
    }

@router.get("/jobs/{job_id}/download")
async def download_translation(job_id: int, db: Session = Depends(get_db)):
    """Download translated file"""
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Translation not completed yet")

    if not job.result_path or not os.path.exists(job.result_path):
        raise HTTPException(status_code=404, detail="Translation file not found")

    filename = f"translation_{job_id}_{job.source_language}_to_{job.target_language}.txt"
    return FileResponse(
        job.result_path,
        media_type='text/plain',
        filename=filename
    )

@router.post("/jobs/{job_id}/process")
async def process_translation_job(job_id: int, db: Session = Depends(get_db)):
    """Manually process a translation job for demo"""
    from app.workers.translation_worker import translate_document_sync

    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")

    if job.status == "completed":
        return {"message": "Job already completed", "job_id": job_id}

    # Process the translation
    result = translate_document_sync(
        job.id,
        job.document_id,
        job.source_language,
        job.target_language
    )

    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    else:
        return {"status": "completed", "job_id": job_id, "result_path": result["result_path"]}

@router.delete("/jobs/{job_id}")
async def delete_translation_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a translation job and its result file"""
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")

    # Delete result file if it exists
    if job.result_path and os.path.exists(job.result_path):
        try:
            os.remove(job.result_path)
        except Exception as e:
            print(f"Error deleting file {job.result_path}: {e}")

    # Delete job from database
    db.delete(job)
    db.commit()

    return {"message": "Translation job deleted successfully", "job_id": job_id}

@router.post("/jobs/{job_id}/rerun")
async def rerun_translation_job(job_id: int, db: Session = Depends(get_db)):
    """Re-run a translation job"""
    from app.workers.translation_worker import translate_document_sync

    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")

    # Reset job status
    job.status = "pending"
    job.completed_at = None
    job.processing_time = None
    job.error_message = None

    # Delete old result file if it exists
    if job.result_path and os.path.exists(job.result_path):
        try:
            os.remove(job.result_path)
        except Exception as e:
            print(f"Error deleting old result file: {e}")

    job.result_path = None
    db.commit()

    # Process the translation
    result = translate_document_sync(
        job.id,
        job.document_id,
        job.source_language,
        job.target_language
    )

    if "error" in result:
        return {"status": "failed", "error": result["error"]}
    else:
        return {"status": "completed", "job_id": job_id, "result_path": result["result_path"]}

@router.get("/jobs/{job_id}/preview")
async def preview_translation(job_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get original and translated content for preview"""
    job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Translation job not found")

    # Get document info
    document = db.query(Document).filter(Document.id == job.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Original document not found")

    # Read original content
    original_content = ""
    if document.original_path and os.path.exists(document.original_path):
        try:
            # Extract text from original document
            from app.workers.translation_worker import extract_text_from_file
            original_content = extract_text_from_file(document.original_path, document.file_type)
        except Exception as e:
            original_content = f"Error reading original file: {str(e)}"
    else:
        original_content = "Original file not found"

    # Read translated content
    translated_content = ""
    if job.status == "completed" and job.result_path and os.path.exists(job.result_path):
        try:
            with open(job.result_path, 'r', encoding='utf-8') as f:
                translated_content = f.read()
        except Exception as e:
            translated_content = f"Error reading translation: {str(e)}"
    elif job.status == "failed":
        translated_content = f"Translation failed: {job.error_message or 'Unknown error'}"
    else:
        translated_content = "Translation not completed yet"

    return {
        "job_id": job_id,
        "document_name": document.filename,
        "source_language": job.source_language,
        "target_language": job.target_language,
        "status": job.status,
        "original_content": original_content[:5000],  # Limit content for preview
        "translated_content": translated_content[:5000],  # Limit content for preview
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }
