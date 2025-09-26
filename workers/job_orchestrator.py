"""
Job Orchestrator - Main worker that coordinates the translation pipeline
"""
import asyncio
import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.jobs import Job, JobFile, JobEvent, JobArtifact, JobStatus, FileStatus
from app.services.queue_service import QueueService, JobEvents
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class JobOrchestrator:
    def __init__(self):
        self.queue_service = QueueService()
        self.storage_service = StorageService()
        self.db = next(get_db())

    async def start(self):
        """Start the job orchestrator worker"""
        logger.info("Starting Job Orchestrator Worker")

        # Start consuming messages from the jobs.events stream
        await self.queue_service.consume("events", self.handle_job_event)

    async def handle_job_event(self, message: dict):
        """Handle job events and orchestrate the pipeline"""
        event_type = message.get("event")
        job_id = message.get("job_id")

        if not job_id:
            logger.error(f"No job_id in message: {message}")
            return

        try:
            job_uuid = uuid.UUID(job_id)
            job = self.db.query(Job).filter(Job.id == job_uuid).first()

            if not job:
                logger.error(f"Job {job_id} not found")
                return

            logger.info(f"Processing event {event_type} for job {job_id}")

            if event_type == JobEvents.JOB_CREATED:
                await self.handle_job_created(job)
            elif event_type == JobEvents.PARSING_COMPLETED:
                await self.handle_parsing_completed(job, message)
            elif event_type == JobEvents.TRANSCRIBING_COMPLETED:
                await self.handle_transcribing_completed(job, message)
            elif event_type == JobEvents.TRANSLATING_COMPLETED:
                await self.handle_translating_completed(job, message)
            elif event_type == JobEvents.POSTPROCESSING_COMPLETED:
                await self.handle_postprocessing_completed(job, message)
            else:
                logger.debug(f"Unhandled event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling event {event_type} for job {job_id}: {e}")
            await self.handle_job_failure(job_uuid, str(e))

    async def handle_job_created(self, job: Job):
        """Handle job.created event - start the pipeline"""
        logger.info(f"Starting pipeline for job {job.id}")

        # Update job status
        job.status = JobStatus.PARSING
        self.add_event(job.id, JobEvents.PARSING_STARTED, "Starting file parsing")
        self.db.commit()

        # Queue parsing for each file
        for file in job.files:
            message = {
                "event": "file.parse",
                "job_id": str(job.id),
                "file_id": str(file.id),
                "object_key": file.object_key,
                "media_type": file.media_type,
                "mime_type": file.mime_type
            }
            await self.queue_service.publish("parsing", message)

    async def handle_parsing_completed(self, job: Job, message: dict):
        """Handle parsing completion for a file"""
        file_id = message.get("file_id")
        success = message.get("success", False)

        if file_id:
            file_uuid = uuid.UUID(file_id)
            job_file = self.db.query(JobFile).filter(JobFile.id == file_uuid).first()

            if job_file:
                if success:
                    job_file.status = FileStatus.COMPLETED
                    # Create parsed artifact
                    artifact = JobArtifact(
                        job_id=job.id,
                        job_file_id=job_file.id,
                        artifact_type="parsed",
                        object_key=message.get("parsed_object_key")
                    )
                    self.db.add(artifact)
                else:
                    job_file.status = FileStatus.FAILED

        # Check if all files are parsed
        if self.all_files_completed(job, FileStatus.COMPLETED):
            logger.info(f"All files parsed for job {job.id}, starting transcription")
            job.status = JobStatus.TRANSCRIBING
            self.add_event(job.id, JobEvents.TRANSCRIBING_STARTED, "Starting transcription")

            # Queue transcription for audio/video files
            for file in job.files:
                if file.media_type in ['audio', 'video']:
                    message = {
                        "event": "file.transcribe",
                        "job_id": str(job.id),
                        "file_id": str(file.id),
                        "object_key": file.object_key,
                        "media_type": file.media_type,
                        "source_language": job.source_language
                    }
                    await self.queue_service.publish("transcription", message)

            # If no audio/video files, skip to translation
            has_media = any(f.media_type in ['audio', 'video'] for f in job.files)
            if not has_media:
                await self.start_translation(job)

        self.db.commit()

    async def handle_transcribing_completed(self, job: Job, message: dict):
        """Handle transcription completion"""
        # Similar logic to parsing - check if all media files are transcribed
        await self.start_translation(job)

    async def start_translation(self, job: Job):
        """Start translation phase"""
        logger.info(f"Starting translation for job {job.id}")

        job.status = JobStatus.TRANSLATING
        self.add_event(job.id, JobEvents.TRANSLATING_STARTED, "Starting translation")

        # Queue translation for each target language
        for target_lang in job.target_languages:
            for file in job.files:
                message = {
                    "event": "file.translate",
                    "job_id": str(job.id),
                    "file_id": str(file.id),
                    "source_language": job.source_language,
                    "target_language": target_lang,
                    "translation_style": job.translation_style,
                    "glossary_id": str(job.glossary_id) if job.glossary_id else None,
                    "settings": job.settings
                }
                await self.queue_service.publish("translation", message)

        self.db.commit()

    async def handle_translating_completed(self, job: Job, message: dict):
        """Handle translation completion"""
        # Check if all translations are done
        total_expected = len(job.files) * len(job.target_languages)
        completed_translations = self.db.query(JobArtifact).filter(
            JobArtifact.job_id == job.id,
            JobArtifact.artifact_type == "translation"
        ).count()

        if completed_translations >= total_expected:
            logger.info(f"All translations completed for job {job.id}, starting post-processing")
            job.status = JobStatus.POSTPROCESSING
            self.add_event(job.id, JobEvents.POSTPROCESSING_STARTED, "Starting post-processing")

            # Queue post-processing
            message = {
                "event": "job.postprocess",
                "job_id": str(job.id),
                "target_languages": job.target_languages,
                "delivery_formats": job.settings.get("delivery_formats", []),
                "settings": job.settings
            }
            await self.queue_service.publish("postprocessing", message)

        self.db.commit()

    async def handle_postprocessing_completed(self, job: Job, message: dict):
        """Handle post-processing completion"""
        success = message.get("success", False)

        if success:
            # Check if human review is required
            if job.settings.get("human_review", False):
                job.status = JobStatus.REVIEW
                self.add_event(job.id, JobEvents.REVIEW_REQUIRED, "Job requires human review")
            else:
                # Job completed
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                self.add_event(job.id, JobEvents.JOB_COMPLETED, "Job completed successfully")
        else:
            await self.handle_job_failure(job.id, "Post-processing failed")

        self.db.commit()

    async def handle_job_failure(self, job_id: uuid.UUID, error_message: str):
        """Handle job failure"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.FAILED
            self.add_event(job.id, JobEvents.JOB_FAILED, f"Job failed: {error_message}")
            self.db.commit()

    def all_files_completed(self, job: Job, target_status: FileStatus) -> bool:
        """Check if all files have reached the target status"""
        for file in job.files:
            if file.status != target_status:
                return False
        return True

    def add_event(self, job_id: uuid.UUID, event_type: str, message: str):
        """Add an event to the job log"""
        event = JobEvent(
            job_id=job_id,
            event_type=event_type,
            message=message,
            meta={}
        )
        self.db.add(event)

async def main():
    """Main entry point for the orchestrator worker"""
    orchestrator = JobOrchestrator()
    await orchestrator.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())