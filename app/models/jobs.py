"""
Job-based translation models for course projects
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, ARRAY, Boolean, ForeignKey, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

Base = declarative_base()

class JobStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    PARSING = "parsing"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    POSTPROCESSING = "postprocessing"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"

class Priority(str, Enum):
    NORMAL = "normal"
    FAST = "fast"
    IMMEDIATE = "immediate"

class MediaType(str, Enum):
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    IMAGE = "image"

class FileStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    COMPLETED = "completed"
    FAILED = "failed"

class ArtifactType(str, Enum):
    PARSED = "parsed"
    TRANSCRIPT = "transcript"
    TRANSLATION = "translation"
    SUBTITLE = "subtitle"
    AUDIO = "audio"
    FINAL = "final"

class ReviewStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

# SQLAlchemy Models
class Glossary(Base):
    __tablename__ = "glossaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(Text, nullable=False)
    data = Column(JSON, nullable=False, default={})
    language_pair = Column(String(10), nullable=False)  # e.g., "en-es"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_code = Column(Text, nullable=False)
    title = Column(Text)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(20), nullable=False, default=JobStatus.CREATED)
    priority = Column(String(10), default=Priority.NORMAL)
    source_language = Column(String(10), default="auto")
    target_languages = Column(ARRAY(String), nullable=False)
    translation_style = Column(String(10), default="neutral")
    glossary_id = Column(UUID(as_uuid=True), ForeignKey("glossaries.id"))
    settings = Column(JSON, nullable=False, default={})
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    files = relationship("JobFile", back_populates="job", cascade="all, delete-orphan")
    events = relationship("JobEvent", back_populates="job", cascade="all, delete-orphan")
    artifacts = relationship("JobArtifact", back_populates="job", cascade="all, delete-orphan")
    glossary = relationship("Glossary")

    __table_args__ = (
        CheckConstraint(status.in_([s.value for s in JobStatus]), name="valid_status"),
        CheckConstraint(priority.in_([p.value for p in Priority]), name="valid_priority"),
    )

class JobFile(Base):
    __tablename__ = "job_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    filename = Column(Text, nullable=False)
    object_key = Column(Text, nullable=False)
    mime_type = Column(Text, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    checksum = Column(Text, nullable=False)
    media_type = Column(String(10), nullable=False)
    pages = Column(Integer)  # for documents
    duration_seconds = Column(Numeric(10, 3))  # for audio/video
    status = Column(String(20), default=FileStatus.UPLOADED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    job = relationship("Job", back_populates="files")
    artifacts = relationship("JobArtifact", back_populates="job_file", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(media_type.in_([m.value for m in MediaType]), name="valid_media_type"),
        CheckConstraint(status.in_([s.value for s in FileStatus]), name="valid_file_status"),
    )

class JobEvent(Base):
    __tablename__ = "job_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Text, nullable=False)
    message = Column(Text)
    meta = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True))

    # Relationships
    job = relationship("Job", back_populates="events")

class JobArtifact(Base):
    __tablename__ = "job_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    job_file_id = Column(UUID(as_uuid=True), ForeignKey("job_files.id", ondelete="CASCADE"), nullable=False)
    artifact_type = Column(String(20), nullable=False)
    language_code = Column(String(10))  # target language for translations
    object_key = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    review_status = Column(String(10), default=ReviewStatus.PENDING)
    reviewed_by = Column(UUID(as_uuid=True))
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="artifacts")
    job_file = relationship("JobFile", back_populates="artifacts")

    __table_args__ = (
        CheckConstraint(artifact_type.in_([a.value for a in ArtifactType]), name="valid_artifact_type"),
        CheckConstraint(review_status.in_([r.value for r in ReviewStatus]), name="valid_review_status"),
    )

# Pydantic Models for API
class JobSettings(BaseModel):
    translation_style: str = "neutral"
    glossary_id: Optional[str] = None
    subtitle_options: Dict[str, Any] = Field(default_factory=dict)
    tts: Dict[str, Any] = Field(default_factory=dict)
    delivery_formats: List[str] = Field(default_factory=list)
    privacy: str = "allow_cloud"
    human_review: bool = False

    @validator('translation_style')
    def validate_style(cls, v):
        if v not in ["formal", "neutral", "casual"]:
            raise ValueError("Invalid translation style")
        return v

class FileUpload(BaseModel):
    filename: str
    object_key: str
    mime_type: str
    size: int
    checksum: str
    media_type: MediaType
    pages: Optional[int] = None
    duration_seconds: Optional[float] = None

class JobCreate(BaseModel):
    project_code: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = None
    source_language: str = "auto"
    target_languages: List[str] = Field(..., min_items=1)
    priority: Priority = Priority.NORMAL
    settings: JobSettings = Field(default_factory=JobSettings)
    files: List[FileUpload] = Field(default_factory=list)

    @validator('project_code')
    def validate_project_code(cls, v):
        # Allow alphanumeric, hyphens, underscores
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Project code must contain only alphanumeric characters, hyphens, and underscores")
        return v

class JobResponse(BaseModel):
    id: str
    project_code: str
    title: Optional[str]
    status: JobStatus
    priority: Priority
    source_language: str
    target_languages: List[str]
    translation_style: str
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    file_count: int = 0

    class Config:
        from_attributes = True

class JobFileResponse(BaseModel):
    id: str
    filename: str
    mime_type: str
    size_bytes: int
    media_type: MediaType
    status: FileStatus
    pages: Optional[int]
    duration_seconds: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True

class JobDetailResponse(JobResponse):
    files: List[JobFileResponse]

    class Config:
        from_attributes = True

class JobEventResponse(BaseModel):
    id: str
    event_type: str
    message: Optional[str]
    meta: Dict[str, Any]
    created_at: datetime
    created_by: Optional[str]

    class Config:
        from_attributes = True