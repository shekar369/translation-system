from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config
from datetime import datetime

DATABASE_URL = config('DATABASE_URL', default='sqlite:///./translation.db')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    user_id = Column(Integer, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

class TranslationJob(Base):
    __tablename__ = "translation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    source_language = Column(String, nullable=False)
    target_language = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    result_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)

# Add to app/models/database.py - after your class definitions
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    uploaded_at: str  # Keep as string
    processed: bool
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_str_dates(cls, obj):
        return cls(
            id=obj.id,
            filename=obj.filename,
            file_type=obj.file_type,
            file_size=obj.file_size,
            uploaded_at=obj.uploaded_at.isoformat(),  # Convert to string
            processed=obj.processed
        )
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
