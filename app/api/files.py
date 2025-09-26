# Update app/api/files.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.models.database import get_db, Document
from app.services.file_service import FileService
from pydantic import BaseModel
from typing import List
from datetime import datetime
import os

router = APIRouter()

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime  # Changed from str to datetime
    processed: bool
    
    class Config:
        from_attributes = True

@router.post("/upload", response_model=DocumentResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    
    # Validate file type
    allowed_extensions = ['pdf', 'docx', 'txt', 'rtf', 'html']
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save file and create database record
    document = await file_service.save_uploaded_file(file, user_id=1)  # TODO: Get from auth
    return document

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.uploaded_at.desc()).all()
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)  
async def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/{document_id}")
async def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from storage
    if os.path.exists(document.original_path):
        os.remove(document.original_path)
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}