# Multi-Modal Translation System - Phase 1

An advanced document translation system built with FastAPI, PostgreSQL, Redis, and Celery.

## 🚀 Features

- **Document Upload**: Support for PDF, DOCX, TXT, RTF, HTML
- **Multi-Language Translation**: 12+ language support
- **Background Processing**: Celery-based async translation
- **User Authentication**: JWT-based security
- **RESTful API**: Complete OpenAPI documentation
- **File Management**: Organized storage and retrieval

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.12
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis + Celery
- **Authentication**: JWT tokens
- **File Processing**: PyPDF2, python-docx, openpyxl
- **Translation**: Google Translate, Deep Translator

## 📋 Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Git

## 🚀 Quick Start

### 1. Start Databases
```bash
docker-compose up postgres redis -d
```

### 2. Activate Virtual Environment
```bash
# Windows
venv\Scripts\activate

# Linux/Mac  
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Initialize Database
```bash
python -c "from app.models.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### 6. Start Services
```bash
# Terminal 1: API Server
python run.py

# Terminal 2: Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Celery Flower (optional monitoring)
celery -A app.workers.celery_app flower
```

### 7. Access the System
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Celery Monitor**: http://localhost:5555

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/token` - Login
- `GET /api/auth/me` - Current user info

### File Management  
- `POST /api/files/upload` - Upload document
- `GET /api/files/` - List documents
- `GET /api/files/{id}` - Get document details
- `DELETE /api/files/{id}` - Delete document

### Translation
- `POST /api/translate/` - Start translation job
- `GET /api/translate/jobs` - List translation jobs
- `GET /api/translate/jobs/{id}` - Get job status
- `GET /api/translate/languages` - Supported languages

## 🔄 Workflow

1. **Upload Document** → File saved to storage + database record
2. **Request Translation** → Job queued for background processing
3. **Background Processing** → Celery worker extracts text, translates, saves result
4. **Monitor Progress** → Check job status via API
5. **Download Result** → Translated document available for download

## 🐳 Docker Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Development

### Adding New Translation Providers
1. Create service in `app/services/`
2. Register in translation worker
3. Update configuration

### File Format Support
1. Add parser in `app/utils/`
2. Update file service
3. Add to allowed extensions

## 🚀 Next Steps (Phase 2)

- Audio translation pipeline
- Speech-to-Text integration
- Text-to-Speech synthesis
- Real-time translation streaming

## 📞 Support

For issues and questions, check the API documentation at `/docs` or review the logs.
