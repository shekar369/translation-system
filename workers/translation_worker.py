"""
Translation Worker - Translates parsed content using MT models or cloud services
"""
import asyncio
import logging
import uuid
import json
import tempfile
import os
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.jobs import JobFile, JobArtifact, Glossary
from app.services.queue_service import QueueService, JobEvents
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class TranslationWorker:
    def __init__(self):
        self.queue_service = QueueService()
        self.storage_service = StorageService()
        self.db = next(get_db())

    async def start(self):
        """Start the translation worker"""
        logger.info("Starting Translation Worker")
        await self.queue_service.consume("translation", self.handle_translate_request)

    async def handle_translate_request(self, message: dict):
        """Handle translation request"""
        job_id = message.get("job_id")
        file_id = message.get("file_id")
        source_language = message.get("source_language")
        target_language = message.get("target_language")
        translation_style = message.get("translation_style", "neutral")
        glossary_id = message.get("glossary_id")
        settings = message.get("settings", {})

        logger.info(f"Translating file {file_id} from {source_language} to {target_language}")

        try:
            # Get the parsed content
            parsed_artifact = self.db.query(JobArtifact).filter(
                JobArtifact.job_file_id == uuid.UUID(file_id),
                JobArtifact.artifact_type == "parsed"
            ).first()

            if not parsed_artifact:
                raise ValueError(f"No parsed content found for file {file_id}")

            # Download parsed content
            parsed_content = await self.download_parsed_content(parsed_artifact.object_key)

            # Load glossary if specified
            glossary_terms = {}
            if glossary_id:
                glossary = self.db.query(Glossary).filter(Glossary.id == uuid.UUID(glossary_id)).first()
                if glossary:
                    glossary_terms = glossary.data

            # Translate the content
            translated_content = await self.translate_content(
                parsed_content,
                source_language,
                target_language,
                translation_style,
                glossary_terms,
                settings
            )

            # Save translated content
            translated_object_key = f"translations/{job_id}/{file_id}_{target_language}.json"
            await self.save_translated_content(translated_content, translated_object_key)

            # Create translation artifact
            artifact = JobArtifact(
                job_id=uuid.UUID(job_id),
                job_file_id=uuid.UUID(file_id),
                artifact_type="translation",
                language_code=target_language,
                object_key=translated_object_key
            )
            self.db.add(artifact)
            self.db.commit()

            # Notify orchestrator
            response = {
                "event": JobEvents.TRANSLATING_COMPLETED,
                "job_id": job_id,
                "file_id": file_id,
                "target_language": target_language,
                "success": True,
                "translated_object_key": translated_object_key
            }
            await self.queue_service.publish("events", response)

            logger.info(f"Successfully translated file {file_id} to {target_language}")

        except Exception as e:
            logger.error(f"Error translating file {file_id}: {e}")

            # Notify orchestrator of failure
            response = {
                "event": JobEvents.TRANSLATING_FAILED,
                "job_id": job_id,
                "file_id": file_id,
                "target_language": target_language,
                "success": False,
                "error": str(e)
            }
            await self.queue_service.publish("events", response)

    async def download_parsed_content(self, object_key: str) -> dict:
        """Download and parse JSON content from storage"""
        file_stream = await self.storage_service.download_file(object_key)
        content = file_stream.read().decode('utf-8')
        return json.loads(content)

    async def translate_content(
        self,
        parsed_content: dict,
        source_lang: str,
        target_lang: str,
        style: str,
        glossary: dict,
        settings: dict
    ) -> dict:
        """Translate parsed content based on document type"""

        doc_type = parsed_content.get("document_type")
        privacy_mode = settings.get("privacy", "allow_cloud")

        if doc_type == "pdf":
            return await self.translate_pdf_content(parsed_content, source_lang, target_lang, style, glossary, privacy_mode)
        elif doc_type == "docx":
            return await self.translate_docx_content(parsed_content, source_lang, target_lang, style, glossary, privacy_mode)
        elif doc_type == "pptx":
            return await self.translate_pptx_content(parsed_content, source_lang, target_lang, style, glossary, privacy_mode)
        elif doc_type == "text":
            return await self.translate_text_content(parsed_content, source_lang, target_lang, style, glossary, privacy_mode)
        else:
            raise ValueError(f"Unsupported document type for translation: {doc_type}")

    async def translate_pdf_content(self, parsed_content: dict, source_lang: str, target_lang: str, style: str, glossary: dict, privacy_mode: str) -> dict:
        """Translate PDF content while preserving structure"""
        translated_pages = []

        for page in parsed_content.get("pages", []):
            text = page.get("text", "")
            if text.strip():
                translated_text = await self.translate_text(text, source_lang, target_lang, style, glossary, privacy_mode)
                translated_pages.append({
                    "page_number": page["page_number"],
                    "original_text": text,
                    "translated_text": translated_text,
                    "word_count": len(translated_text.split()),
                    "char_count": len(translated_text)
                })
            else:
                translated_pages.append(page)

        return {
            "document_type": "pdf",
            "source_language": source_lang,
            "target_language": target_lang,
            "translation_style": style,
            "total_pages": len(translated_pages),
            "pages": translated_pages,
            "metadata": {
                "total_words": sum(p.get("word_count", 0) for p in translated_pages),
                "total_chars": sum(p.get("char_count", 0) for p in translated_pages)
            }
        }

    async def translate_docx_content(self, parsed_content: dict, source_lang: str, target_lang: str, style: str, glossary: dict, privacy_mode: str) -> dict:
        """Translate DOCX content while preserving structure"""
        translated_paragraphs = []

        for para in parsed_content.get("paragraphs", []):
            text = para.get("text", "")
            if text.strip():
                translated_text = await self.translate_text(text, source_lang, target_lang, style, glossary, privacy_mode)
                translated_paragraphs.append({
                    "paragraph_number": para["paragraph_number"],
                    "original_text": text,
                    "translated_text": translated_text,
                    "style": para.get("style", "Normal")
                })
            else:
                translated_paragraphs.append(para)

        return {
            "document_type": "docx",
            "source_language": source_lang,
            "target_language": target_lang,
            "translation_style": style,
            "paragraphs": translated_paragraphs,
            "metadata": {
                "total_paragraphs": len(translated_paragraphs),
                "total_words": sum(len(p.get("translated_text", "").split()) for p in translated_paragraphs)
            }
        }

    async def translate_pptx_content(self, parsed_content: dict, source_lang: str, target_lang: str, style: str, glossary: dict, privacy_mode: str) -> dict:
        """Translate PowerPoint content while preserving structure"""
        translated_slides = []

        for slide in parsed_content.get("slides", []):
            translated_shapes = []
            for shape in slide.get("shapes", []):
                text = shape.get("text", "")
                if text.strip():
                    translated_text = await self.translate_text(text, source_lang, target_lang, style, glossary, privacy_mode)
                    translated_shapes.append({
                        "type": shape["type"],
                        "original_text": text,
                        "translated_text": translated_text
                    })
                else:
                    translated_shapes.append(shape)

            translated_slides.append({
                "slide_number": slide["slide_number"],
                "shapes": translated_shapes
            })

        return {
            "document_type": "pptx",
            "source_language": source_lang,
            "target_language": target_lang,
            "translation_style": style,
            "slides": translated_slides,
            "metadata": {
                "total_slides": len(translated_slides)
            }
        }

    async def translate_text_content(self, parsed_content: dict, source_lang: str, target_lang: str, style: str, glossary: dict, privacy_mode: str) -> dict:
        """Translate plain text content"""
        original_text = parsed_content.get("content", "")
        if original_text.strip():
            translated_text = await self.translate_text(original_text, source_lang, target_lang, style, glossary, privacy_mode)
        else:
            translated_text = original_text

        return {
            "document_type": "text",
            "source_language": source_lang,
            "target_language": target_lang,
            "translation_style": style,
            "original_content": original_text,
            "translated_content": translated_text,
            "metadata": {
                "original_words": len(original_text.split()),
                "translated_words": len(translated_text.split())
            }
        }

    async def translate_text(self, text: str, source_lang: str, target_lang: str, style: str, glossary: dict, privacy_mode: str) -> str:
        """Translate a single text string"""
        if not text.strip():
            return text

        # Apply glossary pre-processing
        processed_text = self.apply_glossary_preprocessing(text, glossary)

        # Choose translation method based on privacy mode
        if privacy_mode == "on-prem_only":
            translated_text = await self.translate_with_local_model(processed_text, source_lang, target_lang, style)
        else:
            translated_text = await self.translate_with_cloud_service(processed_text, source_lang, target_lang, style)

        # Apply glossary post-processing
        final_text = self.apply_glossary_postprocessing(translated_text, glossary, source_lang, target_lang)

        return final_text

    async def translate_with_local_model(self, text: str, source_lang: str, target_lang: str, style: str) -> str:
        """Translate using local on-premises model (NLLB, Marian, etc.)"""
        try:
            # In production, use transformers with NLLB or Marian models
            from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

            # Use Helsinki-NLP models for demo (smaller and faster)
            model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"

            # For demo, use a simple mock translation
            logger.info(f"Mock local translation: {source_lang} -> {target_lang}")
            return f"[LOCAL MT] Translated from {source_lang} to {target_lang}: {text}"

        except Exception as e:
            logger.error(f"Local model translation failed: {e}")
            return await self.mock_translation(text, source_lang, target_lang, "local")

    async def translate_with_cloud_service(self, text: str, source_lang: str, target_lang: str, style: str) -> str:
        """Translate using cloud service (Google Translate, DeepL, etc.)"""
        try:
            # In production, use Google Translate API, DeepL API, etc.
            # For demo, use existing Google Translator
            from googletrans import Translator

            translator = Translator()
            result = translator.translate(
                text,
                src=source_lang if source_lang != "auto" else None,
                dest=target_lang
            )

            return result.text

        except Exception as e:
            logger.error(f"Cloud service translation failed: {e}")
            return await self.mock_translation(text, source_lang, target_lang, "cloud")

    async def mock_translation(self, text: str, source_lang: str, target_lang: str, engine: str) -> str:
        """Mock translation for demo purposes"""
        return f"[{engine.upper()} MT] Mock translation from {source_lang} to {target_lang}: {text}"

    def apply_glossary_preprocessing(self, text: str, glossary: dict) -> str:
        """Apply glossary terms before translation (for context)"""
        if not glossary:
            return text

        # Simple term replacement - in production, use more sophisticated NLP
        processed_text = text
        for source_term, target_term in glossary.items():
            # Mark terms for forced translation
            processed_text = processed_text.replace(source_term, f"<<{source_term}>>")

        return processed_text

    def apply_glossary_postprocessing(self, translated_text: str, glossary: dict, source_lang: str, target_lang: str) -> str:
        """Apply glossary terms after translation"""
        if not glossary:
            return translated_text

        # Replace marked terms with glossary translations
        processed_text = translated_text
        for source_term, target_term in glossary.items():
            processed_text = processed_text.replace(f"<<{source_term}>>", target_term)

        return processed_text

    async def save_translated_content(self, content: dict, object_key: str):
        """Save translated content as JSON"""
        import io

        json_content = json.dumps(content, indent=2, ensure_ascii=False).encode('utf-8')

        class MockFile:
            def __init__(self, content, filename):
                self.file = io.BytesIO(content)
                self.size = len(content)
                self.content_type = "application/json"
                self.filename = filename

        mock_file = MockFile(json_content, "translation.json")
        await self.storage_service.upload_file(mock_file, object_key)

async def main():
    """Main entry point for the translation worker"""
    worker = TranslationWorker()
    await worker.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())