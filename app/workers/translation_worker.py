from celery import current_app
from app.workers.celery_app import celery_app
from app.models.database import SessionLocal, TranslationJob, Document
from app.services.translation_service import TranslationService
import os
import datetime

# Simple translation function (you can enhance this with better APIs)
def simple_translate(text, source_lang, target_lang):
    """Simple translation - replace with Google Translate API or DeepL"""
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        # Fallback - just add prefix for demo
        return f"[{target_lang.upper()}] {text}"

def extract_text_from_file(file_path, file_type):
    """Extract text content from various file formats"""
    try:
        if file_type.lower() == 'pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                return "PDF processing requires PyPDF2. Install with: pip install PyPDF2"
                
        elif file_type.lower() == 'docx':
            try:
                from docx import Document as DocxDocument
                doc = DocxDocument(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                return "DOCX processing requires python-docx. Install with: pip install python-docx"
            
        elif file_type.lower() in ['txt', 'rtf']:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        else:
            return f"Unsupported file type: {file_type}"
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"

@celery_app.task
def translate_document_task(job_id, document_id, source_lang, target_lang):
    """Background task to translate documents"""
    db = SessionLocal()
    
    try:
        # Get job and document from database
        job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not job or not document:
            return {"error": "Job or document not found"}
        
        # Update job status
        job.status = "processing"
        db.commit()
        
        # Extract text based on file type
        text_content = extract_text_from_file(document.original_path, document.file_type)
        
        if not text_content or text_content.startswith("Error"):
            job.status = "failed"
            job.error_message = text_content or "Could not extract text from document"
            db.commit()
            return {"error": job.error_message}
        
        # Translate text
        translated_text = simple_translate(text_content, source_lang, target_lang)
        
        # Save translated content
        os.makedirs("storage/translations", exist_ok=True)
        result_filename = f"translated_{document.id}_{source_lang}_to_{target_lang}.txt"
        result_path = os.path.join("storage", "translations", result_filename)
        
        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(f"Original ({source_lang}) to {target_lang}\n")
            f.write("="*50 + "\n\n")
            f.write(translated_text)
        
        # Update job with results
        job.status = "completed"
        job.result_path = result_path
        job.completed_at = datetime.datetime.utcnow()
        job.processing_time = (job.completed_at - job.created_at).total_seconds()
        
        document.processed = True
        
        db.commit()
        
        return {
            "status": "success",
            "job_id": job_id,
            "result_path": result_path,
            "processing_time": job.processing_time
        }
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        return {"error": str(e)}
    
    finally:
        db.close()

# Test task
@celery_app.task
def test_task():
    return "Hello from Celery worker!"

def translate_document_sync(job_id, document_id, source_lang, target_lang):
    """Synchronous version of translate_document_task for demo without Celery"""
    db = SessionLocal()

    try:
        # Get job and document from database
        job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
        document = db.query(Document).filter(Document.id == document_id).first()

        if not job or not document:
            return {"error": "Job or document not found"}

        # Update job status
        job.status = "processing"
        db.commit()

        # Extract text based on file type
        text_content = extract_text_from_file(document.original_path, document.file_type)

        if not text_content or text_content.startswith("Error"):
            job.status = "failed"
            job.error_message = text_content or "Could not extract text from document"
            db.commit()
            return {"error": job.error_message}

        # Translate text
        translated_text = simple_translate(text_content, source_lang, target_lang)

        # Save translated content
        os.makedirs("storage/translations", exist_ok=True)
        result_filename = f"translated_{document.id}_{source_lang}_to_{target_lang}.txt"
        result_path = os.path.join("storage", "translations", result_filename)

        with open(result_path, 'w', encoding='utf-8') as f:
            f.write(f"Original ({source_lang}) to {target_lang}\n")
            f.write("="*50 + "\n\n")
            f.write(translated_text)

        # Update job with results
        job.status = "completed"
        job.result_path = result_path
        job.completed_at = datetime.datetime.utcnow()
        job.processing_time = (job.completed_at - job.created_at).total_seconds()

        document.processed = True

        db.commit()

        return {
            "status": "success",
            "job_id": job_id,
            "result_path": result_path,
            "processing_time": job.processing_time
        }

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        return {"error": str(e)}

    finally:
        db.close()
