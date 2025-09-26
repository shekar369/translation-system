import os
import uuid
import aiofiles
from sqlalchemy.orm import Session
from app.models.database import Document
from fastapi import UploadFile

class FileService:
    def __init__(self, db: Session):
        self.db = db
    
    async def save_uploaded_file(self, file: UploadFile, user_id: int):
        # Create unique filename
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'unknown'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Create upload directory
        upload_dir = "storage/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Read file content
        content = await file.read()
        
        # Save file to disk
        async with aiofiles.open(file_path, 'wb') as buffer:
            await buffer.write(content)
        
        # Create database record
        document = Document(
            filename=file.filename,
            original_path=file_path,
            file_type=file_extension,
            file_size=len(content),
            user_id=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return document
