from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import auth, files, translation
from app.models.database import engine, Base
import os
from fastapi.encoders import jsonable_encoder
from datetime import datetime

app = FastAPI()


# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Multi-Modal Translation System",
    description="Phase 1: Document Translation with FastAPI, PostgreSQL, Redis & Celery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/translations", exist_ok=True)

# Add custom JSON encoder for datetime
@app.middleware("http")
async def convert_datetime_to_isoformat(request, call_next):
    response = await call_next(request)
    return response

# Configure JSON serialization
app.json_encoder = lambda obj: obj.isoformat() if isinstance(obj, datetime) else str(obj)


# Include API routers FIRST (before static files)
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(files.router, prefix="/api/files", tags=["File Management"])
app.include_router(translation.router, prefix="/api/translate", tags=["Translation"])

# Mount static files for storage
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Mount static files for frontend (LAST)
app.mount("/", StaticFiles(directory=".", html=True), name="static")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "translation-api"}

# Add a test endpoint to verify API is working
@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working!", "status": "success"}