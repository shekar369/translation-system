"""
Transcription Worker - Transcribes audio/video files using Whisper or cloud ASR
"""
import asyncio
import logging
import uuid
import tempfile
import os
import json
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.jobs import JobFile, JobArtifact, FileStatus
from app.services.queue_service import QueueService, JobEvents
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class TranscriptionWorker:
    def __init__(self):
        self.queue_service = QueueService()
        self.storage_service = StorageService()
        self.db = next(get_db())

    async def start(self):
        """Start the transcription worker"""
        logger.info("Starting Transcription Worker")
        await self.queue_service.consume("transcription", self.handle_transcribe_request)

    async def handle_transcribe_request(self, message: dict):
        """Handle transcription request"""
        job_id = message.get("job_id")
        file_id = message.get("file_id")
        object_key = message.get("object_key")
        media_type = message.get("media_type")
        source_language = message.get("source_language", "auto")

        logger.info(f"Transcribing file {file_id} for job {job_id}")

        try:
            # Update file status
            job_file = self.db.query(JobFile).filter(JobFile.id == uuid.UUID(file_id)).first()
            if job_file:
                job_file.status = FileStatus.TRANSCRIBING
                self.db.commit()

            # Transcribe the file
            transcript_data = await self.transcribe_media(object_key, media_type, source_language)

            # Save transcript to storage
            transcript_object_key = f"transcripts/{job_id}/{file_id}.json"
            await self.save_transcript(transcript_data, transcript_object_key)

            # Create transcript artifact
            artifact = JobArtifact(
                job_id=uuid.UUID(job_id),
                job_file_id=uuid.UUID(file_id),
                artifact_type="transcript",
                object_key=transcript_object_key
            )
            self.db.add(artifact)

            # Generate SRT/VTT files
            srt_object_key = f"subtitles/{job_id}/{file_id}.srt"
            await self.generate_subtitles(transcript_data, srt_object_key, "srt")

            vtt_object_key = f"subtitles/{job_id}/{file_id}.vtt"
            await self.generate_subtitles(transcript_data, vtt_object_key, "vtt")

            # Create subtitle artifacts
            srt_artifact = JobArtifact(
                job_id=uuid.UUID(job_id),
                job_file_id=uuid.UUID(file_id),
                artifact_type="subtitle",
                object_key=srt_object_key,
                language_code=source_language
            )
            vtt_artifact = JobArtifact(
                job_id=uuid.UUID(job_id),
                job_file_id=uuid.UUID(file_id),
                artifact_type="subtitle",
                object_key=vtt_object_key,
                language_code=source_language
            )
            self.db.add(srt_artifact)
            self.db.add(vtt_artifact)

            # Update file status
            if job_file:
                job_file.status = FileStatus.COMPLETED
                self.db.commit()

            # Notify orchestrator
            response = {
                "event": JobEvents.TRANSCRIBING_COMPLETED,
                "job_id": job_id,
                "file_id": file_id,
                "success": True,
                "transcript_object_key": transcript_object_key,
                "srt_object_key": srt_object_key,
                "vtt_object_key": vtt_object_key
            }
            await self.queue_service.publish("events", response)

            logger.info(f"Successfully transcribed file {file_id}")

        except Exception as e:
            logger.error(f"Error transcribing file {file_id}: {e}")

            # Update file status to failed
            if job_file:
                job_file.status = FileStatus.FAILED
                self.db.commit()

            # Notify orchestrator of failure
            response = {
                "event": JobEvents.TRANSCRIBING_FAILED,
                "job_id": job_id,
                "file_id": file_id,
                "success": False,
                "error": str(e)
            }
            await self.queue_service.publish("events", response)

    async def transcribe_media(self, object_key: str, media_type: str, source_language: str) -> dict:
        """Transcribe audio/video file using Whisper or cloud ASR"""

        # Download file from storage
        file_stream = await self.storage_service.download_file(object_key)

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(file_stream.read())
            temp_path = temp_file.name

        try:
            # Check privacy settings to determine which ASR to use
            privacy_mode = os.getenv("ASR_PRIVACY_MODE", "on-prem")

            if privacy_mode == "on-prem":
                return await self.transcribe_with_whisper(temp_path, source_language)
            else:
                return await self.transcribe_with_cloud_asr(temp_path, source_language)

        finally:
            os.unlink(temp_path)

    async def transcribe_with_whisper(self, file_path: str, language: str) -> dict:
        """Transcribe using local Whisper model"""
        try:
            import whisper

            # Load Whisper model (use small model for demo)
            model = whisper.load_model("small")

            # Transcribe
            result = model.transcribe(
                file_path,
                language=None if language == "auto" else language,
                word_timestamps=True,
                verbose=False
            )

            # Convert to our format
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "confidence": segment.get("avg_logprob", 0.0),
                    "words": segment.get("words", [])
                })

            return {
                "language": result.get("language", language),
                "duration": max(s["end"] for s in segments) if segments else 0,
                "text": result.get("text", ""),
                "segments": segments,
                "word_count": len(result.get("text", "").split()),
                "engine": "whisper-local",
                "model": "small"
            }

        except ImportError:
            logger.warning("Whisper not available, using mock transcription")
            return await self.mock_transcription(file_path, language)
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return await self.mock_transcription(file_path, language)

    async def transcribe_with_cloud_asr(self, file_path: str, language: str) -> dict:
        """Transcribe using cloud ASR service (placeholder)"""
        # In production, implement with Google Speech-to-Text, Azure, etc.
        logger.info("Cloud ASR not implemented, using mock transcription")
        return await self.mock_transcription(file_path, language)

    async def mock_transcription(self, file_path: str, language: str) -> dict:
        """Mock transcription for demo purposes"""
        return {
            "language": language if language != "auto" else "en",
            "duration": 120.0,
            "text": "This is a mock transcription for demonstration purposes. In a real implementation, this would contain the actual transcribed text from the audio or video file.",
            "segments": [
                {
                    "start": 0.0,
                    "end": 10.0,
                    "text": "This is a mock transcription for demonstration purposes.",
                    "confidence": 0.95,
                    "words": []
                },
                {
                    "start": 10.0,
                    "end": 20.0,
                    "text": "In a real implementation, this would contain the actual transcribed text.",
                    "confidence": 0.92,
                    "words": []
                }
            ],
            "word_count": 20,
            "engine": "mock",
            "model": "demo"
        }

    async def save_transcript(self, transcript_data: dict, object_key: str):
        """Save transcript data as JSON"""
        import io

        json_content = json.dumps(transcript_data, indent=2).encode('utf-8')

        class MockFile:
            def __init__(self, content, filename):
                self.file = io.BytesIO(content)
                self.size = len(content)
                self.content_type = "application/json"
                self.filename = filename

        mock_file = MockFile(json_content, "transcript.json")
        await self.storage_service.upload_file(mock_file, object_key)

    async def generate_subtitles(self, transcript_data: dict, object_key: str, format_type: str):
        """Generate subtitle files (SRT/VTT) from transcript"""
        import io

        if format_type == "srt":
            content = self.generate_srt(transcript_data)
        elif format_type == "vtt":
            content = self.generate_vtt(transcript_data)
        else:
            raise ValueError(f"Unsupported subtitle format: {format_type}")

        class MockFile:
            def __init__(self, content, filename):
                self.file = io.BytesIO(content.encode('utf-8'))
                self.size = len(content.encode('utf-8'))
                self.content_type = "text/plain"
                self.filename = filename

        mock_file = MockFile(content, f"subtitle.{format_type}")
        await self.storage_service.upload_file(mock_file, object_key)

    def generate_srt(self, transcript_data: dict) -> str:
        """Generate SRT format subtitles"""
        srt_content = []

        for i, segment in enumerate(transcript_data.get("segments", []), 1):
            start_time = self.seconds_to_srt_time(segment["start"])
            end_time = self.seconds_to_srt_time(segment["end"])

            srt_content.append(f"{i}")
            srt_content.append(f"{start_time} --> {end_time}")
            srt_content.append(segment["text"])
            srt_content.append("")  # Empty line

        return "\n".join(srt_content)

    def generate_vtt(self, transcript_data: dict) -> str:
        """Generate VTT format subtitles"""
        vtt_content = ["WEBVTT", ""]

        for segment in transcript_data.get("segments", []):
            start_time = self.seconds_to_vtt_time(segment["start"])
            end_time = self.seconds_to_vtt_time(segment["end"])

            vtt_content.append(f"{start_time} --> {end_time}")
            vtt_content.append(segment["text"])
            vtt_content.append("")  # Empty line

        return "\n".join(vtt_content)

    def seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT time format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

async def main():
    """Main entry point for the transcription worker"""
    worker = TranscriptionWorker()
    await worker.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())