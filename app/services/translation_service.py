from sqlalchemy.orm import Session
from app.models.database import TranslationJob
from datetime import datetime

class TranslationService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_translation_job(self, document_id: int, source_language: str, 
                             target_language: str, user_id: int):
        job = TranslationJob(
            document_id=document_id,
            user_id=user_id,
            source_language=source_language,
            target_language=target_language,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def get_translation_job(self, job_id: int):
        return self.db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
    
    def update_job_status(self, job_id: int, status: str, result_path: str = None, 
                         error_message: str = None):
        job = self.get_translation_job(job_id)
        if job:
            job.status = status
            if result_path:
                job.result_path = result_path
            if error_message:
                job.error_message = error_message
            if status == "completed":
                job.completed_at = datetime.utcnow()
                job.processing_time = (job.completed_at - job.created_at).total_seconds()
            
            self.db.commit()
            self.db.refresh(job)
        
        return job
